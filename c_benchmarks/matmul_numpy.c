/* 3000x3000 float64 gemm via Apple Accelerate cblas_dgemm.
 * Mirrors python_benchmarks/matmul_numpy.py — same backend numpy uses on macOS. */

#define ACCELERATE_NEW_LAPACK
#include <Accelerate/Accelerate.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "common.h"

#define SIZE 3000

static double *A = NULL;
static double *B = NULL;
static double *C = NULL;

/* xoshiro256** for cheap, reproducible filler; values not compared to numpy's. */
static uint64_t rng_state[4] = {1, 2, 3, 4};

static uint64_t rotl(uint64_t x, int k) {
    return (x << k) | (x >> (64 - k));
}

static uint64_t xoshiro_next(void) {
    uint64_t result = rotl(rng_state[1] * 5, 7) * 9;
    uint64_t t = rng_state[1] << 17;
    rng_state[2] ^= rng_state[0];
    rng_state[3] ^= rng_state[1];
    rng_state[1] ^= rng_state[2];
    rng_state[0] ^= rng_state[3];
    rng_state[2] ^= t;
    rng_state[3] = rotl(rng_state[3], 45);
    return result;
}

static double next_normal(void) {
    /* Box-Muller. Good enough for filling matrices. */
    double u1 = (double)(xoshiro_next() >> 11) * (1.0 / (double)(1ULL << 53));
    double u2 = (double)(xoshiro_next() >> 11) * (1.0 / (double)(1ULL << 53));
    if (u1 < 1e-300) u1 = 1e-300;
    return sqrt(-2.0 * log(u1)) * cos(2.0 * M_PI * u2);
}

static void init_matrices(void) {
    if (A) return;
    size_t sz = (size_t)SIZE * (size_t)SIZE;
    A = malloc(sz * sizeof(double));
    B = malloc(sz * sizeof(double));
    C = malloc(sz * sizeof(double));
    if (!A || !B || !C) {
        fprintf(stderr, "alloc fail\n");
        exit(1);
    }
    for (size_t i = 0; i < sz; i++) A[i] = next_normal();
    for (size_t i = 0; i < sz; i++) B[i] = next_normal();
}

void run(void) {
    init_matrices();
    cblas_dgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans,
                SIZE, SIZE, SIZE,
                1.0, A, SIZE, B, SIZE,
                0.0, C, SIZE);
    if (C[0] == 1.234567e300) {
        fprintf(stderr, "unreachable\n");
        exit(1);
    }
}
