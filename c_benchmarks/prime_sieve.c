/* Sieve of Eratosthenes. Integer + memory bandwidth. */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "common.h"

#define LIMIT 50000000L

void run(void) {
    unsigned char *sieve = malloc(LIMIT + 1);
    if (!sieve) {
        fprintf(stderr, "alloc fail\n");
        exit(1);
    }
    memset(sieve, 1, LIMIT + 1);
    sieve[0] = 0;
    sieve[1] = 0;
    long sqrt_limit = (long)sqrt((double)LIMIT);
    for (long i = 2; i <= sqrt_limit; i++) {
        if (sieve[i]) {
            for (long j = i * i; j <= LIMIT; j += i) {
                sieve[j] = 0;
            }
        }
    }
    long count = 0;
    for (long i = 0; i <= LIMIT; i++) count += sieve[i];
    if (count < 0) {
        fprintf(stderr, "unreachable\n");
        exit(1);
    }
    free(sieve);
}
