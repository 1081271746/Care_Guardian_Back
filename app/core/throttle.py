"""In-process throttle for failed logins (per e-mail and per client address).

Railway runs a single replica by default; with several replicas each one keeps
its own counters, which still bounds brute force per process.
"""
import os
import threading
import time
from collections import defaultdict, deque

_lock = threading.Lock()
_failures: dict[str, deque] = defaultdict(deque)


def _settings():
    try:
        attempts = max(1, int(os.getenv("LOGIN_MAX_FAILURES", "8")))
        window = max(10, int(os.getenv("LOGIN_WINDOW_SECONDS", "900")))
    except ValueError:
        attempts, window = 8, 900
    return attempts, window


def _prune(bucket: deque, now: float, window: int) -> None:
    while bucket and now - bucket[0] > window:
        bucket.popleft()


def retry_after(*keys: str) -> int:
    """Seconds to wait if any key exceeded the limit, otherwise 0."""
    attempts, window = _settings()
    now = time.monotonic()
    wait = 0
    with _lock:
        for key in keys:
            bucket = _failures[key]
            _prune(bucket, now, window)
            if len(bucket) >= attempts:
                wait = max(wait, int(window - (now - bucket[0])) + 1)
    return wait


def record_failure(*keys: str) -> None:
    now = time.monotonic()
    with _lock:
        for key in keys:
            _failures[key].append(now)


def reset(*keys: str) -> None:
    with _lock:
        for key in keys:
            _failures.pop(key, None)


def clear_all() -> None:
    with _lock:
        _failures.clear()
