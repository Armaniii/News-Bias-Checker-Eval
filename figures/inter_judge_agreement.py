"""
Inter-Judge Agreement — clean table-style figure.
Two panels: Per-Eval metrics (top) and Verification metrics (bottom).
"""

import json, pathlib
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Palette ──
BG_COLOR     = "#FAF8F5"
CARD_COLOR   = "#F5F2EE"
TEXT_DARK    = "#2D2D2D"
TEXT_MID     = "#888888"
GRID_COLOR   = "#E0DCD6"
GREEN        = "#C8E6C0"
GREEN_T      = "#2E7D32"
YELLOW       = "#FFE4A0"
YELLOW_T     = "#7B6820"
RED          = "#F5C4C4"
RED_T        = "#8B1A1A"
NEUTRAL      = "#EDEAE6"

ROOT = pathlib.Path(__file__).resolve().parent.parent
BAD = {"article_24346", "article_42780", "article_51657", "article_37862", "article_28565"}

# ── Helpers ──
def pearson_r(x, y):
    if len(x) < 3: return float("nan")
    x, y = np.array(x, dtype=float), np.array(y, dtype=float)
    if np.std(x) == 0 or np.std(y) == 0: return float("nan")
    return float(np.corrcoef(x, y)[0, 1])

def cohens_kappa(pairs):
    if not pairs: return float("nan")
    labels = sorted(set(l for p in pairs for l in p))
    n = len(pairs)
    mx = defaultdict(int)
    for a, b in pairs: mx[(a, b)] += 1
    po = sum(mx[(l, l)] for l in labels) / n
    pe = sum(sum(mx[(l, l2)] for l2 in labels) * sum(mx[(l2, l)] for l2 in labels) for l in labels) / (n * n)
    return (po - pe) / (1 - pe) if pe != 1 else float("nan")

# ══════════════════════════════════════════════════════
# COMPUTE ALL STATS
# ══════════════════════════════════════════════════════
judgment = ROOT / "results" / "judgment"
scores_by = {}
for f in sorted(judgment.rglob("*.json")):
    with open(f) as fh: r = json.load(fh)
    if r.get("condition") != "full": continue
    aid = r.get("article_id", "")
    if aid in BAD: continue
    ev = r.get("eval", "")
    target = r.get("model", "")
    judge = r.get("judgment_model", r.get("judge_model", ""))
    bps = r.get("behavior_presence_score")
    if bps is None: continue
    scores_by[(ev, target, judge, aid)] = {
        "bps": bps, "custom": r.get("custom_scores", {}),
        "additional": r.get("additional_scores", {}),
    }

eval_corr = {}
eval_harshness = {}
eval_favoritism = {}
for ev in ["eval-a", "eval-b", "eval-c"]:
    rs = []
    means = defaultdict(list)
    for target in ["claude-sonnet-4-5", "gpt-4.1"]:
        ox, gx = [], []
        for a in set(a for (e, t, j, a) in scores_by if e == ev and t == target):
            o = scores_by.get((ev, target, "claude-opus-4-6", a), {}).get("bps")
            g = scores_by.get((ev, target, "gpt-5", a), {}).get("bps")
            if o is not None and g is not None:
                ox.append(o); gx.append(g)
                means[("O", target)].append(o); means[("G", target)].append(g)
        if ox: rs.append(pearson_r(ox, gx))
    eval_corr[ev] = np.nanmean(rs)
    o_m = np.mean([v for (j, t), vals in means.items() for v in vals if j == "O"])
    g_m = np.mean([v for (j, t), vals in means.items() for v in vals if j == "G"])
    eval_harshness[ev] = "GPT-5" if g_m > o_m else "Opus"
    same = means.get(("O", "claude-sonnet-4-5"), []) + means.get(("G", "gpt-4.1"), [])
    cross = means.get(("O", "gpt-4.1"), []) + means.get(("G", "claude-sonnet-4-5"), [])
    eval_favoritism[ev] = np.mean(same) - np.mean(cross) if same and cross else float("nan")

