"""Tests for compress_file."""

from pathlib import Path

import pytest

from brevix.compressor import CompressionMode
from brevix.file_compress import compress_file


def test_compresses_file_in_place_with_backup(tmp_path: Path) -> None:
    src = tmp_path / "notes.md"
    text = (
        "Sure! In order to make use of the new API, you need to actually "
        "call the function with the appropriate parameters.\n"
    )
    src.write_text(text, encoding="utf-8")

    result = compress_file(src, mode=CompressionMode.FULL, guard=False)
    assert not result.skipped
    assert src.read_text(encoding="utf-8") != text
    assert (tmp_path / "notes.original.md").exists()
    assert (tmp_path / "notes.original.md").read_text(encoding="utf-8") == text


def test_dry_run_does_not_write(tmp_path: Path) -> None:
    src = tmp_path / "x.md"
    text = "Sure! Just call the function.\n"
    src.write_text(text, encoding="utf-8")
    compress_file(src, guard=False, dry_run=True)
    assert src.read_text(encoding="utf-8") == text
    assert not (tmp_path / "x.original.md").exists()


def test_guard_block_skips_write(tmp_path: Path) -> None:
    src = tmp_path / "y.md"
    text = (
        "Sure! Just basically call the function with parameters. "
        "Really, you should definitely use it.\n"
    )
    src.write_text(text, encoding="utf-8")
    # Threshold 0.99 + heavy compression → guard will fail → skip.
    result = compress_file(src, guard=True, threshold=0.99)
    assert result.skipped, f"expected skip, got compressed={result.compression.compressed!r}"
    assert "Guard failed" in result.reason
    assert src.read_text(encoding="utf-8") == text


def test_force_overrides_guard(tmp_path: Path) -> None:
    src = tmp_path / "z.md"
    text = (
        "Sure! Just basically call the function with parameters. "
        "Really, you should definitely use it.\n"
    )
    src.write_text(text, encoding="utf-8")
    result = compress_file(src, guard=True, threshold=0.99, force=True)
    assert not result.skipped


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        compress_file(tmp_path / "nope.md")


def test_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(IsADirectoryError):
        compress_file(tmp_path)
