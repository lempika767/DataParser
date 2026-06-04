"""PatternStore: intern token-tuple -> stable integer id, persist to file."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class PatternStore:
    _by_tuple: dict = field(default_factory=dict)
    _by_id: dict = field(default_factory=dict)
    _next_id: int = 1

    def intern(self, tokens: tuple) -> int:
        if tokens not in self._by_tuple:
            rid = self._next_id
            self._next_id += 1
            self._by_tuple[tokens] = rid
            self._by_id[rid] = tokens
        return self._by_tuple[tokens]

    def get_by_id(self, rid: int) -> tuple | None:
        return self._by_id.get(rid)

    def all_ids(self) -> list[int]:
        return list(self._by_id.keys())

    def __len__(self) -> int:
        return len(self._by_id)

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            for rid, toks in sorted(self._by_id.items()):
                tok_str = " ".join(str(t) for t in toks)
                f.write(f"{rid}\t{tok_str}\n")

    @classmethod
    def load(cls, path: str) -> "PatternStore":
        store = cls()
        with open(path, "r") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                rid_str, _, tok_str = line.partition("\t")
                rid = int(rid_str)
                from dataparser.tokenizer import parse_token
                toks = tuple(parse_token(t) for t in tok_str.split())
                store._by_tuple[toks] = rid
                store._by_id[rid] = toks
                if rid >= store._next_id:
                    store._next_id = rid + 1
        return store
