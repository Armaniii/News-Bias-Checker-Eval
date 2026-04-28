"""
Perspective coverage by outlet lean — grouped bar chart.
Measures: avg distinct viewpoints represented in summaries.
"""

import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import numpy as np

# ── Palette ──
SONNET_COLOR = "#C55A11"
GPT_COLOR    = "#1E4067"
BG_COLOR     = "#FAF8F5"
GRID_COLOR   = "#EBDDAF"
TEXT_DARK    = "#2D2D2D"
SPINE_COLOR  = "#D9B5B3"

ROOT = pathlib.Path(__file__).resolve().parent.parent

# ── Data (from eval-b judgment, perspective_completeness, full condition) ──
LEAN_ORDER = ["Left", "Lean Left", "Center", "Lean Right", "Right"]

RATES = {
    "sonnet": [5.2, 5.5, 5.6, 5.0, 4.8],
    "gpt":    [4.6, 4.7, 4.4, 4.5, 4.4],
}

MODELS = [
    ("sonnet", "Claude Sonnet 4.5", SONNET_COLOR),
    ("gpt",    "GPT-4.1",          GPT_COLOR),
]

# ── Lean icon images ──
ICON_FILES = {
    "Left": ROOT / "left.png",
    "Lean Left": ROOT / "leanleft.png",
    "Center": ROOT / "center.png",
    "Lean Right": ROOT / "leanright.png",
    "Right": ROOT / "right.png",
}

# ── Plot ──
fig, ax = plt.subplots(figsize=(11, 6.5))
fig.patch.set_facecolor(BG_COLOR)
ax.set_facecolor(BG_COLOR)

bar_width = 0.34
x = np.arange(len(LEAN_ORDER))

for i, (mk, label, color) in enumerate(MODELS):
    offsets = x + (i - 0.5) * bar_width
    values = RATES[mk]
    bars = ax.bar(
        offsets, values, bar_width,
        label=label, color=color,
        edgecolor=BG_COLOR, linewidth=1.2,
        zorder=3, alpha=0.92,
    )
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.08,
            f"{val:.1f}",
            ha="center", va="bottom",
            fontsize=11, fontweight="700", color=color,
        )

# X-axis: lean icon images
ax.set_xticks(x)
ax.set_xticklabels([""] * len(LEAN_ORDER))
ax.tick_params(axis="x", length=0, pad=35)

for i, lean in enumerate(LEAN_ORDER):
    icon_path = ICON_FILES.get(lean)
    if icon_path and icon_path.exists():
        img = mpimg.imread(str(icon_path))
        imagebox = OffsetImage(img, zoom=0.35)
        ab = AnnotationBbox(imagebox, (i, 0), xybox=(0, -28),
                            xycoords=("data", "axes fraction"),
                            boxcoords="offset points",
                            frameon=False, box_alignment=(0.5, 1.0))
        ax.add_artist(ab)

# Y-axis: no label, darker numbers
ax.set_ylim(0, 7.5)
ax.tick_params(axis="y", colors=TEXT_DARK, labelsize=11)

# Grid
ax.grid(axis="y", color=GRID_COLOR, linewidth=0.7, zorder=0)
ax.set_axisbelow(True)

# Spines
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.spines["left"].set_color(SPINE_COLOR)
ax.spines["left"].set_linewidth(0.8)
ax.spines["bottom"].set_color(SPINE_COLOR)
ax.spines["bottom"].set_linewidth(0.8)
ax.tick_params(axis="x", length=0)
ax.tick_params(axis="y", length=3, color=SPINE_COLOR)

# Title only
ax.set_title(
    "Perspective Coverage by Source Outlet Lean",
    fontsize=17, fontweight="700", pad=16, color=TEXT_DARK,
)

# Legend
legend = ax.legend(
    loc="upper left",
    frameon=True, fancybox=True, shadow=False,
    fontsize=11, edgecolor=SPINE_COLOR, facecolor=BG_COLOR,
    borderpad=0.6, handlelength=1.2,
)
legend.get_frame().set_linewidth(0.6)

plt.tight_layout()
out_path = pathlib.Path(__file__).resolve().parent / "perspective_coverage_by_lean.png"
fig.savefig(out_path, dpi=350, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"\u2713 Saved to {out_path}")
