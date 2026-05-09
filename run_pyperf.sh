#!/usr/bin/env bash
# Run pyperformance on every Python version, save JSON, then plot.
set -euo pipefail

cd "$(dirname "$0")"
unset VIRTUAL_ENV

VERSIONS=("3.11" "3.12" "3.13" "3.14" "3.14t")

mkdir -p results

for v in "${VERSIONS[@]}"; do
    echo "=== pyperformance on Python $v ==="
    if [[ "$v" == *t ]]; then
        export PYTHON_GIL=0
    else
        unset PYTHON_GIL
    fi
    uvx --python "$v" --from pyperformance \
        pyperformance run -o "results/pyperf-$v.json"
done

unset PYTHON_GIL

echo "=== plotting pyperf ==="
uv run --python 3.13 python plot_pyperf.py

echo "=== text comparison ==="
uvx --python 3.13 --from pyperformance \
    pyperformance compare results/pyperf-3.11.json results/pyperf-3.12.json results/pyperf-3.13.json results/pyperf-3.14.json results/pyperf-3.14t.json
