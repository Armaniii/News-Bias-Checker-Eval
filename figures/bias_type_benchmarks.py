"""
Bias Type Benchmarks — per-type detection validity.
Horizontal dot plot, sorted by Sonnet validity, with sample sizes.
"""

import json, pathlib
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import numpy as np

# ── Palette ──
BG_COLOR     = "#FAF8F5"
TEXT_DARK    = "#2D2D2D"
TEXT_MID     = "#999999"
GRID_COLOR   = "#E8E4DE"
SONNET_COLOR = "#C55A11"
SONNET_LIGHT = "#F0D5BC"
GPT_COLOR    = "#3B6FA0"
GPT_LIGHT    = "#B8D4EC"

ROOT = pathlib.Path(__file__).resolve().parent.parent
S2 = ROOT / "results" / "verification" / "stage2"
BAD = {"article_24346", "article_42780", "article_51657", "article_37862", "article_28565"}

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
    "Unsubstantiated Claims": "Unsubst. Claims",
    "Unsubstantiated claims": "Unsubst. Claims",
    "Mind Reading": "Mind Reading", "Mind reading": "Mind Reading",
    "Mudslinging/Ad Hominem": "Mudslinging", "Mudslinging": "Mudslinging",
    "Ad Hominem": "Mudslinging",
    "Elite vs. Populist Bias": "Elite/Populist",
    "Elite / Populist Bias": "Elite/Populist",
}

TYPES = [
    "Spin", "Slant", "Word Choice", "Opinion as Fact",
    "Subj. Adj.", "Sensationalism", "Negativity",
    "Omission", "Unsubst. Claims", "Mind Reading",
    "Mudslinging", "Elite/Populist",
]

# ── Collect per-judge, per-type verdicts ──
data = {}
for judge in ["claude-opus-4-6", "gpt-5"]:
    s2_dir = S2 / judge
    for f in sorted(s2_dir.glob("*.json")):
        with open(f) as fh:
            r = json.load(fh)
        if r.get("article_id", "") in BAD:
            continue
        parsed = r.get("parsed_output")
        if not parsed or not isinstance(parsed, dict):
            continue
        for mk, rk in [("sonnet", "sonnet_review"), ("gpt", "gpt_review")]:
            for item in parsed.get(rk, []):
                raw = item.get("biasType", "")
                bt = NORMALIZE.get(raw, raw)
                v = item.get("verdict", "").lower()
                key = (judge, mk, bt)
                if key not in data:
                    data[key] = defaultdict(int)
                data[key][v] += 1


def get_stats(mk, bt):
    results = []
    total_n = 0
    for judge in ["claude-opus-4-6", "gpt-5"]:
        v = data.get((judge, mk, bt), {})
        n = sum(v.values())
        total_n += n
        if n >= 2:
            valid_pct = (v.get("confirmed", 0) + v.get("plausible", 0)) / n * 100
            results.append(valid_pct)
    if not results:
        return None, None, None, 0
    mean = np.mean(results)
    lo = min(results) if len(results) > 1 else mean
    hi = max(results) if len(results) > 1 else mean
    return mean, lo, hi, total_n


# Filter and sort by average validity (descending)
rows = []
for bt in TYPES:
    s_mean, s_lo, s_hi, s_n = get_stats("sonnet", bt)
    g_mean, g_lo, g_hi, g_n = get_stats("gpt", bt)
    if (s_n >= 4) or (g_n >= 4):
        avg = np.nanmean([x for x in [s_mean, g_mean] if x is not None])
        rows.append((bt, s_mean, s_lo, s_hi, s_n, g_mean, g_lo, g_hi, g_n, avg))

rows.sort(key=lambda r: r[9] if not np.isnan(r[9]) else 0, reverse=True)

n_types = len(rows)
row_height = 0.55
fig_h = max(4.5, n_types * row_height + 1.8)

fig, ax = plt.subplots(figsize=(10, fig_h))
fig.patch.set_facecolor(BG_COLOR)
ax.set_facecolor(BG_COLOR)

y_offset = 0.18  # vertical offset between Sonnet and GPT dots on same row

