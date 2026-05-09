"""Read results.csv, emit annotated bar charts, heatmap, and category overview."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

RESULTS_CSV = Path(__file__).parent / "results" / "results.csv"
PLOTS_DIR = Path(__file__).parent / "results" / "plots"

# Metadata per benchmark. Single source of truth for plot annotations.
BENCH_INFO: dict[str, dict[str, str]] = {
    "float_ops": {
        "category": "single-core",
        "axis": "float",
        "desc": "sin/cos/sqrt over 2M points; pure-Python interpreter float loop",
    },
    "mandelbrot": {
        "category": "single-core",
        "axis": "float",
        "desc": "400x400 escape-time fractal; tight float loop with branches",
    },
    "nbody": {
        "category": "single-core",
        "axis": "float",
        "desc": "5-body gravitational sim, 250k steps; list + float math",
    },
    "fannkuch": {
        "category": "single-core",
        "axis": "integer",
        "desc": "pancake-flipping permutations N=10; integer + list slicing",
    },
    "pidigits": {
        "category": "single-core",
        "axis": "bignum",
        "desc": "spigot algorithm, 8000 digits of pi; arbitrary-precision int",
    },
    "prime_sieve": {
        "category": "single-core",
        "axis": "memory",
        "desc": "Eratosthenes sieve to 50M; bytearray writes, memory bandwidth",
    },
    "matmul_numpy": {
        "category": "native-BLAS",
        "axis": "float (SIMD)",
        "desc": "3000x3000 float64 gemm via Apple Accelerate (SME + threads)",
    },
    "sha256_mp": {
        "category": "multi-core",
        "axis": "hash",
        "desc": "SHA-256 fan-out across all CPU cores via multiprocessing.Pool",
    },
}

CATEGORY_COLORS = {
    "single-core": "#4C72B0",
    "multi-core": "#DD8452",
    "native-BLAS": "#55A868",
}

CATEGORY_ORDER = ["single-core", "multi-core", "native-BLAS"]


def _info(bench: str) -> dict[str, str]:
    return BENCH_INFO.get(
        bench, {"category": "unknown", "axis": "unknown", "desc": "(no metadata)"}
    )


def plot_per_benchmark(agg: pd.DataFrame) -> None:
    for bench, sub in agg.groupby("benchmark"):
        info = _info(bench)
        sub = sub.sort_values("python_version")
        color = CATEGORY_COLORS.get(info["category"], "#888888")

        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.bar(sub["python_version"], sub["median_s"], color=color)
        ax.set_xlabel("Python version")
        ax.set_ylabel("seconds (lower = faster)")
        for i, v in enumerate(sub["median_s"]):
            ax.text(i, v, f"{v:.3f}s", ha="center", va="bottom", fontsize=9)

        ax.set_title(
            f"{bench}  —  {info['category']} / {info['axis']}",
            fontsize=12,
            fontweight="bold",
        )
        fig.suptitle("")
        fig.text(
            0.5,
            0.93,
            info["desc"],
            ha="center",
            va="top",
            fontsize=9,
            style="italic",
            color="#444",
        )
        fig.tight_layout(rect=(0, 0, 1, 0.91))
        fig.savefig(PLOTS_DIR / f"{bench}.png", dpi=120)
        plt.close(fig)


def plot_heatmap(agg: pd.DataFrame) -> None:
    pivot = agg.pivot(index="benchmark", columns="python_version", values="median_s")
    # Sort rows by category then name
    order = sorted(
        pivot.index,
        key=lambda b: (CATEGORY_ORDER.index(_info(b)["category"])
                       if _info(b)["category"] in CATEGORY_ORDER else 99, b),
    )
    pivot = pivot.loc[order]
    rel = pivot.div(pivot.min(axis=1), axis=0)

    fig, ax = plt.subplots(figsize=(9, max(4.5, 0.55 * len(pivot))))
    im = ax.imshow(rel.values, aspect="auto", cmap="RdYlGn_r")
    ax.set_xticks(range(len(rel.columns)))
    ax.set_xticklabels(rel.columns, rotation=0)
    ax.set_yticks(range(len(rel.index)))
    labels = [f"{b}  [{_info(b)['category']}/{_info(b)['axis']}]" for b in rel.index]
    ax.set_yticklabels(labels, fontsize=8)
    for i in range(rel.shape[0]):
        for j in range(rel.shape[1]):
            ax.text(j, i, f"{rel.values[i, j]:.2f}x", ha="center", va="center", fontsize=8)
    ax.set_title("Relative runtime per benchmark (1.00 = fastest version)")
    fig.colorbar(im, ax=ax, label="x slower than fastest")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "_heatmap.png", dpi=120)
    plt.close(fig)


def plot_category_overview(agg: pd.DataFrame) -> None:
    """Grouped bars: x=benchmark grouped by category, color=python version."""
    df = agg.copy()
    df["category"] = df["benchmark"].map(lambda b: _info(b)["category"])
    df = df.sort_values(
        ["category", "benchmark", "python_version"],
        key=lambda s: s.map(lambda v: CATEGORY_ORDER.index(v) if v in CATEGORY_ORDER else 99)
        if s.name == "category" else s,
    )

    versions = sorted(df["python_version"].unique())
    benches = list(dict.fromkeys(df["benchmark"].tolist()))  # preserve order
    n_v = len(versions)
    bar_w = 0.8 / n_v

    fig, ax = plt.subplots(figsize=(max(10, 1.0 * len(benches)), 5))
    x = list(range(len(benches)))
    for vi, ver in enumerate(versions):
        sub = df[df["python_version"] == ver].set_index("benchmark").reindex(benches)
        offsets = [xi + (vi - n_v / 2 + 0.5) * bar_w for xi in x]
        ax.bar(offsets, sub["median_s"].values, width=bar_w, label=f"py{ver}")

    ax.set_xticks(x)
    ax.set_xticklabels(benches, rotation=30, ha="right")
    ax.set_ylabel("seconds (lower = faster)")
    ax.set_title("All benchmarks by category — runtime per Python version")
    ax.legend(title="Python")

    # Category bands across the bottom
    ymin, ymax = ax.get_ylim()
    band_y = ymax * 1.02
    ax.set_ylim(ymin, ymax * 1.15)
    cat_for = {b: _info(b)["category"] for b in benches}
    last_cat = None
    start = 0
    for i, b in enumerate(benches + [None]):
        cat = cat_for.get(b) if b else None
        if cat != last_cat:
            if last_cat is not None:
                mid = (start + i - 1) / 2
                color = CATEGORY_COLORS.get(last_cat, "#888")
                ax.axvspan(start - 0.5, i - 0.5, ymin=0.95, ymax=1.0, color=color, alpha=0.25)
                ax.text(mid, band_y, last_cat, ha="center", va="bottom",
                        fontsize=9, fontweight="bold", color=color)
            start = i
            last_cat = cat

    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "_overview.png", dpi=120)
    plt.close(fig)


def main() -> None:
    if not RESULTS_CSV.exists():
        raise SystemExit(f"no results at {RESULTS_CSV}")

    df = pd.read_csv(RESULTS_CSV)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    agg = df.groupby(["benchmark", "python_version"], as_index=False)["median_s"].median()

    plot_per_benchmark(agg)
    plot_heatmap(agg)
    plot_category_overview(agg)

    print(f"wrote plots to {PLOTS_DIR}")


if __name__ == "__main__":
    main()
