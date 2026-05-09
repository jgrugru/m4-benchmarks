/* Fannkuch-redux. Permutation pancake-flipping. Integer-heavy. */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "common.h"

#define N 10

static int fannkuch(int n) {
    int max_flips = 0;
    int perm[N], perm1[N], count[N];
    for (int i = 0; i < n; i++) {
        perm1[i] = i;
        count[i] = i;
    }
    int r = n;
    while (1) {
        while (r != 1) {
            count[r - 1] = r;
            r--;
        }
        if (perm1[0] != 0 && perm1[n - 1] != n - 1) {
            memcpy(perm, perm1, sizeof(int) * (size_t)n);
            int flips = 0;
            int k = perm[0];
            while (k) {
                int lo = 0, hi = k;
                while (lo < hi) {
                    int tmp = perm[lo];
                    perm[lo] = perm[hi];
                    perm[hi] = tmp;
                    lo++;
                    hi--;
                }
                flips++;
                k = perm[0];
            }
            if (flips > max_flips) max_flips = flips;
        }
        int rotated_to_end = 1;
        while (r < n) {
            int first = perm1[0];
            for (int i = 0; i < r; i++) perm1[i] = perm1[i + 1];
            perm1[r] = first;
            count[r]--;
            if (count[r] > 0) {
                rotated_to_end = 0;
                break;
            }
            r++;
        }
        if (rotated_to_end) return max_flips;
    }
}

void run(void) {
    int result = fannkuch(N);
    if (result < 0) {
        fprintf(stderr, "unreachable\n");
        exit(1);
    }
}