for i, (bt, s_mean, s_lo, s_hi, s_n, g_mean, g_lo, g_hi, g_n, avg) in enumerate(rows):
    y = n_types - 1 - i  # top to bottom

    # Faint horizontal band for readability
    if i % 2 == 0:
        ax.axhspan(y - 0.4, y + 0.4, color="#F0EDE8", zorder=0)

    # ── Sonnet ──
    ys = y + y_offset
    if s_mean is not None:
        # Range whisker
        if abs(s_hi - s_lo) > 0.5:
            ax.plot([s_lo, s_hi], [ys, ys], color=SONNET_LIGHT, linewidth=4,
                    solid_capstyle="round", zorder=2)
        # Mean dot
        ax.scatter(s_mean, ys, color=SONNET_COLOR, s=90, zorder=5,
                   edgecolors="white", linewidths=0.8)
        # Value
        ax.text(s_mean + 1.2, ys, f"{s_mean:.0f}%",
                va="center", ha="left", fontsize=8.5,
                fontweight="600", color=SONNET_COLOR)
    else:
        ax.text(42, ys, "n/a", va="center", ha="left",
                fontsize=8, color=TEXT_MID, style="italic")

    # ── GPT ──
    yg = y - y_offset
    if g_mean is not None:
        if abs(g_hi - g_lo) > 0.5:
            ax.plot([g_lo, g_hi], [yg, yg], color=GPT_LIGHT, linewidth=4,
                    solid_capstyle="round", zorder=2)
        ax.scatter(g_mean, yg, color=GPT_COLOR, s=90, zorder=5,
                   edgecolors="white", linewidths=0.8)
        ax.text(g_mean + 1.2, yg, f"{g_mean:.0f}%",
                va="center", ha="left", fontsize=8.5,
                fontweight="600", color=GPT_COLOR)
    else:
        ax.text(42, yg, "n/a", va="center", ha="left",
                fontsize=8, color=TEXT_MID, style="italic")

    # Sample size annotation (right side)
    s_label = f"n={s_n}" if s_n else ""
    g_label = f"n={g_n}" if g_n else ""
    ax.text(103.5, ys, s_label, va="center", ha="left", fontsize=6.5,
            color=SONNET_COLOR, alpha=0.6)
    ax.text(103.5, yg, g_label, va="center", ha="left", fontsize=6.5,
            color=GPT_COLOR, alpha=0.6)

# Axis config
ax.set_xlim(38, 108)
ax.set_ylim(-0.5, n_types - 0.5)
ax.set_yticks(range(n_types))
ax.set_yticklabels([r[0] for r in reversed(rows)],
                   fontsize=10, fontweight="600", color=TEXT_DARK)

ax.set_xticks([40, 50, 60, 70, 80, 90, 100])
ax.set_xticklabels(["40%", "50%", "60%", "70%", "80%", "90%", "100%"],
                   fontsize=9, color=TEXT_DARK)
ax.tick_params(axis="both", length=0, pad=8)

# Vertical grid
for gx in [40, 50, 60, 70, 80, 90, 100]:
    ax.axvline(gx, color=GRID_COLOR, linewidth=0.6, zorder=0)

# Spines
for spine in ax.spines.values():
    spine.set_visible(False)

# Title
ax.set_title("Detection Validity by Bias Type",
             fontsize=17, fontweight="700", pad=16, color=TEXT_DARK)

# Legend
legend_elements = [
    Line2D([0], [0], marker="o", color=SONNET_LIGHT, markerfacecolor=SONNET_COLOR,
           markersize=9, linewidth=4, label="Claude Sonnet 4.5"),
    Line2D([0], [0], marker="o", color=GPT_LIGHT, markerfacecolor=GPT_COLOR,
           markersize=9, linewidth=4, label="GPT-4.1"),
]
ax.legend(handles=legend_elements, loc="upper center",
          bbox_to_anchor=(0.5, -0.06), ncol=2,
          fontsize=9, frameon=True, facecolor=BG_COLOR,
          edgecolor=GRID_COLOR, borderpad=0.6,
          handlelength=2.5, handletextpad=0.5, columnspacing=1.5)

plt.tight_layout()
out_path = pathlib.Path(__file__).resolve().parent / "bias_type_benchmarks.png"
fig.savefig(out_path, dpi=600, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"\u2713 Saved to {out_path}")
