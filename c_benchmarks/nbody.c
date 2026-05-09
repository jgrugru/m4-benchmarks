/* N-body simulation. Adapted from Benchmarks Game (simplified). */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include "common.h"

#define N_STEPS 250000
#define N_BODIES 5

#define PI 3.141592653589793
#define SOLAR_MASS (4.0 * PI * PI)
#define DAYS_PER_YEAR 365.24

typedef struct {
    double x, y, z;
    double vx, vy, vz;
    double mass;
} body_t;

static const body_t INITIAL_BODIES[N_BODIES] = {
    {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, SOLAR_MASS},
    {4.84143144246472090e00, -1.16032004402742839e00, -1.03622044471123109e-01,
     1.66007664274403694e-03 * DAYS_PER_YEAR,
     7.69901118419740425e-03 * DAYS_PER_YEAR,
     -6.90460016972063023e-05 * DAYS_PER_YEAR,
     9.54791938424326609e-04 * SOLAR_MASS},
    {8.34336671824457987e00, 4.12479856412430479e00, -4.03523417114321381e-01,
     -2.76742510726862411e-03 * DAYS_PER_YEAR,
     4.99852801234917238e-03 * DAYS_PER_YEAR,
     2.30417297573763929e-05 * DAYS_PER_YEAR,
     2.85885980666130812e-04 * SOLAR_MASS},
    {1.28943695621391310e01, -1.51111514016986312e01, -2.23307578892655734e-01,
     2.96460137564761618e-03 * DAYS_PER_YEAR,
     2.37847173959480950e-03 * DAYS_PER_YEAR,
     -2.96589568540237556e-05 * DAYS_PER_YEAR,
     4.36624404335156298e-05 * SOLAR_MASS},
    {1.53796971148509165e01, -2.59193146099879641e01, 1.79258772950371181e-01,
     2.68067772490389322e-03 * DAYS_PER_YEAR,
     1.62824170038242295e-03 * DAYS_PER_YEAR,
     -9.51592254519715870e-05 * DAYS_PER_YEAR,
     5.15138902046611451e-05 * SOLAR_MASS},
};

static void offset_momentum(body_t *bodies) {
    double px = 0.0, py = 0.0, pz = 0.0;
    for (int i = 0; i < N_BODIES; i++) {
        px -= bodies[i].vx * bodies[i].mass;
        py -= bodies[i].vy * bodies[i].mass;
        pz -= bodies[i].vz * bodies[i].mass;
    }
    bodies[0].vx = px / bodies[0].mass;
    bodies[0].vy = py / bodies[0].mass;
    bodies[0].vz = pz / bodies[0].mass;
}

static void advance(double dt, body_t *bodies) {
    for (int i = 0; i < N_BODIES; i++) {
        for (int j = i + 1; j < N_BODIES; j++) {
            double dx = bodies[i].x - bodies[j].x;
            double dy = bodies[i].y - bodies[j].y;
            double dz = bodies[i].z - bodies[j].z;
            double d2 = dx * dx + dy * dy + dz * dz;
            double mag = dt / (d2 * sqrt(d2));
            bodies[i].vx -= dx * bodies[j].mass * mag;
            bodies[i].vy -= dy * bodies[j].mass * mag;
            bodies[i].vz -= dz * bodies[j].mass * mag;
            bodies[j].vx += dx * bodies[i].mass * mag;
            bodies[j].vy += dy * bodies[i].mass * mag;
            bodies[j].vz += dz * bodies[i].mass * mag;
        }
    }
    for (int i = 0; i < N_BODIES; i++) {
        bodies[i].x += dt * bodies[i].vx;
        bodies[i].y += dt * bodies[i].vy;
        bodies[i].z += dt * bodies[i].vz;
    }
}

void run(void) {
    body_t bodies[N_BODIES];
    for (int i = 0; i < N_BODIES; i++) bodies[i] = INITIAL_BODIES[i];
    offset_momentum(bodies);
    for (long s = 0; s < N_STEPS; s++) {
        advance(0.01, bodies);
    }
    if (bodies[0].x == 1e300) {
        fprintf(stderr, "unreachable\n");
        exit(1);
    }
}
