"""Compress a file in place — safe in-file rewrite for memory/context files.

Used for files loaded into the model's input every session (CLAUDE.md,
AGENTS.md, project notes, persona prompts). Compression there saves input
tokens for the entire project lifetime.

Behavior:
- Read file
- Run Compressor (default: full mode)
- Write result back to original path
- Save untouched copy as <stem>.original<suffix>
- Skip backup if .original already exists (assumes prior compress)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from brevix.accuracy_guard import AccuracyGuard, GuardResult
from brevix.compressor import Compressor, CompressionMode, CompressionResult


@dataclass
class FileCompressionResult:
    path: Path
    backup: Path | None
    compression: CompressionResult
    guard: GuardResult | None
    skipped: bool = False
    reason: str = ""


def compress_file(
    path: str | Path,
    mode: CompressionMode = CompressionMode.FULL,
    *,
    guard: bool = True,
    threshold: float = 0.85,
    dry_run: bool = False,
    force: bool = False,
) -> FileCompressionResult:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Not found: {p}")
    if p.is_dir():
        raise IsADirectoryError(f"Is a directory: {p}")

    original = p.read_text(encoding="utf-8")
    result = Compressor(mode=mode).compress(original)

    guard_result: GuardResult | None = None
    if guard:
        guard_result = AccuracyGuard(threshold=threshold).check(original, result.compressed)
        if not guard_result.passed and not force:
            return FileCompressionResult(
                path=p,
                backup=None,
                compression=result,
                guard=guard_result,
                skipped=True,
                reason=f"Guard failed (sim {guard_result.similarity:.3f} < {threshold:.2f}). "
                       f"Re-run with --force to override.",
            )

    backup = _backup_path(p)
    if dry_run:
        return FileCompressionResult(p, backup if not backup.exists() else None, result, guard_result)

    if not backup.exists():
        backup.write_text(original, encoding="utf-8")

    p.write_text(result.compressed, encoding="utf-8")
    return FileCompressionResult(p, backup if backup.exists() else None, result, guard_result)


def _backup_path(p: Path) -> Path:
    if p.suffix:
        return p.with_name(f"{p.stem}.original{p.suffix}")
    return p.with_name(f"{p.name}.original")
