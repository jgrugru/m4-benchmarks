/* Float ops: sin/cos/sqrt over many points. */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include "common.h"

#define POINTS 2000000

void run(void) {
    double total = 0.0;
    for (long i = 0; i < POINTS; i++) {
        double x = (double)i * 0.0001;
        total += sin(x) * cos(x) + sqrt(x + 1.0);
    }
    if (total == 0.0) {
        fprintf(stderr, "unreachable\n");
        exit(1);
    }
}
