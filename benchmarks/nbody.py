"""N-body simulation. Adapted from Benchmarks Game (simplified)."""

PI = 3.141592653589793
SOLAR_MASS = 4 * PI * PI
DAYS_PER_YEAR = 365.24
N_STEPS = 250_000

BODIES = {
    "sun": ([0.0, 0.0, 0.0], [0.0, 0.0, 0.0], SOLAR_MASS),
    "jupiter": (
        [4.84143144246472090e00, -1.16032004402742839e00, -1.03622044471123109e-01],
        [
            1.66007664274403694e-03 * DAYS_PER_YEAR,
            7.69901118419740425e-03 * DAYS_PER_YEAR,
            -6.90460016972063023e-05 * DAYS_PER_YEAR,
        ],
        9.54791938424326609e-04 * SOLAR_MASS,
    ),
    "saturn": (
        [8.34336671824457987e00, 4.12479856412430479e00, -4.03523417114321381e-01],
        [
            -2.76742510726862411e-03 * DAYS_PER_YEAR,
            4.99852801234917238e-03 * DAYS_PER_YEAR,
            2.30417297573763929e-05 * DAYS_PER_YEAR,
        ],
        2.85885980666130812e-04 * SOLAR_MASS,
    ),
    "uranus": (
        [1.28943695621391310e01, -1.51111514016986312e01, -2.23307578892655734e-01],
        [
            2.96460137564761618e-03 * DAYS_PER_YEAR,
            2.37847173959480950e-03 * DAYS_PER_YEAR,
            -2.96589568540237556e-05 * DAYS_PER_YEAR,
        ],
        4.36624404335156298e-05 * SOLAR_MASS,
    ),
    "neptune": (
        [1.53796971148509165e01, -2.59193146099879641e01, 1.79258772950371181e-01],
        [
            2.68067772490389322e-03 * DAYS_PER_YEAR,
            1.62824170038242295e-03 * DAYS_PER_YEAR,
            -9.51592254519715870e-05 * DAYS_PER_YEAR,
        ],
        5.15138902046611451e-05 * SOLAR_MASS,
    ),
}


def advance(dt, bodies, pairs):
    for ([x1, y1, z1], v1, m1), ([x2, y2, z2], v2, m2) in pairs:
        dx = x1 - x2
        dy = y1 - y2
        dz = z1 - z2
        mag = dt * ((dx * dx + dy * dy + dz * dz) ** -1.5)
        v1[0] -= dx * m2 * mag
        v1[1] -= dy * m2 * mag
        v1[2] -= dz * m2 * mag
        v2[0] += dx * m1 * mag
        v2[1] += dy * m1 * mag
        v2[2] += dz * m1 * mag
    for r, [vx, vy, vz], m in bodies:
        r[0] += dt * vx
        r[1] += dt * vy
        r[2] += dt * vz


def offset_momentum(ref, bodies):
    px = py = pz = 0.0
    for r, [vx, vy, vz], m in bodies:
        px -= vx * m
        py -= vy * m
        pz -= vz * m
    r, v, m = ref
    v[0] = px / m
    v[1] = py / m
    v[2] = pz / m


def run() -> None:
    # Deep-copy fresh state each call
    bodies = [
        (list(r), list(v), m)
        for r, v, m in (
            BODIES["sun"],
            BODIES["jupiter"],
            BODIES["saturn"],
            BODIES["uranus"],
            BODIES["neptune"],
        )
    ]
    pairs = [
        (bodies[i], bodies[j])
        for i in range(len(bodies))
        for j in range(i + 1, len(bodies))
    ]
    offset_momentum(bodies[0], bodies)
    for _ in range(N_STEPS):
        advance(0.01, bodies, pairs)
