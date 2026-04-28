"""
Summary fidelity to source bias — grouped bar chart with trend lines.
Measures: BPS by source article bias level (from Eval A detection count).
"""

import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ── Palette ──
SONNET_COLOR = "#C55A11"
SONNET_LIGHT = "#E8C4A8"
GPT_COLOR    = "#1E4067"
GPT_LIGHT    = "#A0B8CC"
BG_COLOR     = "#FAF8F5"
GRID_COLOR   = "#EBDDAF"
TEXT_DARK    = "#2D2D2D"
SPINE_COLOR  = "#D9B5B3"

# ── Data (BPS by source bias level, eval-b full, Opus judge) ──
CATEGORIES = ["No Bias\nDetected", "Low\n(1\u20132)", "Moderate\n(3\u20134)", "High\n(5+)"]

RATES = {
    "sonnet": [2.00, 3.18, 3.55, 3.66],
    "gpt":    [2.38, 2.74, 3.00, 3.17],
}

MODELS = [
    ("sonnet", "Claude Sonnet 4.5", SONNET_COLOR, SONNET_LIGHT),
    ("gpt",    "GPT-4.1",          GPT_COLOR,    GPT_LIGHT),
]

# ── Plot ──
fig, ax = plt.subplots(figsize=(10, 6.5))
fig.patch.set_facecolor(BG_COLOR)
ax.set_facecolor(BG_COLOR)

bar_width = 0.34
x = np.arange(len(CATEGORIES))

for i, (mk, label, color, light) in enumerate(MODELS):
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
            bar.get_height() + 0.06,
            f"{val:.2f}",
            ha="center", va="bottom",
            fontsize=11, fontweight="700", color=color,
        )

    # Trend / slope line
    ax.plot(offsets, values, color=light, linewidth=2, zorder=4,
            marker="o", markersize=5, markerfacecolor="white",
            markeredgecolor=light, markeredgewidth=1.5)

# X-axis
ax.set_xticks(x)
ax.set_xticklabels(CATEGORIES, fontsize=11, fontweight="500", color=TEXT_DARK)
ax.tick_params(axis="x", length=0, pad=8)

# Y-axis: no label, darker numbers
ax.set_ylim(0, 4.3)
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
ax.tick_params(axis="y", length=3, color=SPINE_COLOR)

# Title only
ax.set_title(
    "Summary Faithfulness to Source Bias",
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
out_path = pathlib.Path(__file__).resolve().parent / "fidelity.png"
fig.savefig(out_path, dpi=600, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"\u2713 Saved to {out_path}")