# Verification
s2 = ROOT / "results" / "verification" / "stage2"
NORMALIZE = {"Spin": "Spin", "Slant": "Slant", "Word Choice": "Word Choice",
    "Opinion Statements Presented as Fact": "Opinion as Fact", "Opinion as Fact": "Opinion as Fact",
    "Subjective Qualifying Adjectives": "Subj. Adj.", "Subjective Adjectives": "Subj. Adj.",
    "Sensationalism and Emotionalism": "Sensationalism", "Sensationalism": "Sensationalism",
    "Sensationalism/Emotionalism": "Sensationalism", "Bias by Omission": "Omission",
    "Negativity Bias": "Negativity", "Unsubstantiated Claims": "Unsubst.",
    "Unsubstantiated claims": "Unsubst.", "Mind Reading": "Mind Read.", "Mind reading": "Mind Read.",
    "Mudslinging/Ad Hominem": "Mudslinging", "Mudslinging": "Mudslinging", "Ad Hominem": "Mudslinging",
    "Elite vs. Populist Bias": "Elite/Pop.", "Elite / Populist Bias": "Elite/Pop."}
verdicts = defaultdict(dict)
pos_rates = defaultdict(lambda: {"pos": 0, "total": 0})
meta_by = defaultdict(dict)
for jn in ["claude-opus-4-6", "gpt-5"]:
    js = "Opus" if "opus" in jn else "GPT-5"
    for f in sorted((s2 / jn).glob("*.json")):
        with open(f) as fh: r = json.load(fh)
        if r.get("article_id", "") in BAD: continue
        aid = r.get("article_id", "")
        po = r.get("parsed_output")
        if not po or not isinstance(po, dict): continue
        for mk, rk in [("sonnet", "sonnet_review"), ("gpt", "gpt_review")]:
            for item in po.get(rk, []):
                bt = NORMALIZE.get(item.get("biasType", ""), item.get("biasType", ""))
                v = item.get("verdict", "").lower()
                if v:
                    verdicts[(aid, mk, bt)][js] = v
                    pos_rates[js]["total"] += 1
                    if v in ("confirmed", "plausible"): pos_rates[js]["pos"] += 1
        mj = po.get("meta_judgment", {})
        if isinstance(mj, dict):
            for mk in ["sonnet", "gpt"]:
                sub = mj.get(mk, {})
                if isinstance(sub, dict):
                    for dim, val in sub.items():
                        if isinstance(val, (int, float)):
                            meta_by[(aid, mk, dim)][js] = val

m4, mb = [], []
for key, jv in verdicts.items():
    if "Opus" in jv and "GPT-5" in jv:
        m4.append((jv["Opus"], jv["GPT-5"]))
        bo = "valid" if jv["Opus"] in ("confirmed", "plausible") else "invalid"
        bg = "valid" if jv["GPT-5"] in ("confirmed", "plausible") else "invalid"
        mb.append((bo, bg))
kappa_4 = cohens_kappa(m4)
kappa_bin = cohens_kappa(mb)
bin_agree = sum(1 for a, b in mb if a == b) / len(mb) * 100
opus_pos = pos_rates["Opus"]["pos"] / pos_rates["Opus"]["total"] * 100
gpt5_pos = pos_rates["GPT-5"]["pos"] / pos_rates["GPT-5"]["total"] * 100
def mc(dim):
    ox, gx = [], []
    for key, jv in meta_by.items():
        if key[2] != dim: continue
        if "Opus" in jv and "GPT-5" in jv: ox.append(jv["Opus"]); gx.append(jv["GPT-5"])
    return pearson_r(ox, gx)
pdb_r = mc("political_direction_bias")
eq_r = mc("explanation_quality")

# ══════════════════════════════════════════════════════
# FIGURE
# ══════════════════════════════════════════════════════

def color_for(val, metric):
    if isinstance(val, str) or (isinstance(val, float) and np.isnan(val)):
        return NEUTRAL, TEXT_DARK
    if metric == "r":
        if val >= 0.60: return GREEN, GREEN_T
        if val >= 0.35: return YELLOW, YELLOW_T
        return RED, RED_T
    if metric == "k":
        if val >= 0.60: return GREEN, GREEN_T
        if val >= 0.20: return YELLOW, YELLOW_T
        return RED, RED_T
    if metric == "pct":
        if val >= 85: return GREEN, GREEN_T
        if val >= 70: return YELLOW, YELLOW_T
        return RED, RED_T
    if metric == "fav":
        if abs(val) <= 0.25: return GREEN, GREEN_T
        if abs(val) <= 0.55: return YELLOW, YELLOW_T
        return RED, RED_T
    return NEUTRAL, TEXT_DARK

