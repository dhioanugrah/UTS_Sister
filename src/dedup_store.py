
import json
import os
import threading
from typing import Set

class DedupStore:
    """
    File-based JSON dedup store.
    Persists a set of keys: "<topic>::<event_id>"
    Safe for basic concurrent access via a process-level lock.
    """
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        self._keys: Set[str] = set()
        self._load()

    def _load(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self._atomic_write({"keys": []})
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
                keys = data.get("keys", [])
                self._keys = set(keys)
        except json.JSONDecodeError:
            self._keys = set()
            self._atomic_write({"keys": []})

    def _atomic_write(self, obj: dict) -> None:
        tmp = f"{self.path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.path)

    def make_key(self, topic: str, event_id: str) -> str:
        return f"{topic}::{event_id}"

    def contains(self, topic: str, event_id: str) -> bool:
        key = self.make_key(topic, event_id)
        with self._lock:
            return key in self._keys

    def add(self, topic: str, event_id: str) -> None:
        key = self.make_key(topic, event_id)
        with self._lock:
            if key in self._keys:
                return
            self._keys.add(key)
            self._atomic_write({"keys": list(self._keys)})
