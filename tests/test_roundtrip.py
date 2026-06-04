"""End-to-end encode -> decode round-trip tests for the dataparser CLI.

These run the actual CLI the way the skill does, so they cover the full
pipeline (phase 1/2 detection, cleanup, renumber) and guard against the
data-loss bug where a no-pattern input was deleted during work-file cleanup.
"""
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
CLI = os.path.join(REPO_ROOT, ".claude", "skills", "dataparser", "scripts", "cli.py")


def _run(*args):
    result = subprocess.run(
        [sys.executable, CLI, *args],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result


def _tokens(path):
    with open(path, encoding="utf-8") as f:
        return f.read().split()


def _encode_decode(tmp_path, content):
    src = tmp_path / "input.txt"
    src.write_text(content, encoding="utf-8")
    original = _tokens(src)

    _run("encode", str(src), "--out-dir", str(tmp_path))

    encoded = tmp_path / "input.encoded.txt"
    patterns = tmp_path / "input.patterns.txt"
    assert encoded.exists() and patterns.exists()
    # Regression: the original input must never be deleted by encoding.
    assert src.exists(), "encode deleted the input file"

    decoded = tmp_path / "input.decoded.txt"
    _run("decode", str(encoded), str(patterns), "-o", str(decoded))

    return original, _tokens(decoded)


# A few rows with heavily repeated subsequences -> patterns get created.
REPEATED = (
    "15 67 23 45 15 67 23 45 89 12 34 56 78 90 11 22 33 44 55 66\n"
    "15 67 23 45 77 88 99 15 67 23 45 11 22 33 44 55 66 77 88 99\n"
    "10 20 30 40 50 10 20 30 40 50 11 22 33 44 55 66 10 20 30 40\n"
)


def test_roundtrip_with_patterns(tmp_path):
    original, decoded = _encode_decode(tmp_path, REPEATED)
    assert decoded == original


def test_roundtrip_no_patterns_preserves_input(tmp_path):
    # All-unique tokens: no patterns are found. This is the case that used
    # to delete the input file during work-file cleanup.
    content = " ".join(str(n) for n in range(50)) + "\n"
    original, decoded = _encode_decode(tmp_path, content)
    assert decoded == original


def test_roundtrip_sample_fixture(tmp_path):
    fixture = os.path.join(os.path.dirname(__file__), "fixtures", "sample.txt")
    original, decoded = _encode_decode(tmp_path, open(fixture, encoding="utf-8").read())
    assert decoded == original
