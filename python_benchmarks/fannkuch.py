"""Fannkuch-redux. Permutation pancake-flipping. Integer-heavy."""

N = 10


def fannkuch(n):
    max_flips = 0
    perm = list(range(n))
    perm1 = list(range(n))
    count = list(range(n))
    r = n
    while True:
        while r != 1:
            count[r - 1] = r
            r -= 1
        if perm1[0] != 0 and perm1[n - 1] != n - 1:
            perm[:] = perm1
            flips = 0
            k = perm[0]
            while k:
                perm[: k + 1] = perm[k::-1]
                flips += 1
                k = perm[0]
            if flips > max_flips:
                max_flips = flips
        while r < n:
            perm1.insert(r, perm1.pop(0))
            count[r] -= 1
            if count[r] > 0:
                break
            r += 1
        else:
            return max_flips


def run() -> None:
    fannkuch(N)