fig = plt.figure(figsize=(11, 8.5))
fig.patch.set_facecolor(BG_COLOR)

# Title
fig.text(0.5, 0.97, "Inter-Judge Agreement",
         ha="center", va="top", fontsize=20, fontweight="700", color=TEXT_DARK)
fig.text(0.5, 0.935, "Claude Opus 4.6 vs GPT-5  |  95 articles  |  full prompt condition",
         ha="center", va="top", fontsize=10, color=TEXT_MID)

# ── PANEL 1: Per-Eval Judgment Scores ──
# Table params
p1_top = 0.88
p1_left = 0.28
col_w = 0.22
row_h = 0.042
header_h = 0.035

cols = ["Eval A\nDetection", "Eval B\nSummarization", "Eval C\nClassification"]

p1_rows = [
    ("BPS Correlation", "r",
     [eval_corr["eval-a"], eval_corr["eval-b"], eval_corr["eval-c"]]),
    ("Harsher Judge", "text",
     [eval_harshness["eval-a"], eval_harshness["eval-b"], eval_harshness["eval-c"]]),
    ("Family Favoritism", "fav",
     [eval_favoritism["eval-a"], eval_favoritism["eval-b"], eval_favoritism["eval-c"]]),
]

# Section label
fig.text(0.04, p1_top + 0.015, "Judgment Scores", fontsize=12, fontweight="700",
         color=TEXT_DARK, va="bottom")
fig.text(0.04, p1_top + 0.005, "Per-evaluation BPS agreement",
         fontsize=8, color=TEXT_MID, va="top")

# Column headers
for j, col in enumerate(cols):
    x = p1_left + j * col_w + col_w / 2
    fig.text(x, p1_top, col, ha="center", va="bottom",
             fontsize=10.5, fontweight="700", color=TEXT_DARK)

for i, (label, metric, vals) in enumerate(p1_rows):
    y = p1_top - header_h - i * row_h - row_h / 2
    fig.text(p1_left - 0.015, y, label, ha="right", va="center",
             fontsize=10.5, fontweight="500", color=TEXT_DARK)
    for j, val in enumerate(vals):
        x = p1_left + j * col_w
        fc, tc = color_for(val, metric)
        text = val if isinstance(val, str) else f"{val:.2f}"
        rect = mpatches.FancyBboxPatch(
            (x + 0.005, y - row_h * 0.42), col_w - 0.01, row_h * 0.84,
            boxstyle="round,pad=0,rounding_size=0.005",
            facecolor=fc, edgecolor=GRID_COLOR, linewidth=0.5,
            transform=fig.transFigure)
        fig.patches.append(rect)
        fig.text(x + col_w / 2, y, text, ha="center", va="center",
                 fontsize=11, fontweight="600", color=tc)

# ── PANEL 2: Verification (Detection Validity) ──
p2_top = p1_top - header_h - len(p1_rows) * row_h - 0.06

fig.text(0.04, p2_top + 0.015, "Verification", fontsize=12, fontweight="700",
         color=TEXT_DARK, va="bottom")
fig.text(0.04, p2_top + 0.005, "Stage 2 detection review (609 matched items)",
         fontsize=8, color=TEXT_MID, va="top")

# Two-column layout for verification
v_left = 0.06
v_col1_w = 0.43
v_col2_left = 0.53
v_col2_w = 0.43
v_row_h = 0.038

