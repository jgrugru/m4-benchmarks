/* Mandelbrot set. Float-heavy escape-time loop. */

#include <stdio.h>
#include <stdlib.h>

#include "common.h"

#define WIDTH 400
#define HEIGHT 400
#define MAX_ITER 200

void run(void) {
    long count = 0;
    for (int py = 0; py < HEIGHT; py++) {
        double cy = ((double)py / HEIGHT) * 2.0 - 1.0;
        for (int px = 0; px < WIDTH; px++) {
            double cx = ((double)px / WIDTH) * 3.5 - 2.5;
            double x = 0.0, y = 0.0;
            int escaped = 0;
            for (int i = 0; i < MAX_ITER; i++) {
                double x2 = x * x;
                double y2 = y * y;
                if (x2 + y2 > 4.0) {
                    escaped = 1;
                    break;
                }
                y = 2.0 * x * y + cy;
                x = x2 - y2 + cx;
            }
            if (!escaped) count++;
        }
    }
    if (count < 0) {
        fprintf(stderr, "unreachable\n");
        exit(1);
    }
}
