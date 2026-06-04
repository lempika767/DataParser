"""N-gram repeat detection and greedy non-overlapping replacement."""
from __future__ import annotations
from collections import defaultdict
from dataparser.patterns import PatternStore


def find_and_replace(
    tokens: list,
    store: PatternStore,
    min_len: int = 2,
    max_len: int = 15,
) -> tuple[list, int]:
    """
    Find repeated subsequences of length min_len..max_len (>=2 occurrences),
    replace non-overlapping occurrences greedily by savings, return
    (new_token_list, replacement_count).
    """
    n = len(tokens)
    if n < min_len:
        return tokens, 0

    # Count all ngrams
    counts: dict[tuple, list[int]] = defaultdict(list)
    for length in range(min_len, min(max_len, n) + 1):
        for i in range(n - length + 1):
            gram = tuple(tokens[i : i + length])
            counts[gram].append(i)

    # Candidates with >=2 occurrences; rank by savings desc then length desc
    candidates = [
        (gram, positions)
        for gram, positions in counts.items()
        if len(positions) >= 2
    ]
    candidates.sort(key=lambda x: (len(x[1]) * (len(x[0]) - 1), len(x[0])), reverse=True)

    if not candidates:
        return tokens, 0

    replaced = list(tokens)
    total_replacements = 0

    for gram, _ in candidates:
        length = len(gram)
        # Re-scan current state for this gram (tokens may have shifted)
        positions = []
        i = 0
        while i <= len(replaced) - length:
            if tuple(replaced[i : i + length]) == gram:
                positions.append(i)
                i += length  # skip to avoid overlap
            else:
                i += 1

        if len(positions) < 2:
            continue

        rid = store.intern(gram)
        ref = f"${rid}"

        # Replace right-to-left to keep positions valid
        for pos in reversed(positions):
            replaced[pos : pos + length] = [ref]
        total_replacements += len(positions)

    return replaced, total_replacements
