#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "common.h"

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

int main(int argc, char **argv) {
    int iters = 5;
    for (int i = 1; i + 1 < argc; i++) {
        if (strcmp(argv[i], "-n") == 0) {
            iters = atoi(argv[i + 1]);
        }
    }
    if (iters < 1) iters = 1;

    run(); /* warmup */

    for (int i = 0; i < iters; i++) {
        double t0 = now_sec();
        run();
        double dt = now_sec() - t0;
        printf("%.9f\n", dt);
    }
    return 0;
}
