#!/usr/bin/env bash
# Run pyperformance on every Python version, save JSON, then plot.
set -euo pipefail

cd "$(dirname "$0")"
unset VIRTUAL_ENV

VERSIONS=("3.11" "3.12" "3.13")

mkdir -p results

for v in "${VERSIONS[@]}"; do
    echo "=== pyperformance on Python $v ==="
    export UV_PROJECT_ENVIRONMENT=".venv-pyperf-$v"
    uv run --python "$v" --with pyperformance \
        pyperformance run -o "results/pyperf-$v.json"
done

echo "=== plotting pyperf ==="
export UV_PROJECT_ENVIRONMENT=".venv-3.13"
uv run --python 3.13 python plot_pyperf.py

echo "=== text comparison ==="
export UV_PROJECT_ENVIRONMENT=".venv-pyperf-compare"
uv run --python 3.13 --with pyperformance \
    pyperformance compare results/pyperf-3.11.json results/pyperf-3.12.json results/pyperf-3.13.json
