"""Pidigits. Arbitrary-precision integer arithmetic via spigot algorithm."""

N_DIGITS = 8000


def run() -> None:
    k, ns = 1, 0
    n, a, d, t, u = 1, 0, 1, 0, 0
    out = []
    produced = 0
    while produced < N_DIGITS:
        k1 = k * 2 + 1
        n *= 2
        a += n
        a *= k1
        d *= k1
        k += 1
        if a >= n:
            t, u = divmod(n * 3 + a, d)
            u += n
            if d > u:
                ns = ns * 10 + t
                produced += 1
                if produced % 10 == 0:
                    out.append(ns)
                    ns = 0
                a -= d * t
                a *= 10
                n *= 10
