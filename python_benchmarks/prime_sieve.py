"""Sieve of Eratosthenes. Integer + memory bandwidth."""

LIMIT = 50_000_000


def run() -> None:
    sieve = bytearray(b"\x01") * (LIMIT + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(LIMIT**0.5) + 1):
        if sieve[i]:
            sieve[i * i :: i] = b"\x00" * len(sieve[i * i :: i])
    count = sum(sieve)
    if count < 0:
        raise RuntimeError("unreachable")
