"""Plot pyperformance JSON results across Python versions.

Reads results/pyperf-*.json, emits one bar chart per benchmark + a heatmap
under results/plots/pyperf/.
"""

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

RESULTS_DIR = Path(__file__).parent / "results"
PLOTS_DIR = RESULTS_DIR / "plots" / "pyperf"
FILE_RE = re.compile(r"pyperf-(?P<ver>[\d.]+)\.json$")


def load_suite(path: Path) -> dict[str, float]:
    """Return {benchmark_name: mean_seconds} from a pyperf BenchmarkSuite JSON."""
    data = json.loads(path.read_text())
    out: dict[str, float] = {}
    for bench in data.get("benchmarks", []):
        meta = bench.get("metadata") or bench["runs"][0].get("metadata", {})
        name = meta.get("name", "?")
        values: list[float] = []
        for run in bench.get("runs", []):
            values.extend(run.get("values", []))
        if values:
            out[name] = sum(values) / len(values)
    return out


def main() -> None:
    files = sorted(RESULTS_DIR.glob("pyperf-*.json"))
    if not files:
        raise SystemExit(f"no pyperf-*.json in {RESULTS_DIR}")

    rows = []
    for f in files:
        m = FILE_RE.search(f.name)
        if not m:
            continue
        ver = m.group("ver")
        for name, mean in load_suite(f).items():
            rows.append({"python_version": ver, "benchmark": name, "mean_s": mean})

    df = pd.DataFrame(rows)
    if df.empty:
        raise SystemExit("no benchmarks parsed")

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # Bar chart per benchmark
    for bench, sub in df.groupby("benchmark"):
        sub = sub.sort_values("python_version")
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(sub["python_version"], sub["mean_s"])
        ax.set_title(f"pyperf:{bench} — mean runtime")
        ax.set_xlabel("Python version")
        ax.set_ylabel("seconds (lower = faster)")
        for i, v in enumerate(sub["mean_s"]):
            ax.text(i, v, f"{v:.4f}", ha="center", va="bottom", fontsize=8)
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / f"{bench}.png", dpi=120)
        plt.close(fig)

    # Heatmap: rows=benchmarks, cols=versions, color=relative slowdown vs fastest
    pivot = df.pivot(index="benchmark", columns="python_version", values="mean_s")
    rel = pivot.div(pivot.min(axis=1), axis=0)
    fig, ax = plt.subplots(figsize=(8, max(6, 0.3 * len(pivot))))
    im = ax.imshow(rel.values, aspect="auto", cmap="RdYlGn_r")
    ax.set_xticks(range(len(rel.columns)))
    ax.set_xticklabels(rel.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(rel.index)))
    ax.set_yticklabels(rel.index, fontsize=7)
    for i in range(rel.shape[0]):
        for j in range(rel.shape[1]):
            ax.text(j, i, f"{rel.values[i, j]:.2f}", ha="center", va="center", fontsize=6)
    ax.set_title("pyperformance: relative runtime (1.00 = fastest version)")
    fig.colorbar(im, ax=ax, label="x slower than fastest")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "_heatmap.png", dpi=120)
    plt.close(fig)

    print(f"wrote {len(df['benchmark'].unique())} pyperf plots to {PLOTS_DIR}")


if __name__ == "__main__":
    main()
