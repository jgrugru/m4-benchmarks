"""Mandelbrot set, pure Python. Float-heavy escape-time loop."""

WIDTH = 400
HEIGHT = 400
MAX_ITER = 200


def run() -> None:
    count = 0
    for py in range(HEIGHT):
        cy = (py / HEIGHT) * 2.0 - 1.0
        for px in range(WIDTH):
            cx = (px / WIDTH) * 3.5 - 2.5
            x = 0.0
            y = 0.0
            for _i in range(MAX_ITER):
                x2 = x * x
                y2 = y * y
                if x2 + y2 > 4.0:
                    break
                y = 2.0 * x * y + cy
                x = x2 - y2 + cx
            else:
                count += 1
    if count < 0:
        raise RuntimeError("unreachable")
