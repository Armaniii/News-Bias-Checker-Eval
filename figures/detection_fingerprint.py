"""
Detection fingerprint — stacked proportion bars.
Two horizontal bars showing how each model distributes detections across bias types.
"""

import json, pathlib, sys, csv, math
from collections import Counter
csv.field_size_limit(sys.maxsize)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BG_COLOR  = "#FAF8F5"
TEXT_DARK = "#2D2D2D"
TEXT_MID  = "#888888"

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / "rollout" / "eval-a" / "full"

MODELS = [
    ("claude-sonnet-4-5", "Claude Sonnet 4.5"),
    ("gpt-4.1",           "GPT-4.1"),
]

TYPES = [
    "Spin", "Slant", "Word Choice", "Opinion as Fact",
    "Subj. Adj.", "Sensationalism", "Negativity",
    "Omission", "Unsubst.", "Mind Read.",
    "Mudslinging", "Elite/Pop.",
]


# 12 distinct colors — warm-to-cool spectrum
TYPE_COLORS = [
    "#C55A11",  # Spin – orange
    "#E8913A",  # Slant – amber
    "#D4A843",  # Word Choice – gold
    "#8DB051",  # Opinion as Fact – olive
    "#5BA06E",  # Subj. Adj. – sage
    "#3A9188",  # Sensationalism – teal
    "#3585A0",  # Negativity – steel blue
    "#3A6FB5",  # Omission – blue
    "#5656A8",  # Unsubst. – indigo
    "#7B4F9E",  # Mind Read. – purple
    "#9E4580",  # Mudslinging – magenta
    "#B5475A",  # Elite/Pop. – rose
]

NORMALIZE = {
    "Spin": "Spin", "Slant": "Slant", "Word Choice": "Word Choice",
    "Opinion Statements Presented as Fact": "Opinion as Fact",
    "Opinion as Fact": "Opinion as Fact",
    "Subjective Qualifying Adjectives": "Subj. Adj.",
    "Subjective Adjectives": "Subj. Adj.",
    "Sensationalism and Emotionalism": "Sensationalism",
    "Sensationalism": "Sensationalism",
    "Sensationalism/Emotionalism": "Sensationalism",
    "Bias by Omission": "Omission",
    "Negativity Bias": "Negativity",
    "Unsubstantiated Claims": "Unsubst.",
    "Unsubstantiated claims": "Unsubst.",
    "Mind Reading": "Mind Read.", "Mind reading": "Mind Read.",
    "Mudslinging/Ad Hominem": "Mudslinging", "Mudslinging": "Mudslinging",
    "Ad Hominem": "Mudslinging",
    "Elite vs. Populist Bias": "Elite/Pop.",
    "Elite / Populist Bias": "Elite/Pop.",
}


def count_types(model_key):
    mdir = RESULTS / model_key
    counts = Counter()
    total = 0
    for f in sorted(mdir.glob("*.json")):
        with open(f) as fh:
            r = json.load(fh)
        parsed = r.get("parsed_output")
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    raw = item.get("bias_type", item.get("biasType", ""))
                    canonical = NORMALIZE.get(raw)
                    if canonical:
                        counts[canonical] += 1
                        total += 1
    return counts, total


model_data = {}
for mk, label in MODELS:
    counts, total = count_types(mk)
    pcts = [counts[bt] / total * 100 if total else 0 for bt in TYPES]
    model_data[mk] = {"pcts": pcts, "total": total}
    print(f"{label}: {total} instances")

# ── Figure — side-by-side donut charts ──
fig, axes = plt.subplots(1, 3, figsize=(11, 4.2),
                         gridspec_kw={"width_ratios": [1, 0.32, 1]})
fig.patch.set_facecolor(BG_COLOR)

wedge_props = dict(edgecolor=BG_COLOR, linewidth=1.5)
donut_width = 0.38

for idx, (mk, label) in enumerate(MODELS):
    ax = axes[idx * 2]  # axes 0 and 2
    ax.set_facecolor(BG_COLOR)
    pcts = model_data[mk]["pcts"]

    wedges, _ = ax.pie(
        pcts, colors=TYPE_COLORS, startangle=90, counterclock=False,
        wedgeprops={**wedge_props, "width": donut_width},
        radius=1.0,
    )

    # Labels for segments >= 5%
    for i, (pct, wedge) in enumerate(zip(pcts, wedges)):
        if pct < 5:
            continue
        ang = (wedge.theta1 + wedge.theta2) / 2
        r = 1.0 - donut_width / 2
        x = r * np.cos(np.radians(ang))
        y = r * np.sin(np.radians(ang))
        ax.text(x, y, f"{pct:.0f}%",
                ha="center", va="center",
                fontsize=7.5, fontweight="600", color="white", zorder=5)

    ax.set_title(label, fontsize=13, fontweight="700", color=TEXT_DARK, pad=12)

# Center column: legend
ax_leg = axes[1]
ax_leg.set_facecolor(BG_COLOR)
ax_leg.axis("off")
legend_elements = [
    plt.Line2D([0], [0], marker="s", color="none",
               markerfacecolor=c, markersize=7, label=t)
    for t, c in zip(TYPES, TYPE_COLORS)
]
ax_leg.legend(
    handles=legend_elements, loc="center",
    ncol=1, frameon=False, fontsize=8,
    labelspacing=0.9, handletextpad=0.5,
)

plt.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.04, wspace=0.02)
out_path = pathlib.Path(__file__).resolve().parent / "detection_fingerprint.png"
fig.savefig(out_path, dpi=250, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"\n\u2713 Saved to {out_path}")
