#!/usr/bin/env bash
# Run every benchmark on every Python version. Append rows to results/results.csv.
set -euo pipefail

cd "$(dirname "$0")"
unset VIRTUAL_ENV

VERSIONS=("3.11" "3.12" "3.13")
BENCHES=(
    float_ops
    mandelbrot
    nbody
    fannkuch
    pidigits
    prime_sieve
    matmul_numpy
    sha256_mp
)

for v in "${VERSIONS[@]}"; do
    echo "=== Python $v ==="
    export UV_PROJECT_ENVIRONMENT=".venv-$v"
    for b in "${BENCHES[@]}"; do
        uv run --python "$v" python runner.py "$b"
    done
done

echo "=== plotting ==="
export UV_PROJECT_ENVIRONMENT=".venv-3.13"
uv run --python 3.13 python plot.py
