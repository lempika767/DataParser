"""Decode an encoded token stream back to the original number sequence."""
from __future__ import annotations
from dataparser.tokenizer import read_all_tokens, parse_token
from dataparser.patterns import PatternStore


def _expand(token, store: PatternStore, cache: dict) -> list:
    if isinstance(token, int):
        return [token]
    rid = int(token[1:])
    if rid in cache:
        return cache[rid]
    pattern = store.get_by_id(rid)
    if pattern is None:
        raise ValueError(f"Unknown ref id {rid}")
    expanded = []
    for t in pattern:
        expanded.extend(_expand(t, store, cache))
    cache[rid] = expanded
    return expanded


def decode(encoded_path: str, patterns_path: str, output_path: str) -> int:
    """Returns count of output tokens written."""
    store = PatternStore.load(patterns_path)
    tokens = read_all_tokens(encoded_path)
    cache: dict = {}
    result = []
    for tok in tokens:
        result.extend(_expand(tok, store, cache))
    with open(output_path, "w") as f:
        f.write(" ".join(str(t) for t in result))
        f.write("\n")
    return len(result)
