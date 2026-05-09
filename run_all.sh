#!/usr/bin/env bash
# Run every benchmark on every Python version + C. Append rows to results/results.csv.
# Pass --fresh to wipe results.csv before running.
set -euo pipefail

cd "$(dirname "$0")"
unset VIRTUAL_ENV

FRESH=0
for arg in "$@"; do
    case "$arg" in
        --fresh) FRESH=1 ;;
        *) echo "unknown arg: $arg" >&2; exit 2 ;;
    esac
done

if [[ "$FRESH" == "1" ]]; then
    echo "=== --fresh: wiping results/results.csv ==="
    rm -f results/results.csv
fi

VERSIONS=("3.11" "3.12" "3.13" "3.14" "3.14t")
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
    if [[ "$v" == *t ]]; then
        export PYTHON_GIL=0
    else
        unset PYTHON_GIL
    fi
    for b in "${BENCHES[@]}"; do
        uv run --python "$v" python runner.py "$b"
    done
done

unset PYTHON_GIL

echo "=== building C benchmarks ==="
make -C c_benchmarks -j

echo "=== C ==="
export UV_PROJECT_ENVIRONMENT=".venv-3.12"
for b in "${BENCHES[@]}"; do
    uv run --python 3.12 python runner.py --lang c "$b"
done

echo "=== plotting ==="
uv run --python 3.12 python plot.py
