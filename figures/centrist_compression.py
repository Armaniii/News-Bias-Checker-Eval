"""
Centrist compression — side-by-side confusion matrix heatmaps.
Shows where each true lean class gets classified, revealing centrist pull.
"""

import json, pathlib, sys, csv
from collections import defaultdict
csv.field_size_limit(sys.maxsize)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# ── Palette ──
SONNET_COLOR   = "#C55A11"   # warm orange (Anthropic)
GPT_COLOR      = "#1E4067"   # deep navy
BG_COLOR       = "#FAF8F5"   # warm off-white
GRID_COLOR     = "#EBDDAF"   # warm tan
TEXT_DARK      = "#1E4067"   # deep navy
TEXT_MID       = "#658197"   # muted blue-grey
SPINE_COLOR    = "#D9B5B3"   # soft rose
ACCENT_WARM    = "#C55A11"

# AllSides lean icon colors
LEAN_COLORS = {
    "Left":       "#2E64A0",
    "Lean Left":  "#9DC8EB",
    "Center":     "#96659E",
    "Lean Right": "#D9B5B3",
    "Right":      "#CB2127",
}

# ── Config ──
RESULTS = pathlib.Path(__file__).resolve().parent.parent / "results" / "rollout"
LEAN_ORDER = ["Left", "Lean Left", "Center", "Lean Right", "Right"]
LEAN_SHORT = ["L", "LL", "C", "LR", "R"]
LEAN_MAP   = {"Left": -2, "Lean Left": -1, "Center": 0, "Lean Right": 1, "Right": 2}
MODELS = [
    ("claude-sonnet-4-5", "Claude Sonnet 4.5", SONNET_COLOR),
    ("gpt-4.1",           "GPT-4.1",           GPT_COLOR),
]

# ── Gather data ──
def build_confusion(model_key):
    """Returns 5x5 confusion matrix and per-row average shift."""
    rdir = RESULTS / "eval-c" / "full" / model_key
    matrix = np.zeros((5, 5), dtype=int)
    shifts = defaultdict(list)

    for f in sorted(rdir.glob("*.json")):
        with open(f) as fh:
            r = json.load(fh)
        true_lean = r.get("labeled_lean") or r.get("article_meta", {}).get("labeled_lean", "")
        parsed = r.get("parsed_output")
        if not true_lean or not parsed or not isinstance(parsed, dict):
            continue
        pred_lean = parsed.get("lean", "")
        if true_lean not in LEAN_MAP or pred_lean not in LEAN_MAP:
            continue
        ti = LEAN_ORDER.index(true_lean)
        pi = LEAN_ORDER.index(pred_lean)
        matrix[ti][pi] += 1
        shifts[true_lean].append(LEAN_MAP[pred_lean] - LEAN_MAP[true_lean])

    avg_shifts = []
    for lean in LEAN_ORDER:
        s = shifts[lean]
        avg_shifts.append(sum(s) / len(s) if s else 0)
    return matrix, avg_shifts


def draw_lean_icon(ax, x, y, size, lean, is_xaxis=True):
    """Draw a small AllSides-style lean icon."""
    color = LEAN_COLORS[lean]
    letter = lean[0] if lean in ("Left", "Center", "Right") else lean.split()[1][0]
    # Use a simple colored square with letter
    rect = plt.Rectangle((x - size/2, y - size/2), size, size,
                          facecolor=color, edgecolor="white", linewidth=0.8,
                          transform=ax.transData, clip_on=False, zorder=10)
    ax.add_patch(rect)
    ax.text(x, y, letter, ha="center", va="center", fontsize=7,
            fontweight="800", color="white", transform=ax.transData,
            clip_on=False, zorder=11)


# ── Build figure ──
fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.2))
fig.patch.set_facecolor(BG_COLOR)

# Custom colormap: warm off-white → warm orange/navy per model
for idx, (model_key, model_label, model_color) in enumerate(MODELS):
    ax = axes[idx]
    ax.set_facecolor(BG_COLOR)

    matrix, avg_shifts = build_confusion(model_key)

    # Normalize for color intensity (0-1 within each row)
    row_totals = matrix.sum(axis=1, keepdims=True)
    row_totals[row_totals == 0] = 1
    pct_matrix = matrix / row_totals * 100

    # Custom colormap from BG to model color
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "custom", [BG_COLOR, model_color], N=256
    )

    # Draw heatmap cells
    for i in range(5):
        for j in range(5):
            val = pct_matrix[i, j]
            count = matrix[i, j]
            color = cmap(val / 100.0)

            # Cell rectangle
            rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                  facecolor=color, edgecolor=BG_COLOR,
                                  linewidth=2, zorder=2)
            ax.add_patch(rect)

            # Diagonal highlight border
            if i == j:
                rect2 = plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                       facecolor="none", edgecolor=model_color,
                                       linewidth=2.5, linestyle="-", zorder=3,
                                       alpha=0.6)
                ax.add_patch(rect2)

            # Cell text
            if count > 0:
                text_color = "white" if val > 45 else TEXT_DARK
                ax.text(j, i, str(count), ha="center", va="center",
                        fontsize=14, fontweight="700", color=text_color, zorder=4)
                # Percentage below count
                ax.text(j, i + 0.28, f"{val:.0f}%", ha="center", va="center",
                        fontsize=8, fontweight="400", color=text_color, alpha=0.8,
                        zorder=4)

    # Avg shift annotations on right side
    for i, shift in enumerate(avg_shifts):
        arrow = "\u2192" if shift > 0 else "\u2190" if shift < 0 else "\u2022"
        shift_color = "#B71E23" if shift > 0 else "#2E64A0" if shift < 0 else TEXT_MID
        ax.text(5.1, i, f"{arrow} {abs(shift):.2f}",
                ha="left", va="center", fontsize=10, fontweight="600",
                color=shift_color, zorder=5)

    # Axis setup
    ax.set_xlim(-0.5, 4.5)
    ax.set_ylim(4.5, -0.5)  # Invert y so Left is at top
    ax.set_aspect("equal")

    # Tick labels
    ax.set_xticks(range(5))
    ax.set_xticklabels(LEAN_SHORT, fontsize=11, fontweight="500", color=TEXT_DARK)
    ax.set_yticks(range(5))
    ax.set_yticklabels(LEAN_ORDER if idx == 0 else [""] * 5,
                       fontsize=10.5, fontweight="500", color=TEXT_DARK)

    # Labels
    ax.set_xlabel("Predicted Lean", fontsize=11.5, fontweight="500",
                  color=TEXT_DARK, labelpad=10)
    if idx == 0:
        ax.set_ylabel("True Lean (AllSides)", fontsize=11.5, fontweight="500",
                      color=TEXT_DARK, labelpad=10)

    # Spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)

    # Model title
    ax.set_title(model_label, fontsize=15, fontweight="700", color=model_color,
                 pad=14)

    # "Avg Shift" header on right
    ax.text(5.1, -0.7, "Avg\nShift", ha="left", va="center", fontsize=8,
            fontweight="500", color=TEXT_MID, linespacing=1.1)

# Suptitle
fig.suptitle("Centrist Compression in Lean Classification",
             fontsize=18, fontweight="700", color=TEXT_DARK, y=1.02)

plt.tight_layout(rect=[0, 0, 0.95, 0.96])
out_path = pathlib.Path(__file__).resolve().parent / "centrist_compression.png"
fig.savefig(out_path, dpi=250, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"\n\u2713 Saved to {out_path}")
