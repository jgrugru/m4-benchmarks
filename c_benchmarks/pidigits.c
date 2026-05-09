/* Pidigits. Spigot algorithm via GMP for arbitrary-precision int. */

#include <gmp.h>
#include <stdio.h>
#include <stdlib.h>

#include "common.h"

#define N_DIGITS 8000

void run(void) {
    mpz_t k, ns, n, a, d, t, u, k1, tmp;
    mpz_inits(k, ns, n, a, d, t, u, k1, tmp, NULL);
    mpz_set_ui(k, 1);
    mpz_set_ui(ns, 0);
    mpz_set_ui(n, 1);
    mpz_set_ui(a, 0);
    mpz_set_ui(d, 1);

    int produced = 0;
    while (produced < N_DIGITS) {
        mpz_mul_ui(k1, k, 2);
        mpz_add_ui(k1, k1, 1);
        mpz_mul_ui(n, n, 2);
        mpz_add(a, a, n);
        mpz_mul(a, a, k1);
        mpz_mul(d, d, k1);
        mpz_add_ui(k, k, 1);

        if (mpz_cmp(a, n) >= 0) {
            mpz_mul_ui(tmp, n, 3);
            mpz_add(tmp, tmp, a);
            mpz_fdiv_qr(t, u, tmp, d);
            mpz_add(u, u, n);

            if (mpz_cmp(d, u) > 0) {
                mpz_mul_ui(ns, ns, 10);
                mpz_add(ns, ns, t);
                produced++;
                if (produced % 10 == 0) {
                    mpz_set_ui(ns, 0);
                }
                mpz_mul(tmp, d, t);
                mpz_sub(a, a, tmp);
                mpz_mul_ui(a, a, 10);
                mpz_mul_ui(n, n, 10);
            }
        }
    }

    mpz_clears(k, ns, n, a, d, t, u, k1, tmp, NULL);
}
