"""NumPy matmul. Hits Apple Accelerate / SME on macOS aarch64."""

import numpy as np

SIZE = 3000
_RNG = np.random.default_rng(42)
_A = _RNG.standard_normal((SIZE, SIZE), dtype=np.float64)
_B = _RNG.standard_normal((SIZE, SIZE), dtype=np.float64)


def run() -> None:
    c = _A @ _B
    if c.shape != (SIZE, SIZE):
        raise RuntimeError("unreachable")
