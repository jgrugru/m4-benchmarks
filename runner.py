"""Benchmark runner. Times a Python or C bench, appends a row to results.csv."""

import argparse
import csv
import importlib
import os
import platform
import re
import statistics
import subprocess
import sys
import sysconfig
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).parent
RESULTS_DIR = ROOT / "results"
RESULTS_CSV = RESULTS_DIR / "results.csv"
C_BUILD = ROOT / "c_benchmarks" / "build"

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


def time_python(bench: str, iters: int) -> list[float]:
    module = importlib.import_module(f"python_benchmarks.{bench}")
    if not hasattr(module, "run"):
        sys.exit(f"python_benchmarks.{bench} missing run()")
    module.run()  # warmup
    timings = []
    for _ in range(iters):
        t0 = time.perf_counter()
        module.run()
        timings.append(time.perf_counter() - t0)
    return timings


def time_c(bench: str, iters: int) -> list[float]:
    binary = C_BUILD / bench
    if not binary.exists():
        sys.exit(f"C binary missing: {binary}. Run `make` in c_benchmarks/.")
    proc = subprocess.run(
        [str(binary), "-n", str(iters)],
        capture_output=True,
        text=True,
        check=True,
    )
    return [float(line) for line in proc.stdout.strip().splitlines() if line.strip()]


def python_label() -> str:
    base = platform.python_version()
    if sysconfig.get_config_var("Py_GIL_DISABLED") == 1:
        return f"{base}t"
    return base


def clang_label() -> str:
    try:
        out = subprocess.run(["clang", "--version"], capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "C"
    m = re.search(r"clang version (\d+)", out)
    return f"C-clang{m.group(1)}" if m else "C"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark", help="Bench name (e.g. mandelbrot)")
    parser.add_argument("-n", "--iterations", type=int, default=5)
    parser.add_argument("--lang", default="python", choices=["python", "c"])
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    if args.lang == "python":
        timings = time_python(args.benchmark, args.iterations)
        version_label = python_label()
        impl_label = platform.python_implementation()
    else:
        timings = time_c(args.benchmark, args.iterations)
        version_label = clang_label()
        impl_label = "C"

    median = statistics.median(timings)
    row = {
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "python_version": version_label,
        "python_impl": impl_label,
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

    print(f"{args.benchmark:20s} {version_label:14s} median={median:.4f}s min={min(timings):.4f}s max={max(timings):.4f}s")


if __name__ == "__main__":
    main()