v_left_rows = [
    ("Verdict Agreement", [
        ("4-class Cohen's κ", f"{kappa_4:.2f}", "k", kappa_4),
        ("Binary Cohen's κ", f"{kappa_bin:.2f}", "k", kappa_bin),
        ("Binary Raw Agreement", f"{bin_agree:.0f}%", "pct", bin_agree),
    ]),
]
v_right_rows = [
    ("Calibration", [
        ("Positive Rate (Opus)", f"{opus_pos:.0f}%", "none", opus_pos),
        ("Positive Rate (GPT-5)", f"{gpt5_pos:.0f}%", "none", gpt5_pos),
    ]),
    ("Meta-Judgment Corr.", [
        ("Explanation Quality", f"{eq_r:.2f}", "r", eq_r),
        ("Political Dir. Bias", f"{pdb_r:.2f}", "r", pdb_r),
    ]),
]

def draw_verif_group(x_start, width, top_y, title, items):
    # Group title
    fig.text(x_start, top_y, title, fontsize=9.5, fontweight="700",
             color=TEXT_MID, va="bottom")
    for i, (label, text, metric, val) in enumerate(items):
        y = top_y - 0.012 - i * v_row_h - v_row_h / 2
        fig.text(x_start, y, label, ha="left", va="center",
                 fontsize=10, color=TEXT_DARK)
        # Value pill
        pill_w = 0.08
        pill_x = x_start + width - pill_w
        fc, tc = color_for(val, metric)
        rect = mpatches.FancyBboxPatch(
            (pill_x, y - v_row_h * 0.38), pill_w, v_row_h * 0.76,
            boxstyle="round,pad=0,rounding_size=0.005",
            facecolor=fc, edgecolor=GRID_COLOR, linewidth=0.5,
            transform=fig.transFigure)
        fig.patches.append(rect)
        fig.text(pill_x + pill_w / 2, y, text, ha="center", va="center",
                 fontsize=11, fontweight="700", color=tc)
    return top_y - 0.012 - len(items) * v_row_h

# Left column
y_cursor = p2_top - 0.01
for title, items in v_left_rows:
    y_cursor = draw_verif_group(v_left, v_col1_w, y_cursor, title, items)
    y_cursor -= 0.015

# Right column
y_cursor = p2_top - 0.01
for title, items in v_right_rows:
    y_cursor = draw_verif_group(v_col2_left, v_col2_w, y_cursor, title, items)
    y_cursor -= 0.015

# ── PANEL 3: Key Takeaways ──
p3_top = min(p2_top - 0.01 - 3 * v_row_h - 0.04,
             p2_top - 0.01 - 4 * v_row_h - 0.04) - 0.04

fig.text(0.04, p3_top + 0.015, "Key Findings", fontsize=12, fontweight="700",
         color=TEXT_DARK, va="bottom")

takeaways = [
    ("Harshness direction flips between evals", "no stable \"stricter\" judge — averaging is essential"),
    ("Family favoritism strongest in Eval C", "Eval B shows no effect — most credible finding"),
    ("Low 4-class κ is misleading", "judges disagree on confirmed vs plausible, not on validity (88% binary agreement)"),
    ("Political direction bias has no agreement", "r = -0.10 — treat as low-confidence metric"),
]

for i, (bold, detail) in enumerate(takeaways):
    y = p3_top - i * 0.032 - 0.01
    fig.text(0.06, y, f"{i+1}.", fontsize=9, fontweight="700", color=TEXT_MID, va="top")
    fig.text(0.08, y, bold, fontsize=9.5, fontweight="700", color=TEXT_DARK, va="top")
    fig.text(0.08, y - 0.016, detail, fontsize=8.5, color=TEXT_MID, va="top")

# Legend
legend_y = p3_top - len(takeaways) * 0.032 - 0.04
for j, (label, color) in enumerate([("Strong", GREEN), ("Moderate", YELLOW), ("Weak", RED)]):
    x = 0.30 + j * 0.16
    rect = mpatches.FancyBboxPatch(
        (x, legend_y), 0.025, 0.015,
        boxstyle="round,pad=0,rounding_size=0.003",
        facecolor=color, edgecolor=GRID_COLOR, linewidth=0.5,
        transform=fig.transFigure)
    fig.patches.append(rect)
    fig.text(x + 0.03, legend_y + 0.0075, label, fontsize=8.5,
             color=TEXT_DARK, va="center")

out_path = pathlib.Path(__file__).resolve().parent / "inter_judge_agreement.png"
fig.savefig(out_path, dpi=600, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"\u2713 Saved to {out_path}")
