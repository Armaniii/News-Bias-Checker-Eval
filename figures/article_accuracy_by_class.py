"""
Article-level classification accuracy by class.
Ground truth: Opus 4.6 article-level bias ratings (not outlet lean).
"""

import json, pathlib, sys, csv
from collections import defaultdict
csv.field_size_limit(sys.maxsize)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mtick
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import numpy as np

# ── Palette ──
SONNET_COLOR = "#C55A11"
GPT_COLOR    = "#1E4067"
BG_COLOR     = "#FAF8F5"
GRID_COLOR   = "#EBDDAF"
TEXT_DARK    = "#2D2D2D"
TEXT_MID     = "#2D2D2D"
SPINE_COLOR  = "#D9B5B3"

LEAN_COLORS = {
    "Left":       "#2E64A0",
    "Lean Left":  "#9DC8EB",
    "Center":     "#96659E",
    "Lean Right": "#D9B5B3",
    "Right":      "#CB2127",
}

ICON_FILES = {
    "Left":       "left.png",
    "Lean Left":  "leanleft.png",
    "Center":     "center.png",
    "Lean Right": "leanright.png",
    "Right":      "right.png",
}

# ── Config ──
ROOT = pathlib.Path(__file__).resolve().parent.parent
LEAN_ORDER = ["Left", "Lean Left", "Center", "Lean Right", "Right"]
LEAN_MAP   = {"Left": -2, "Lean Left": -1, "Center": 0, "Lean Right": 1, "Right": 2}

MODELS = {
    "claude-sonnet-4-5": {"label": "Claude Sonnet 4.5", "color": SONNET_COLOR},
    "gpt-4.1":           {"label": "GPT-4.1",           "color": GPT_COLOR},
}


def classify_rating(rating):
    if rating <= -3.00: return "Left"
    if rating <= -1.00: return "Lean Left"
    if rating <=  0.99: return "Center"
    if rating <=  2.99: return "Lean Right"
    return "Right"


# ── Load Opus article-level ground truth ──
opus = {}
rdir = ROOT / "results" / "article_ratings" / "claude-opus-4-6"
for f in sorted(rdir.glob("*.json")):
    with open(f) as fh:
        r = json.load(fh)
    if r.get("rating") is not None:
        opus[r["article_id"]] = {
            "rating": r["rating"],
            "lean": r.get("corrected_lean", r.get("predicted_lean", "")),
        }

# ── Load Eval C predictions ──
def load_eval_c(model_key):
    preds = {}
    rdir = ROOT / "results" / "rollout" / "eval-c" / "full" / model_key
    for f in sorted(rdir.glob("*.json")):
        with open(f) as fh:
            r = json.load(fh)
        aid = r.get("article_id", "")
        parsed = r.get("parsed_output")
        if parsed and isinstance(parsed, dict) and parsed.get("lean"):
            preds[aid] = parsed["lean"]
    return preds


# ── Compute per-class accuracy ──
rates = {}
counts = {}
for mk, meta in MODELS.items():
    preds = load_eval_c(mk)
    rates[mk] = {}
    counts[mk] = {}
    for lean in LEAN_ORDER:
        # Articles where Opus says ground truth = lean
        articles = [(aid, preds[aid]) for aid in preds
                     if aid in opus and opus[aid]["lean"] == lean]
        correct = sum(1 for aid, pred in articles if pred == lean)
        n = len(articles)
        rates[mk][lean] = correct / n * 100 if n else 0
        counts[mk][lean] = n

# ── Print table ──
print(f"\n{'Class':<12}", end="")
for mk in MODELS:
    print(f"  {MODELS[mk]['label']:>20}", end="")
print()
print("-" * 56)
for lean in LEAN_ORDER:
    print(f"{lean:<12}", end="")
    for mk in MODELS:
        n = counts[mk][lean]
        r = rates[mk][lean]
        print(f"  {r:>5.0f}% (n={n:<3})", end="")
    print()


# ── Load AllSides icon PNGs ──
def place_icon(ax, data_x, lean, y_pos, zoom=0.15):
    icon_path = ROOT / ICON_FILES[lean]
    img = mpimg.imread(str(icon_path))
    im = OffsetImage(img, zoom=zoom)
    ab = AnnotationBbox(im, (data_x, y_pos), frameon=False,
                        box_alignment=(0.5, 0.5),
                        xycoords="data", clip_on=False, zorder=10)
    ax.add_artist(ab)


# ── Plot ──
fig, ax = plt.subplots(figsize=(11, 6.5))
fig.patch.set_facecolor(BG_COLOR)
ax.set_facecolor(BG_COLOR)

bar_width = 0.34
x = np.arange(len(LEAN_ORDER))

for i, (mk, meta) in enumerate(MODELS.items()):
    offsets = x + (i - 0.5) * bar_width
    values = [rates[mk][lean] for lean in LEAN_ORDER]
    bars = ax.bar(
        offsets, values, bar_width,
        label=meta["label"], color=meta["color"],
        edgecolor=BG_COLOR, linewidth=1.2,
        zorder=3, alpha=0.92,
    )
    for bar, val, lean in zip(bars, values, LEAN_ORDER):
        n = counts[mk][lean]
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.8,
            f"{val:.0f}%",
            ha="center", va="bottom",
            fontsize=11, fontweight="700",
            color=meta["color"],
        )

# AllSides icon PNGs as x-axis labels
for i, lean in enumerate(LEAN_ORDER):
    place_icon(ax, x[i], lean, y_pos=-10, zoom=0.15)

# Axes
ax.set_xticks(x)
ax.set_xticklabels([""] * len(LEAN_ORDER))
ax.set_ylim(-18, 108)
ax.yaxis.set_major_locator(mtick.FixedLocator([0, 20, 40, 60, 80, 100]))
ax.yaxis.set_major_formatter(mtick.FuncFormatter(
    lambda v, _: f"{int(v)}%" if v >= 0 else ""))
ax.tick_params(axis="y", colors=TEXT_MID, labelsize=11)
ax.tick_params(axis="x", length=0)

# Grid — only at visible tick positions (>= 0)
ax.grid(axis="y", color=GRID_COLOR, linewidth=0.7, zorder=0)
ax.set_axisbelow(True)

# Spines
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.spines["left"].set_color(SPINE_COLOR)
ax.spines["left"].set_linewidth(0.8)
ax.spines["left"].set_bounds(0, 100)
ax.spines["bottom"].set_color(SPINE_COLOR)
ax.spines["bottom"].set_linewidth(0.8)
ax.spines["bottom"].set_position(("data", 0))
ax.tick_params(axis="y", length=3, color=SPINE_COLOR)

# Title
ax.set_title(
    "Lean Classification Accuracy",
    fontsize=17, fontweight="700", pad=16, color=TEXT_DARK,
)

# Legend
legend = ax.legend(
    loc="upper center", bbox_to_anchor=(0.5, -0.02),
    ncol=2, frameon=True, fancybox=True, shadow=False,
    fontsize=12, edgecolor=SPINE_COLOR, facecolor=BG_COLOR,
    borderpad=0.8, columnspacing=2.5, handlelength=1.5,
)
legend.get_frame().set_linewidth(0.6)

plt.tight_layout()
out_path = pathlib.Path(__file__).resolve().parent / "article_accuracy_by_class.png"
fig.savefig(out_path, dpi=600, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"\n\u2713 Saved to {out_path}")
