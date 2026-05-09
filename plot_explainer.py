"""Generate per-benchmark explainer PNGs.

For each benchmark, render one PNG:
  left  panel  -- a small visualization of the workload
  right panel  -- text: summary, algorithm, what it stresses, refs

Also emits an _overview_explainer.png grid combining all 8.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).parent / "results" / "plots" / "explainers"
OUT.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------------
# Per-benchmark metadata. Concise enough to fit in a text panel.
# ----------------------------------------------------------------------------

EXPLAINERS: dict[str, dict] = {
    "float_ops": {
        "title": "float_ops  --  interpreter + libm microbench",
        "summary": "Pure-Python loop over 2,000,000 points evaluating\nf(x) = sin(x)*cos(x) + sqrt(x+1).",
        "algorithm": (
            "Single for-loop accumulator. Each iteration: 3 libm calls\n"
            "(sin, cos, sqrt), one multiply, one add. Every op crosses\n"
            "the Python/C boundary -- bytecode dispatch, PyFloat box/unbox,\n"
            "indirect call into Apple's libsystem_m.\n"
            "No SIMD: interpreter blocks autovectorization."
        ),
        "stresses": ["interpreter dispatch", "PyFloat alloc", "libm transcendentals", "branch pred"],
        "size": "N = 2,000,000  ->  ~6M libm calls",
        "refs": ["CPython ceval.c", "Apple libsystem_m"],
    },
    "mandelbrot": {
        "title": "mandelbrot  --  escape-time fractal, pure Python",
        "summary": "400 x 400 grid, max_iter = 200.\nFor each pixel c, iterate z = z^2 + c\nuntil |z|^2 > 4 (escape) or cap hit.",
        "algorithm": ("Two FP multiplies + two adds per inner step,\nplus a magnitude bailout test.\nTrip count is data-dependent: pixels inside the\ncardioid run the full 200; exterior pixels exit early.\nEach z*z + c allocates fresh PyFloats."),
        "stresses": ["FP mul/add", "tight inner loop", "branch pred", "PyFloat alloc", "data-dep loop bounds"],
        "size": "160,000 pixels x up to 200 iters = up to 32M steps",
        "refs": ["Brooks-Matelski 1978; Mandelbrot 1980", "Benchmarks Game: mandelbrot"],
    },
    "nbody": {
        "title": "nbody  --  5-body solar system sim",
        "summary": "Sun + Jupiter, Saturn, Uranus, Neptune.\n250,000 leapfrog timesteps.",
        "algorithm": (
            "Pairwise gravity, O(N^2). N=5 -> 10 pair interactions/step.\n"
            "Per pair: 3-D distance, r^2, r^3 = r^2 * sqrt(r^2),\n"
            "momentum kicks on both bodies. Then drift positions by v*dt.\n"
            "Symplectic 2nd-order integrator: time-reversible,\n"
            "energy-conserving over long runs."
        ),
        "stresses": ["FP add/mul/sqrt", "list/tuple indexing", "attr lookup", "scalar (no SIMD)"],
        "size": "10 pairs x 250,000 steps = 2.5M force evals",
        "refs": ["Mark C. Lewis -- Benchmarks Game: nbody", "Leapfrog / Verlet integrator"],
    },
    "fannkuch": {
        "title": "fannkuch-redux  --  pancake-flipping perms",
        "summary": "n = 10. Generate all 10! = 3,628,800 permutations.\nFor each, count prefix-reversals to bring 1 to front.\nReturn the maximum.",
        "algorithm": (
            "Look at p[0] = k. Reverse p[0..k]. Repeat until p[0] = 1.\n"
            "Count reversals -- that's this permutation's flip count.\n"
            "Permutations generated in-place via index-cycle scheme;\n"
            "no allocation in inner loop. All integer + small array slicing.\n"
            "Working set fits in L1."
        ),
        "stresses": ["integer ops", "small-array reversal", "branch pred", "L1-resident", "loop dispatch"],
        "size": "10! = 3,628,800 permutations",
        "refs": ["Anderson & Rettig 1994", "Mazonka 'redux' variant", "Benchmarks Game: fannkuch-redux"],
    },
    "pidigits": {
        "title": "pidigits  --  spigot bignum arithmetic",
        "summary": "Compute first 8000 digits of pi via\nGibbons' streaming spigot algorithm (2006).",
        "algorithm": (
            "Maintain a Mobius transform (q,r,s,t) bounding pi.\n"
            "Each step either PRODUCE a digit (when interval endpoints\n"
            "agree on integer part) or CONSUME a new continued-fraction term.\n"
            "Each is a handful of bigint mul/add/divmod.\n"
            "Integers grow ~linearly with digit index -> superlinear total cost."
        ),
        "stresses": ["arbitrary-prec int mul/add/divmod", "PyLong allocator", "no FP, no SIMD"],
        "size": "8,000 digits  (PyLong ops grow with digit index)",
        "refs": ["Gibbons 2006: 'Unbounded Spigot Algorithms for the Digits of Pi'", "Benchmarks Game: pidigits"],
    },
    "prime_sieve": {
        "title": "prime_sieve  --  Eratosthenes, memory-bandwidth",
        "summary": "Sieve of Eratosthenes up to N = 50,000,000\non a length-N bytearray (~50 MB).",
        "algorithm": (
            "Init bytearray to 1. Mark indices 0,1 composite.\n"
            "For i = 2 .. sqrt(N): if buf[i] still prime,\n"
            "set buf[i*i :: i] = b'\\x00' * len(...).\n"
            "Slice-assignment lowers to a tight C-level memset-style loop.\n"
            "Buffer >> all caches -> measures DRAM streaming + prefetch."
        ),
        "stresses": ["memory bandwidth", "cache hierarchy", "bytearray slice store", "prefetcher"],
        "size": "N = 5e7,  ~50 MB buffer  ( >> L3 )",
        "refs": ["Eratosthenes of Cyrene, 3rd c. BCE", "Nicomachus, Intro. to Arithmetic"],
    },
    "matmul_numpy": {
        "title": "matmul_numpy  --  BLAS dgemm via Apple Accelerate / SME",
        "summary": "C = A @ B for 3000 x 3000 float64.\n2 * N^3 = 5.4e10 multiply-add ops.\nOne Python call -> Accelerate cblas_dgemm.",
        "algorithm": (
            "Standard Level-3 BLAS GEMM.\n"
            "Cache-blocked + register-tiled, vectorized inner kernels.\n"
            "On macOS arm64, NumPy '@' dispatches to Apple Accelerate.\n"
            "On M4, Accelerate routes to SME (Scalable Matrix Extension):\n"
            "outer-product instructions against tile registers,\n"
            "multi-TFLOPS from a single core. Python overhead negligible."
        ),
        "stresses": ["FP64 FMA throughput", "SME tile ops", "L1/L2 reuse via blocking", "DRAM stream"],
        "size": "N=3000, 5.4e10 FLOPs",
        "refs": ["Lawson/Hanson/Kincaid/Krogh 1979 (BLAS)", "Dongarra et al. 1990 (Level-3)", "Apple Accelerate; M4 SME"],
    },
    "sha256_mp": {
        "title": "sha256_mp  --  all-core SHA-256 fan-out",
        "summary": "multiprocessing.Pool, one worker per CPU core.\nEach worker chains 200,000 SHA-256 hashes:\n  h = sha256(h).digest()  in a loop.",
        "algorithm": (
            "SHA-256 (NIST FIPS 180-4): Merkle-Damgard + Davies-Meyer\n"
            "compression, 32-bit words, 512-bit blocks, 64 rounds,\n"
            "constants from cube-roots of first 64 primes.\n"
            "CPython hashlib -> OpenSSL EVP -> ARMv8 SHA2 crypto extension.\n"
            "Each worker is its own OS process: no GIL, near-linear scaling."
        ),
        "stresses": ["SHA-2 round throughput", "ARMv8 SHA2 ext", "all-core scaling", "process startup"],
        "size": "n_cores workers  x  200,000 hashes each",
        "refs": ["NIST FIPS 180-4", "Python hashlib (OpenSSL)", "ARMv8 crypto ext"],
    },
}


# ----------------------------------------------------------------------------
# Visual panels (one per benchmark). Each takes an Axes, draws onto it.
# ----------------------------------------------------------------------------


def viz_float_ops(ax: plt.Axes) -> None:
    """Plot f(x) = sin(x)*cos(x) + sqrt(x+1) over a sample range."""
    x = np.linspace(0, 200, 2000)
    y = np.sin(x) * np.cos(x) + np.sqrt(x + 1)
    ax.plot(x, y, color="#1f77b4", linewidth=1.0)
    ax.set_xlabel("x")
    ax.set_ylabel("f(x) = sin(x)*cos(x) + sqrt(x+1)")
    ax.set_title("Function evaluated 2,000,000 times in pure Python", fontsize=10)
    ax.grid(alpha=0.3)


def viz_mandelbrot(ax: plt.Axes) -> None:
    """Render small Mandelbrot escape-time image."""
    w, h, max_iter = 240, 240, 80
    xs = np.linspace(-2.5, 1.0, w)
    ys = np.linspace(-1.0, 1.0, h)
    cx, cy = np.meshgrid(xs, ys)
    c = cx + 1j * cy
    z = np.zeros_like(c)
    div_time = np.full(c.shape, max_iter, dtype=int)
    mask = np.ones(c.shape, dtype=bool)
    for i in range(max_iter):
        z[mask] = z[mask] * z[mask] + c[mask]
        diverged = np.abs(z) > 2
        new = diverged & mask
        div_time[new] = i
        mask &= ~diverged
    ax.imshow(div_time, extent=(-2.5, 1.0, -1.0, 1.0), cmap="twilight_shifted", origin="lower")
    ax.set_title("z <- z^2 + c, escape when |z| > 2", fontsize=10)
    ax.set_xlabel("Re(c)")
    ax.set_ylabel("Im(c)")


def viz_nbody(ax: plt.Axes) -> None:
    """Sketch sun + 4 planets on roughly-correct orbital radii."""
    ax.set_aspect("equal")
    ax.set_facecolor("#0b0b18")
    bodies = [
        ("Sun", 0.0, "#ffd24a", 280),
        ("Jupiter", 5.2, "#d8a766", 90),
        ("Saturn", 9.5, "#e3c98c", 75),
        ("Uranus", 19.2, "#9fd1e3", 50),
        ("Neptune", 30.0, "#5078e0", 50),
    ]
    rmax = 32
    for name, r, color, size in bodies:
        if r > 0:
            ax.add_patch(mpatches.Circle((0, 0), r, fill=False, edgecolor="#445", linewidth=0.6))
            ax.scatter([r], [0], s=size, c=color, edgecolor="white", linewidth=0.4, zorder=3)
            ax.text(r, 1.5, name, color="white", fontsize=8, ha="center")
        else:
            ax.scatter([0], [0], s=size, c=color, edgecolor="orange", linewidth=0.4, zorder=3)
            ax.text(0, -2.2, name, color="white", fontsize=8, ha="center")
    ax.set_xlim(-rmax, rmax)
    ax.set_ylim(-rmax, rmax)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("5 bodies, pairwise gravity (10 pairs), 250k steps", fontsize=10)


def viz_fannkuch(ax: plt.Axes) -> None:
    """Show three pancake-flip steps for a small permutation."""
    perms = [
        [3, 1, 4, 2, 0],
        [2, 4, 1, 3, 0],
        [1, 4, 2, 3, 0],
        [4, 1, 2, 3, 0],
        [0, 3, 2, 1, 4],
    ]
    labels = ["start", "flip 4", "flip 3", "flip 2", "flip 5  (done; flips=4)"]
    n = len(perms[0])
    for row, (p, lab) in enumerate(zip(perms, labels, strict=True)):
        y = len(perms) - row - 1
        for col, v in enumerate(p):
            highlight = col < (p[0] + 1) if row < len(perms) - 1 else False
            color = "#ff6b6b" if highlight else "#4a90e2"
            ax.add_patch(mpatches.Rectangle((col, y), 0.9, 0.85, facecolor=color, edgecolor="black", linewidth=0.5))
            ax.text(col + 0.45, y + 0.42, str(v + 1), ha="center", va="center", color="white", fontsize=10, fontweight="bold")
        ax.text(n + 0.3, y + 0.42, lab, va="center", fontsize=9)
    ax.set_xlim(-0.3, n + 4.5)
    ax.set_ylim(-0.3, len(perms) + 0.3)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Reverse the first p[0] elements until p[0] = 1", fontsize=10)


def viz_pidigits(ax: plt.Axes) -> None:
    """Bar chart: bigint bit-width vs digit produced (illustrative trend)."""
    n = np.arange(0, 8001, 200)
    # Heuristic: PyLong size grows ~linearly with digit index for spigot.
    bits = 8 + n * 3.4
    ax.fill_between(n, bits, color="#6c5ce7", alpha=0.4)
    ax.plot(n, bits, color="#6c5ce7", linewidth=1.4)
    ax.set_xlabel("digits produced")
    ax.set_ylabel("approx PyLong width (bits)")
    ax.set_title("Bigint operands grow with each produced digit", fontsize=10)
    ax.grid(alpha=0.3)
    digits = "3.14159265358979323846..."
    ax.text(0.98, 0.05, "pi = " + digits, transform=ax.transAxes, ha="right", fontsize=9, family="monospace", color="#333", bbox={"facecolor": "white", "edgecolor": "#ccc", "boxstyle": "round,pad=0.3"})


def viz_prime_sieve(ax: plt.Axes) -> None:
    """30x10 grid of integers 1..300, composites greyed-out."""
    cols, rows = 30, 10
    n = cols * rows
    is_prime = np.ones(n + 1, dtype=bool)
    is_prime[:2] = False
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            is_prime[i * i :: i] = False
    for k in range(1, n + 1):
        col = (k - 1) % cols
        row = rows - 1 - (k - 1) // cols
        if is_prime[k]:
            face = "#27ae60"
            tcolor = "white"
        else:
            face = "#ecf0f1"
            tcolor = "#999"
        ax.add_patch(mpatches.Rectangle((col, row), 0.95, 0.95, facecolor=face, edgecolor="#bbb", linewidth=0.4))
        ax.text(col + 0.475, row + 0.5, str(k), ha="center", va="center", fontsize=6, color=tcolor)
    ax.set_xlim(-0.2, cols + 0.2)
    ax.set_ylim(-0.2, rows + 0.2)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Cross out multiples; survivors are prime  (shown: 1..300)", fontsize=10)


def viz_matmul(ax: plt.Axes) -> None:
    """Sketch A * B = C with N labels."""
    ax.set_aspect("equal")
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis("off")

    def matrix(x, y, label, fill="#74b9ff"):
        ax.add_patch(mpatches.Rectangle((x, y), 2.5, 2.5, facecolor=fill, edgecolor="black", linewidth=0.8))
        # grid lines
        for i in range(1, 5):
            ax.plot([x + i * 0.5, x + i * 0.5], [y, y + 2.5], color="white", linewidth=0.3, alpha=0.6)
            ax.plot([x, x + 2.5], [y + i * 0.5, y + i * 0.5], color="white", linewidth=0.3, alpha=0.6)
        ax.text(x + 1.25, y - 0.4, label, ha="center", fontsize=11, fontweight="bold")

    matrix(0.5, 1.7, "A  (3000 x 3000)", fill="#74b9ff")
    ax.text(3.4, 2.95, "@", fontsize=22, ha="center", va="center")
    matrix(4.0, 1.7, "B  (3000 x 3000)", fill="#a29bfe")
    ax.text(7.0, 2.95, "=", fontsize=22, ha="center", va="center")
    matrix(7.7, 1.7, "C  (3000 x 3000)", fill="#55efc4")

    ax.text(5.5, 5.4, "5.4e10 multiply-adds  ->  Apple Accelerate cblas_dgemm  ->  M4 SME tiles", ha="center", fontsize=10)
    ax.text(5.5, 0.7, "(one Python call; runtime is FPU/SME-bound, not interpreter-bound)", ha="center", fontsize=9, color="#555", style="italic")


def viz_sha256_mp(ax: plt.Axes) -> None:
    """Draw fan-out: range(n_cores) -> Pool -> n_cores workers -> results."""
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.add_patch(mpatches.FancyBboxPatch((0.4, 2.6), 1.6, 0.8, boxstyle="round,pad=0.1", facecolor="#ffeaa7", edgecolor="black"))
    ax.text(1.2, 3.0, "range(N)", ha="center", va="center", fontsize=10)

    ax.add_patch(mpatches.FancyBboxPatch((3.0, 2.4), 1.4, 1.2, boxstyle="round,pad=0.1", facecolor="#fab1a0", edgecolor="black"))
    ax.text(3.7, 3.0, "Pool", ha="center", va="center", fontsize=11, fontweight="bold")

    n_workers = 6
    worker_x = 6.0
    worker_h = 0.55
    gap = 0.18
    total_h = n_workers * worker_h + (n_workers - 1) * gap
    y0 = (6 - total_h) / 2
    for i in range(n_workers):
        y = y0 + i * (worker_h + gap)
        ax.add_patch(mpatches.FancyBboxPatch((worker_x, y), 2.5, worker_h, boxstyle="round,pad=0.05", facecolor="#81ecec", edgecolor="black"))
        ax.text(worker_x + 1.25, y + worker_h / 2, f"core {i}: 200k x sha256(h)", ha="center", va="center", fontsize=8)
        # arrow Pool -> worker
        arr = FancyArrowPatch((4.4, 3.0), (worker_x, y + worker_h / 2), arrowstyle="->", color="#555", linewidth=0.8, mutation_scale=10)
        ax.add_patch(arr)

    arr = FancyArrowPatch((2.0, 3.0), (3.0, 3.0), arrowstyle="->", color="black", linewidth=1.2, mutation_scale=14)
    ax.add_patch(arr)

    ax.text(5.0, 5.7, "one OS process per core  =>  no GIL, near-linear scaling", ha="center", fontsize=10)


VIZ = {
    "float_ops": viz_float_ops,
    "mandelbrot": viz_mandelbrot,
    "nbody": viz_nbody,
    "fannkuch": viz_fannkuch,
    "pidigits": viz_pidigits,
    "prime_sieve": viz_prime_sieve,
    "matmul_numpy": viz_matmul,
    "sha256_mp": viz_sha256_mp,
}


# ----------------------------------------------------------------------------
# Text panel
# ----------------------------------------------------------------------------


def render_text_panel(ax: plt.Axes, info: dict) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    def section(y, header, body, header_color="#2d3436"):
        ax.text(0.0, y, header, fontsize=10, fontweight="bold", color=header_color)
        ax.text(0.0, y - 0.04, body, fontsize=9, color="#222", verticalalignment="top", wrap=True)

    # Summary
    ax.text(0.0, 0.97, "Summary", fontsize=10, fontweight="bold", color="#2d3436")
    ax.text(0.0, 0.93, info["summary"], fontsize=9.5, color="#222", verticalalignment="top")

    # Algorithm
    ax.text(0.0, 0.74, "Algorithm", fontsize=10, fontweight="bold", color="#2d3436")
    ax.text(0.0, 0.70, info["algorithm"], fontsize=9, color="#222", verticalalignment="top")

    # Stresses (chips)
    ax.text(0.0, 0.34, "Stresses", fontsize=10, fontweight="bold", color="#2d3436")
    chip_y = 0.30
    chip_x = 0.0
    for tag in info["stresses"]:
        ax.add_patch(FancyBboxPatch((chip_x, chip_y - 0.025), 0.005 + 0.012 * len(tag), 0.05, boxstyle="round,pad=0.015", facecolor="#dfe6e9", edgecolor="#b2bec3", linewidth=0.6, transform=ax.transAxes))
        ax.text(chip_x + 0.005, chip_y, tag, fontsize=8, color="#2d3436", verticalalignment="center")
        chip_x += 0.012 * len(tag) + 0.025
        if chip_x > 0.85:
            chip_x = 0.0
            chip_y -= 0.06

    # Size
    ax.text(0.0, 0.18, "Workload size", fontsize=10, fontweight="bold", color="#2d3436")
    ax.text(0.0, 0.14, info["size"], fontsize=9, color="#222", verticalalignment="top")

    # Refs
    ax.text(0.0, 0.08, "Refs", fontsize=10, fontweight="bold", color="#2d3436")
    ax.text(0.0, 0.04, "  -  " + "\n  -  ".join(info["refs"]), fontsize=8.5, color="#444", verticalalignment="top")


# ----------------------------------------------------------------------------
# Per-benchmark figure
# ----------------------------------------------------------------------------


def render_one(name: str) -> Path:
    info = EXPLAINERS[name]
    fig, (ax_viz, ax_txt) = plt.subplots(1, 2, figsize=(13, 6.2), gridspec_kw={"width_ratios": [1.15, 1.0]})
    VIZ[name](ax_viz)
    render_text_panel(ax_txt, info)
    fig.suptitle(info["title"], fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    out = OUT / f"{name}.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out


def render_overview() -> Path:
    """Single 4x2 grid: small viz + name + one-line summary per bench."""
    names = list(EXPLAINERS)
    fig, axes = plt.subplots(4, 2, figsize=(14, 18))
    for ax, name in zip(axes.flat, names, strict=True):
        VIZ[name](ax)
        info = EXPLAINERS[name]
        # First line of summary as subtitle line under the existing title
        head = info["title"]
        ax.set_title(head + "\n" + info["summary"].split("\n")[0], fontsize=10)
    fig.suptitle("m4-benchmarks  --  what each benchmark is doing", fontsize=15, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out = OUT / "_overview_explainer.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> None:
    written: list[Path] = []
    for name in EXPLAINERS:
        p = render_one(name)
        print(f"wrote {p}")
        written.append(p)
    p = render_overview()
    print(f"wrote {p}")
    written.append(p)


if __name__ == "__main__":
    main()
