"""Stream tokens to/from files. A token is either an int or a $ref string."""
from __future__ import annotations
from typing import Iterator


def parse_token(s: str) -> int | str:
    return s if s.startswith("$") else int(s)


def tokens_to_str(tokens: list) -> str:
    return " ".join(str(t) for t in tokens)


def iter_tokens(path: str) -> Iterator[int | str]:
    with open(path, "r") as f:
        for line in f:
            for part in line.split():
                if part:
                    yield parse_token(part)


def read_all_tokens(path: str) -> list:
    return list(iter_tokens(path))


def write_tokens(path: str, tokens: list) -> None:
    with open(path, "w") as f:
        f.write(tokens_to_str(tokens))
        f.write("\n")


def iter_batches(tokens: list, batch_size: int) -> Iterator[tuple[int, list]]:
    """Yield (start_index, batch) tuples."""
    for i in range(0, len(tokens), batch_size):
        yield i, tokens[i : i + batch_size]
