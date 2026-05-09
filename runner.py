"""Benchmark runner. Imports a benchmark module, times its run() function, appends a row to results.csv."""

import argparse
import csv
import importlib
import os
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_CSV = RESULTS_DIR / "results.csv"
HEADER = [
    "timestamp",
    "python_version",
    "python_impl",
    "benchmark",
    "median_s",
    "min_s",
    "max_s",
    "iterations",
    "cpu_count",
    "notes",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark", help="Module name under benchmarks/ (e.g. mandelbrot)")
    parser.add_argument("-n", "--iterations", type=int, default=5)
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    module = importlib.import_module(f"benchmarks.{args.benchmark}")
    if not hasattr(module, "run"):
        print(f"benchmarks.{args.benchmark} missing run()", file=sys.stderr)
        sys.exit(1)

    # Warmup
    module.run()

    timings = []
    for _ in range(args.iterations):
        t0 = time.perf_counter()
        module.run()
        timings.append(time.perf_counter() - t0)

    median = statistics.median(timings)
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python_version": platform.python_version(),
        "python_impl": platform.python_implementation(),
        "benchmark": args.benchmark,
        "median_s": f"{median:.6f}",
        "min_s": f"{min(timings):.6f}",
        "max_s": f"{max(timings):.6f}",
        "iterations": args.iterations,
        "cpu_count": os.cpu_count(),
        "notes": args.notes,
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    new_file = not RESULTS_CSV.exists()
    with RESULTS_CSV.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        if new_file:
            writer.writeheader()
        writer.writerow(row)

    print(
        f"{args.benchmark:20s} py{row['python_version']:8s} median={median:.4f}s "
        f"min={min(timings):.4f}s max={max(timings):.4f}s"
    )


if __name__ == "__main__":
    main()
