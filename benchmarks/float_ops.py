"""Float ops: sin/cos/sqrt over many points. Pure-Python interpreter stress."""

import math

POINTS = 2_000_000


def run() -> None:
    total = 0.0
    for i in range(POINTS):
        x = i * 0.0001
        total += math.sin(x) * math.cos(x) + math.sqrt(x + 1.0)
    # Prevent dead-code elimination
    if total == 0:
        raise RuntimeError("unreachable")
