"""SHA-256 fan-out via multiprocessing. Saturates all cores."""

import hashlib
import os
from multiprocessing import Pool

WORK_PER_PROC = 200_000
DATA_SIZE = 4096


def _hash_loop(seed: int) -> int:
    data = seed.to_bytes(8, "little") + b"\x00" * (DATA_SIZE - 8)
    h = hashlib.sha256(data).digest()
    for _ in range(WORK_PER_PROC):
        h = hashlib.sha256(h).digest()
    return h[0]


def run() -> None:
    n = os.cpu_count() or 1
    with Pool(processes=n) as pool:
        results = pool.map(_hash_loop, range(n))
    if len(results) != n:
        raise RuntimeError("unreachable")
