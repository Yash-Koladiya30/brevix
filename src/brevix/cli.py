"""Brevix CLI entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from brevix import (
    Compressor,
    CompressionMode,
    AccuracyGuard,
    Stats,
    pick_mode,
    count_tokens,
    count_tokens_method,
    install as install_target,
    list_targets,
    TARGETS,
    __version__,
)
from brevix.file_compress import compress_file


def _cmd_compress(args: argparse.Namespace) -> int:
    text = args.text
    if text == "-" or not text:
        text = sys.stdin.read()

    if args.mode == "auto":
        adaptive = pick_mode(text, threshold=args.threshold)
        result = adaptive.compression
        guard_result = adaptive.guard
        chosen = adaptive.chosen_mode
        if not guard_result.passed and args.strict:
            sys.stderr.write(
                f"[brevix] auto: no mode passed guard ({guard_result.similarity:.2f} < {args.threshold:.2f}). "
                f"Emitting original.\n"
            )
            print(text)
            return 2
        if args.verbose:
            sys.stderr.write(f"[brevix] auto picked mode={chosen.value}\n")
    else:
        chosen = CompressionMode(args.mode)
        result = Compressor(mode=chosen).compress(text)
        guard_result = None
        if args.guard:
            guard = AccuracyGuard(threshold=args.threshold)
            guard_result = guard.check(result.original, result.compressed)
            if not guard_result.passed:
                sys.stderr.write(guard_result.warning + "\n")
                if args.strict:
                    sys.stderr.write("Strict mode: emitting original instead.\n")
                    print(result.original)
                    return 2

    if not args.no_stats:
        Stats().record(
            mode=chosen.value,
            chars_saved=result.char_savings,
            tokens_saved=result.token_savings_estimate,
        )

    print(result.compressed)
    if args.verbose:
        orig_tok = count_tokens(result.original)
        comp_tok = count_tokens(result.compressed)
        method = count_tokens_method()
        sys.stderr.write(
            f"\n[brevix] mode={chosen.value} "
            f"chars: {len(result.original)}→{len(result.compressed)} "
            f"({result.char_savings_pct}% saved) "
            f"tokens ({method}): {orig_tok}→{comp_tok}\n"
        )
        if guard_result:
            sys.stderr.write(
                f"[brevix] guard: sim={guard_result.similarity:.3f} "
                f"({guard_result.method}) pass={guard_result.passed}\n"
            )
    return 0


def _cmd_compress_file(args: argparse.Namespace) -> int:
    mode = CompressionMode(args.mode)
    try:
        result = compress_file(
            args.path,
            mode=mode,
            guard=not args.no_guard,
            threshold=args.threshold,
            dry_run=args.dry_run,
            force=args.force,
        )
    except (FileNotFoundError, IsADirectoryError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2

    if result.skipped:
        sys.stderr.write(f"Skipped: {result.reason}\n")
        return 1

    suffix = " (dry-run)" if args.dry_run else ""
    print(
        f"Compressed {result.path}{suffix}: "
        f"{result.compression.char_savings} chars saved "
        f"({result.compression.char_savings_pct}%)"
    )
    if result.backup:
        print(f"Backup: {result.backup}")
    if result.guard:
        print(
            f"Guard: sim={result.guard.similarity:.3f} "
            f"({result.guard.method}) pass={result.guard.passed}"
        )
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    stats = Stats()
    if args.reset:
        stats.reset()
        print("Stats reset.")
        return 0
    try:
        print(stats.summary(since=args.since, real=args.real, share=args.share))
    except ValueError as e:
        sys.stderr.write(f"Error: {e}\n")
        return 2
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    guard = AccuracyGuard(threshold=args.threshold)
    result = guard.check(args.original, args.compressed)
    print(
        f"Similarity: {result.similarity:.4f}  "
        f"Threshold: {result.threshold:.2f}  "
        f"Passed: {result.passed}  "
        f"Method: {result.method}"
    )
    return 0 if result.passed else 1


def _cmd_count(args: argparse.Namespace) -> int:
    text = args.text
    if text == "-" or not text:
        text = sys.stdin.read()
    print(f"{count_tokens(text)} tokens ({count_tokens_method()}, {len(text)} chars)")
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    if args.list:
        print(list_targets())
        return 0
    target = args.target
    if target is None:
        sys.stderr.write("Error: target required (or use --list).\n")
        return 2
    if target != "all" and target not in TARGETS:
        sys.stderr.write(f"Error: unknown target '{target}'. Run `brevix install --list`.\n")
        return 2
    root = Path(args.path).resolve()

    if args.dry_run:
        print(f"[dry-run] Would install '{target}' into {root}.")
        return 0

    files = install_target(target, root)
    print(f"Brevix installed for target '{target}' in {root}:")
    for f in files:
        try:
            print(f"  + {f.relative_to(root)}")
        except ValueError:
            print(f"  + {f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="brevix",
        description="Compress LLM output safely. Save tokens without breaking your code.",
    )
    parser.add_argument("--version", action="version", version=f"brevix {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_compress = sub.add_parser("compress", help="Compress text")
    p_compress.add_argument("text", nargs="?", default="-", help="Text to compress, or '-' for stdin")
    p_compress.add_argument("--mode", choices=["lite", "full", "ultra", "auto"], default="full")
    p_compress.add_argument("--guard", action="store_true", help="Enable Accuracy Guard")
    p_compress.add_argument("--strict", action="store_true", help="Fall back to original if guard fails")
    p_compress.add_argument("--threshold", type=float, default=0.85)
    p_compress.add_argument("--no-stats", action="store_true", help="Don't record to local stats")
    p_compress.add_argument("-v", "--verbose", action="store_true")
    p_compress.set_defaults(func=_cmd_compress)

    p_cf = sub.add_parser("compress-file", help="Compress a file in place (with .original backup)")
    p_cf.add_argument("path")
    p_cf.add_argument("--mode", choices=["lite", "full", "ultra"], default="full")
    p_cf.add_argument("--threshold", type=float, default=0.85)
    p_cf.add_argument("--no-guard", action="store_true")
    p_cf.add_argument("--dry-run", action="store_true")
    p_cf.add_argument("--force", action="store_true", help="Overwrite even if guard fails")
    p_cf.set_defaults(func=_cmd_compress_file)

    p_stats = sub.add_parser("stats", help="Show local stats")
    p_stats.add_argument("--reset", action="store_true")
    p_stats.add_argument("--since", default="all", help="Time window: 7d, 24h, 30m, all")
    p_stats.add_argument("--real", action="store_true", help="Parse real Claude Code session logs")
    p_stats.add_argument("--share", action="store_true", help="One-line tweet-ready output")
    p_stats.set_defaults(func=_cmd_stats)

    p_check = sub.add_parser("check", help="Check similarity between two texts")
    p_check.add_argument("original")
    p_check.add_argument("compressed")
    p_check.add_argument("--threshold", type=float, default=0.85)
    p_check.set_defaults(func=_cmd_check)

    p_count = sub.add_parser("count", help="Count tokens in text")
    p_count.add_argument("text", nargs="?", default="-")
    p_count.set_defaults(func=_cmd_count)

    p_install = sub.add_parser(
        "install",
        help="Install Brevix rules into a project for a specific LLM coding tool",
    )
    p_install.add_argument(
        "target",
        nargs="?",
        help="Target tool. Use --list to see all options.",
    )
    p_install.add_argument("--path", default=".", help="Project root (default: cwd)")
    p_install.add_argument("--list", action="store_true", help="List available targets")
    p_install.add_argument("--dry-run", action="store_true", help="Preview without writing")
    p_install.set_defaults(func=_cmd_install)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
