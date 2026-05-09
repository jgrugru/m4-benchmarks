# m4-benchmarks

Python CPU benchmarks for Apple M4. Runs against Python 3.11, 3.12, 3.13, 3.14, and 3.14t (free-threaded / no-GIL) via `uv`.

## Setup

```bash
uv python install 3.11 3.12 3.13 3.14 3.14t
```

Dependencies required for the C benchmarks, using Brew
```bash
brew install gmp openssl@3
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

Loops 5 Python versions × 8 benchmarks + 8 C benchmarks. Appends rows to `results/results.csv`. Auto-plots at end.

Pass `--fresh` to wipe `results/results.csv` first (default keeps history; plots take median across all runs):

```bash
./run_all.sh --fresh
```

If a prior shell exported `PYTHON_GIL=0` globally, non-`t` Pythons crash with `Disabling the GIL is not supported by this build`. Clear it before running:

```bash
unset PYTHON_GIL
./run_all.sh
```

## Plot only (no re-run)

```bash
UV_PROJECT_ENVIRONMENT=.venv-3.12 uv run --python 3.12 python plot.py
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

### What each benchmark is doing

Per-benchmark explainer plots (algorithm sketch + workload size + what hardware
component it stresses + references) live in `results/plots/explainers/`.
Regenerate with:

```bash
UV_PROJECT_ENVIRONMENT=.venv-3.12 uv run --python 3.12 python plot_explainer.py
```

Overview of all 8: [`results/plots/explainers/_overview_explainer.png`](results/plots/explainers/_overview_explainer.png)

| Benchmark | Plot | What it does |
|-----------|------|--------------|
| `float_ops` | [png](results/plots/explainers/float_ops.png) | Pure-Python loop, 2,000,000 iters of `sin(x)*cos(x) + sqrt(x+1)`. Measures interpreter dispatch + libm — no SIMD reaches the FPU through the eval loop. |
| `mandelbrot` | [png](results/plots/explainers/mandelbrot.png) | 400×400 escape-time fractal, max_iter=200. `z ← z² + c` until `\|z\|² > 4`. Tight FP inner loop with data-dependent branches; allocates `PyFloat`s every step. |
| `nbody` | [png](results/plots/explainers/nbody.png) | Sun + Jupiter/Saturn/Uranus/Neptune, 250k leapfrog steps. O(N²) pairwise gravity (10 pairs), scalar FP add/mul/sqrt + list indexing. Adapted from Benchmarks Game (Mark C. Lewis). |
| `fannkuch` | [png](results/plots/explainers/fannkuch.png) | Fannkuch-redux at n=10. Generate all 10! = 3,628,800 permutations; for each, count prefix-reversals to bring 1 to front; return max. Integer + small-array work, L1-resident. (Anderson & Rettig 1994; Mazonka redux.) |
| `pidigits` | [png](results/plots/explainers/pidigits.png) | First 8000 digits of π via Gibbons' streaming spigot (2006). Möbius transform `(q,r,s,t)`; produce/consume on big integers that grow with the digit index. Pure CPython `PyLong` stress. |
| `prime_sieve` | [png](results/plots/explainers/prime_sieve.png) | Sieve of Eratosthenes up to 5×10⁷ on a `bytearray` (≈50 MB, well past L3). Slice-assignment lowers to a memset-style loop — measures DRAM bandwidth + prefetcher. |
| `matmul_numpy` | [png](results/plots/explainers/matmul_numpy.png) | `A @ B` for 3000×3000 float64. `2·N³ = 5.4×10¹⁰` FMAs dispatched once into Apple Accelerate `cblas_dgemm`, which on M4 lights up SME (Scalable Matrix Extension) tile registers. |
| `sha256_mp` | [png](results/plots/explainers/sha256_mp.png) | `multiprocessing.Pool`, one worker per core; each chains 200,000 SHA-256s. SHA-256 (FIPS 180-4) via OpenSSL EVP → ARMv8 SHA2 crypto extension. Per-process = no GIL → near-linear all-core scaling. |

## Layout

```
python_benchmarks/  one file per Python benchmark, each exposes run()
c_benchmarks/       C port of every benchmark + Makefile
runner.py           times one benchmark (Python or C), appends CSV row
plot.py             CSV -> PNG plots
plot_explainer.py   per-benchmark explainer PNGs (algorithm + stresses + refs)
plot_pyperf.py      pyperf JSON -> PNG plots
run_all.sh          loop versions x benchmarks (Python + C)
run_pyperf.sh       loop versions x pyperformance + plot
results/            results.csv, pyperf-*.json, plots/
```

## Add a benchmark

Drop `python_benchmarks/foo.py` with a `run()` function. Add `foo` to `BENCHES` in `run_all.sh`. For a C variant, drop `c_benchmarks/foo.c` defining `void run(void)` and add a build rule in `c_benchmarks/Makefile`.

## C benchmarks

C ports of every Python benchmark, treated as another "version" in the CSV (`python_version` = `C-clang<major>`, `python_impl` = `C`). Same workload sizes as Python. Compiled with `-O3 -mcpu=apple-m4`.

Backends chosen for fair compare:
- `pidigits` — GMP (`libgmp`) for arbitrary-precision int (matches Python int internals).
- `matmul_numpy` — `cblas_dgemm` via Apple Accelerate (same backend numpy uses on macOS).
- `sha256_mp` — OpenSSL EVP (same impl as Python `hashlib`), pthreads for fan-out.

System deps (Homebrew):

```bash
brew install gmp openssl@3
```

Build:

```bash
make -C c_benchmarks
```

Run all C benches (called automatically by `run_all.sh`):

```bash
for b in float_ops mandelbrot nbody fannkuch pidigits prime_sieve matmul_numpy sha256_mp; do
    uv run --python 3.12 python runner.py --lang c "$b"
done
```

Single C bench:

```bash
uv run --python 3.12 python runner.py --lang c mandelbrot
```

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
UV_PROJECT_ENVIRONMENT=.venv-3.12 uv run --python 3.12 python plot_pyperf.py
```

Single version manual:

```bash
uvx --python 3.12 --from pyperformance pyperformance run -o results/pyperf-3.12.json
```

Text-only comparison (no plot):

```bash
uvx --from pyperformance pyperformance compare \
    results/pyperf-3.11.json results/pyperf-3.13.json
```

## Reset results

```bash
rm results/results.csv results/pyperf-*.json
rm -rf results/plots
```

CSV is append-only — re-runs add new rows, plots use median across rows per (benchmark, version).
