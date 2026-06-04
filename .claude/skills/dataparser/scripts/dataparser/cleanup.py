"""Phase 3: garbage-collect unused/single-use refs, optionally renumber."""
from __future__ import annotations
from dataparser.tokenizer import read_all_tokens, write_tokens, parse_token
from dataparser.patterns import PatternStore


def _count_usages(encoded_tokens: list, store: PatternStore) -> dict[int, int]:
    usage: dict[int, int] = {rid: 0 for rid in store.all_ids()}

    def _count_seq(seq):
        for tok in seq:
            if isinstance(tok, str) and tok.startswith("$"):
                rid = int(tok[1:])
                if rid in usage:
                    usage[rid] += 1
                    _count_seq(store.get_by_id(rid) or ())

    _count_seq(encoded_tokens)
    return usage


def _inline_ref(tokens: list, rid: int, store: PatternStore) -> list:
    pattern = store.get_by_id(rid)
    if pattern is None:
        return tokens
    ref = f"${rid}"
    result = []
    for tok in tokens:
        if tok == ref:
            result.extend(pattern)
        else:
            result.append(tok)
    return result


def _inline_in_patterns(store: PatternStore, target_rid: int) -> None:
    """Replace $target_rid inside all other pattern definitions."""
    pattern = store.get_by_id(target_rid)
    if pattern is None:
        return
    ref = f"${target_rid}"
    updated: dict[int, tuple] = {}
    for rid, toks in list(store._by_id.items()):
        if rid == target_rid:
            continue
        if ref in toks:
            new_toks = []
            for t in toks:
                if t == ref:
                    new_toks.extend(pattern)
                else:
                    new_toks.append(t)
            updated[rid] = tuple(new_toks)
    for rid, new_toks in updated.items():
        old_toks = store._by_id[rid]
        del store._by_tuple[old_toks]
        store._by_id[rid] = new_toks
        store._by_tuple[new_toks] = rid


def _remove_ref(store: PatternStore, rid: int) -> None:
    toks = store._by_id.pop(rid, None)
    if toks is not None:
        store._by_tuple.pop(toks, None)


def run_cleanup(encoded_path: str, store: PatternStore) -> tuple[list, int]:
    """
    Iteratively remove zero-use refs and inline single-use refs until stable.
    Returns (final_token_list, total_removed).
    """
    tokens = read_all_tokens(encoded_path)
    total_removed = 0

    while True:
        usage = _count_usages(tokens, store)
        changed = False

        # Delete zero-use
        for rid, count in list(usage.items()):
            if count == 0:
                _remove_ref(store, rid)
                total_removed += 1
                changed = True

        # Inline single-use (in encoded stream and in other patterns)
        usage = _count_usages(tokens, store)
        for rid, count in list(usage.items()):
            if count == 1:
                _inline_in_patterns(store, rid)
                tokens = _inline_ref(tokens, rid, store)
                _remove_ref(store, rid)
                total_removed += 1
                changed = True

        if not changed:
            break

    return tokens, total_removed


def renumber(tokens: list, store: PatternStore) -> tuple[list, PatternStore]:
    """Compact ref ids to 1..N preserving order of first appearance."""
    new_store = PatternStore()
    id_map: dict[int, int] = {}

    def _remap_toks(toks):
        result = []
        for t in toks:
            if isinstance(t, str) and t.startswith("$"):
                old = int(t[1:])
                result.append(f"${id_map[old]}")
            else:
                result.append(t)
        return tuple(result)

    # Process patterns in id order so inner refs are remapped before outer ones
    for old_id in sorted(store.all_ids()):
        pattern = store.get_by_id(old_id)
        new_toks = _remap_toks(pattern)
        new_id = new_store.intern(new_toks)
        id_map[old_id] = new_id

    new_tokens = []
    for t in tokens:
        if isinstance(t, str) and t.startswith("$"):
            old = int(t[1:])
            new_tokens.append(f"${id_map[old]}")
        else:
            new_tokens.append(t)

    return new_tokens, new_store
