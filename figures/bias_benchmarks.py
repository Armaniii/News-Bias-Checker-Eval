"""
Bias Benchmarks — multi-panel dot plot matching Bloom Benchmarks style.
"""

import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Palette ──
BG_COLOR     = "#FAF8F5"
TEXT_DARK    = "#2D2D2D"
TEXT_MID     = "#999999"
BORDER_COLOR = "#D5D0CA"
GRID_COLOR   = "#E5E0DA"
SONNET_COLOR = "#C55A11"
SONNET_LIGHT = "#E8B895"
GPT_COLOR    = "#3B6FA0"
GPT_LIGHT    = "#9DC0E0"

# ── Data (per-judge, 95 clean articles) ──
DATA = {
    "opus": {
        "sonnet": {"validated": 94.56, "hallucinated": 0.91, "explanation_quality": 4.04, "political_direction_bias": 3.29},
        "gpt":    {"validated": 95.78, "hallucinated": 0.60, "explanation_quality": 4.52, "political_direction_bias": 3.78},
    },
    "gpt5": {
        "sonnet": {"validated": 85.50, "hallucinated": 6.04, "explanation_quality": 4.02, "political_direction_bias": 2.16},
        "gpt":    {"validated": 91.27, "hallucinated": 2.11, "explanation_quality": 4.97, "political_direction_bias": 1.92},
    },
}

MODELS = [
    ("sonnet", "Claude Sonnet 4.5", SONNET_COLOR, SONNET_LIGHT),
    ("gpt",    "GPT-4.1",           GPT_COLOR,    GPT_LIGHT),
]

PANELS = [
    {"key": "validated",  "title": "Detection\nValidity",
     "desc": "% of detections confirmed\nor rated plausible by\nindependent judges.",
     "vmin": 0, "vmax": 100, "fmt": "{:.0f}%"},
    {"key": "hallucinated", "title": "Hallucination\nRate",
     "desc": "% of detections flagged\nas hallucinated — text not\nbiased, quoted, or absent.",
     "vmin": 0, "vmax": 10, "fmt": "{:.1f}%"},
    {"key": "explanation_quality", "title": "Explanation\nQuality",
     "desc": "Specificity and grounding\nof bias explanations.\n1 = excellent, 10 = generic.",
     "vmin": 0, "vmax": 10, "fmt": "{:.2f}"},
    {"key": "political_direction_bias", "title": "Political\nDirection Bias",
     "desc": "Asymmetry in flagging\nleft vs. right-leaning bias.\n1 = symmetric, 10 = one-sided.",
     "vmin": 0, "vmax": 10, "fmt": "{:.2f}"},
]

# ── Figure ──
n_panels = len(PANELS)
panel_w = 2.8
label_w = 1.6
fig_w = label_w + panel_w * n_panels + 0.6
fig_h = 5.5

fig, axes = plt.subplots(1, n_panels, figsize=(fig_w, fig_h),
                         gridspec_kw={"left": label_w / fig_w,
                                      "right": 1 - 0.15 / fig_w,
                                      "top": 0.48, "bottom": 0.08,
                                      "wspace": 0.4})
fig.patch.set_facecolor(BG_COLOR)

# Outer rounded border
outer = mpatches.FancyBboxPatch(
    (0.02, 0.03), 0.96, 0.94,
    boxstyle="round,pad=0,rounding_size=0.015",
    facecolor="none", edgecolor=BORDER_COLOR, linewidth=1.5,
    transform=fig.transFigure, clip_on=False,
)
fig.patches.append(outer)

# Title
fig.text(0.5, 0.98, "Bias Benchmarks",
         ha="center", va="top", fontsize=20, fontweight="700", color=TEXT_DARK)

y_rows = [0.22, 0.08]  # two model rows — bottom of panel

for col, (ax, panel) in enumerate(zip(axes, PANELS)):
    ax.set_facecolor("none")
    for spine in ax.spines.values():
        spine.set_visible(False)

    key = panel["key"]
    vmin, vmax = panel["vmin"], panel["vmax"]

    # Faint vertical grid
    for gx in [0, 0.25, 0.5, 0.75, 1.0]:
        ax.axvline(gx, color=GRID_COLOR, linewidth=0.5, zorder=0)

    for i, (mk, label, color, light) in enumerate(MODELS):
        y = y_rows[i]
        v_opus = DATA["opus"][mk][key]
        v_gpt5 = DATA["gpt5"][mk][key]
        mean = (v_opus + v_gpt5) / 2

        # Normalize to 0–1
        def norm(v):
            return (v - vmin) / (vmax - vmin)

        n_opus = norm(v_opus)
        n_gpt5 = norm(v_gpt5)
        n_mean = norm(mean)
        n_lo = min(n_opus, n_gpt5)
        n_hi = max(n_opus, n_gpt5)

        # Range bar — thick, light color
        ax.plot([n_lo, n_hi], [y, y], color=light, linewidth=7,
                solid_capstyle="round", zorder=2)

        # Mean dot
        ax.scatter(n_mean, y, color=color, s=55, zorder=5,
                   edgecolors="white", linewidths=0.8)

        # Judge dots (smaller)
        if abs(n_opus - n_gpt5) > 0.02:
            ax.scatter([n_opus, n_gpt5], [y, y], color=color, s=22,
                       zorder=4, alpha=0.55, edgecolors="white", linewidths=0.5)

        # Value label
        val_str = panel["fmt"].format(mean)
        ax.text(n_hi + 0.05, y, val_str,
                va="center", ha="left",
                fontsize=9, fontweight="400", color=color)

        # Model name (first panel only)
        if col == 0:
            ax.text(-0.08, y, label, va="center", ha="right",
                    fontsize=10, fontweight="600", color=TEXT_DARK,
                    transform=ax.get_yaxis_transform())

    # Axis
    ax.set_xlim(-0.03, 1.18)
    ax.set_ylim(-0.02, 0.32)
    ax.set_xticks([0, 0.50, 1.00])
    ax.set_xticklabels(["0.00", "0.50", "1.00"], fontsize=7.5, color=TEXT_MID)
    ax.set_yticks([])
    ax.tick_params(axis="x", length=0, pad=5)

    # Panel header — title (above axes in figure coords)
    pos = ax.get_position()
    title_y = pos.y1 + 0.28
    desc_y = pos.y1 + 0.04
    fig.text(pos.x0, title_y, panel["title"],
             fontsize=12, fontweight="700",
             color=TEXT_DARK, va="top", ha="left", linespacing=1.2)
    fig.text(pos.x0, desc_y, panel["desc"],
             fontsize=7.5, color=TEXT_MID,
             va="top", ha="left", linespacing=1.35)

    # Vertical separator between panels
    if col > 0:
        lx = ax.get_position().x0 - 0.008
        fig.add_artist(plt.Line2D(
            [lx, lx], [0.06, 0.95],
            transform=fig.transFigure, color=BORDER_COLOR,
            linewidth=0.8, clip_on=False,
        ))

out_path = pathlib.Path(__file__).resolve().parent / "bias_benchmarks.png"
fig.savefig(out_path, dpi=250, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"\u2713 Saved to {out_path}")
