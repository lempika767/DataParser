"""Phase 1 (per-batch iterative) and Phase 2 (global) encoding."""
from __future__ import annotations
import os
from dataparser.tokenizer import read_all_tokens, write_tokens, iter_batches
from dataparser.patterns import PatternStore
from dataparser.detect import find_and_replace


def _versioned_path(base: str, version: int) -> str:
    root, ext = os.path.splitext(base)
    return f"{root}.v{version}{ext}"


def phase1_encode(
    input_path: str,
    store: PatternStore,
    base_output: str,
    batch_size: int = 5000,
    max_passes: int = 10,
    min_len: int = 2,
    max_len: int = 15,
) -> tuple[str, int]:
    """
    Run up to max_passes; stop early when a pass finds no replacements.
    Returns (final_path, passes_run).
    """
    current_path = input_path
    last_written: str | None = None
    passes_run = 0
    step = max(1, batch_size // 7)  # vary batch size each pass

    for pass_num in range(max_passes):
        this_batch = batch_size + pass_num * step
        tokens = read_all_tokens(current_path)
        new_tokens: list = []
        total_replaced = 0

        for _, batch in iter_batches(tokens, this_batch):
            updated, count = find_and_replace(batch, store, min_len, max_len)
            new_tokens.extend(updated)
            total_replaced += count

        passes_run += 1

        if total_replaced == 0:
            break

        version = pass_num + 1
        out_path = _versioned_path(base_output, version)
        write_tokens(out_path, new_tokens)

        if last_written and os.path.exists(last_written):
            os.remove(last_written)
        last_written = out_path
        current_path = out_path

    return current_path, passes_run


def phase2_encode(
    current_path: str,
    store: PatternStore,
    base_output: str,
    min_len: int = 2,
    max_len: int = 15,
) -> str:
    """
    Global cross-batch detection: iterate until no more replacements found.
    Returns final path.
    """
    version = 0
    last_written: str | None = None

    # detect starting version from base_output
    root, ext = os.path.splitext(base_output)
    v = 1
    while os.path.exists(_versioned_path(base_output, v)):
        v += 1
    version = v - 1  # last existing version number (0 if none)

    while True:
        tokens = read_all_tokens(current_path)
        new_tokens, total_replaced = find_and_replace(tokens, store, min_len, max_len)

        if total_replaced == 0:
            break

        version += 1
        out_path = _versioned_path(base_output, version)
        write_tokens(out_path, new_tokens)

        if last_written and os.path.exists(last_written):
            os.remove(last_written)
        last_written = out_path
        current_path = out_path

    return current_path


def finalize(current_path: str, final_path: str) -> None:
    """Rename current working file to the final output name."""
    if os.path.exists(final_path) and final_path != current_path:
        os.remove(final_path)
    if current_path != final_path:
        os.rename(current_path, final_path)
