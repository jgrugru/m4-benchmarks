# m4-benchmarks

Python CPU benchmarks for Apple M4. Runs against Python 3.11, 3.12, 3.13, 3.14, and 3.14t (free-threaded / no-GIL) via `uv`.

## Setup

```bash
uv python install 3.11 3.12 3.13 3.14 3.14t
```

Create individual .venvs for each environment
```bash
uv venv .venv-3.11 --python 3.11
uv venv .venv-3.12 --python 3.12
uv venv .venv-3.13 --python 3.13
uv venv .venv-3.14 --python 3.14
uv venv .venv-3.14t --python 3.14t
```

`3.14t` = free-threaded build (PEP 703). GIL disabled by default; scripts export `PYTHON_GIL=0` only for `*t` versions to keep C extensions from re-enabling it.

## Run all benchmarks

```bash
./run_all.sh
```

Loops 5 versions × 8 benchmarks. Appends rows to `results/results.csv`. Auto-plots at end.

If a prior shell exported `PYTHON_GIL=0` globally, non-`t` Pythons crash with `Disabling the GIL is not supported by this build`. Clear it before running:

```bash
unset PYTHON_GIL
./run_all.sh
```

## Plot only (no re-run)

```bash
UV_PROJECT_ENVIRONMENT=.venv-3.13 uv run --python 3.13 python plot.py
```

PNGs land in `results/plots/`:
- `<benchmark>.png` — bar chart, runtime per version
- `_heatmap.png` — all benchmarks × versions, relative speed

## Run single benchmark on single version

```bash
UV_PROJECT_ENVIRONMENT=.venv-3.12 uv run --python 3.12 python runner.py mandelbrot
```

`UV_PROJECT_ENVIRONMENT` keeps per-version venvs separate. Without it `uv` rebuilds `.venv` and trashes prior version's install.

Optional flags:
- `-n 10` — iterations (default 5)
- `--notes "thermal throttle test"` — free-text column in CSV

## Benchmarks

| Name | Stresses |
|------|----------|
| `float_ops` | Pure-Python float math (sin/cos/sqrt) |
| `mandelbrot` | Pure-Python escape-time loop, float-heavy |
| `nbody` | Pure-Python physics sim, list/float heavy |
| `fannkuch` | Pure-Python integer permutation |
| `pidigits` | Bignum arithmetic |
| `prime_sieve` | Bytearray + integer, memory bandwidth |
| `matmul_numpy` | NumPy gemm via Apple Accelerate / SME |
| `sha256_mp` | All-core multiprocess SHA-256 fan-out |

## Layout

```
benchmarks/         one file per benchmark, each exposes run()
runner.py           times one benchmark, appends CSV row
plot.py             CSV -> PNG plots
plot_pyperf.py      pyperf JSON -> PNG plots
run_all.sh          loop versions x benchmarks (own suite)
run_pyperf.sh       loop versions x pyperformance + plot
results/            results.csv, pyperf-*.json, plots/
```

## Add a benchmark

Drop `benchmarks/foo.py` with a `run()` function. Add `foo` to `BENCHES` in `run_all.sh`.

## Pyperformance (full official suite)

Run + plot:

```bash
./run_pyperf.sh
```

Slow — pyperformance runs ~60 benchmarks per version. Outputs:
- `results/pyperf-3.11.json`, `pyperf-3.12.json`, `pyperf-3.13.json`, `pyperf-3.14.json`, `pyperf-3.14t.json`
- `results/plots/pyperf/<benchmark>.png` + `_heatmap.png`
- text comparison printed at end

Some pyperformance benches may skip on `3.14t` if a C extension lacks a free-threaded wheel.

Plot only (after JSONs exist):

```bash
UV_PROJECT_ENVIRONMENT=.venv-3.13 uv run --python 3.13 python plot_pyperf.py
```

Single version manual:

```bash
UV_PROJECT_ENVIRONMENT=.venv-pyperf-3.12 uv run --python 3.12 --with pyperformance \
    pyperformance run -o results/pyperf-3.12.json
```

Text-only comparison (no plot):

```bash
uv run --with pyperformance pyperformance compare \
    results/pyperf-3.11.json results/pyperf-3.13.json
```

## Reset results

```bash
rm results/results.csv results/pyperf-*.json
rm -rf results/plots
```

CSV is append-only — re-runs add new rows, plots use median across rows per (benchmark, version).
