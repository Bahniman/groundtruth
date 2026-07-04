"""Hash-chained certificate ledger: the e-Measurement-Book that cannot be
quietly rewritten. Same construction as a tamper-evident audit log; every
entry carries the hash of its predecessor."""
import hashlib
import json
import time
from dataclasses import asdict

GENESIS = "0" * 64


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


class Ledger:
    def __init__(self):
        self.entries = []

    def record(self, kind: str, payload) -> dict:
        if hasattr(payload, "__dataclass_fields__"):
            payload = asdict(payload)
        prev = self.entries[-1]["hash"] if self.entries else GENESIS
        entry = {"seq": len(self.entries), "kind": kind, "ts": time.time(),
                 "payload": payload, "prev": prev}
        entry["hash"] = hashlib.sha256(_canonical(entry).encode()).hexdigest()
        self.entries.append(entry)
        return entry

    def verify(self) -> tuple:
        prev = GENESIS
        for e in self.entries:
            body = {k: v for k, v in e.items() if k != "hash"}
            if e["prev"] != prev:
                return False, e["seq"]
            if hashlib.sha256(_canonical(body).encode()).hexdigest() != e["hash"]:
                return False, e["seq"]
            prev = e["hash"]
        return True, None

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            for e in self.entries:
                f.write(json.dumps(e) + "\n")
