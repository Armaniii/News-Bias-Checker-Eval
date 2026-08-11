#!/usr/bin/env python3
"""fig_crown.py — crown-jewel figure drafts (A ladder / B primitives / C both).
Nature-minimal style: sans, small, no grid, left+bottom spines, one accent hue.
All v3-only, baseline; article-bootstrap CIs (10k, fixed seed).
Outputs: paper/figures/drafts/crown_{a,b,c}.{pdf,png}
"""
import json, glob, sys, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import Counter
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "analysis"))
from triage_router import load, exp5, V3, L5, rows_for

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5,
                     "axes.linewidth": 0.7, "xtick.major.width": 0.7,
                     "ytick.major.width": 0.7})
BLUE, ORANGE, GRAY, DGRAY = "#2a78d6", "#eb6834", "#c3c2b7", "#6b6a60"
rng = np.random.default_rng(20260811)
OUT = ROOT / "paper" / "figures" / "drafts"; OUT.mkdir(parents=True, exist_ok=True)

# ---------------- shared data ----------------
JUDGES = ("claude-sonnet-4-6", "gpt-5", "qwen3-235b", "deepseek-v32")
d0 = load("baseline")
pred = {t: {a: v[0] for a, v in d0[t].items()} for t in d0}
conf = {t: {a: v[1] for a, v in d0[t].items()} for t in d0}
for j in JUDGES:
    p = {}
    for f in glob.glob(str(ROOT / f"results/article_ratings/{j}/*.json")):
        d = json.load(open(f)); pl = d.get("predicted_lean")
        if pl in L5 and d.get("article_id") in V3: p[d["article_id"]] = L5[pl]
    pred[j] = p
M6 = list(pred)
c6 = sorted(a for a in set.intersection(*[set(pred[m]) for m in M6])
            if exp5(a) is not None)
n6 = len(c6)
BUDGET = 0.387

def strategy_outcomes():
    """per-article final-correctness vectors for each ladder strategy (budget fixed)."""
    T = ("claude-sonnet-4-5", "gpt-4.1")
    out = {}
    arts = [a for a in c6 if a in pred[T[0]] and a in pred[T[1]]]
    e = {a: exp5(a) for a in arts}
    out["Claude alone"] = np.array([pred[T[0]][a] == e[a] for a in arts])
    out["GPT-4.1 alone"] = np.array([pred[T[1]][a] == e[a] for a in arts])
    k = int(round(len(arts) * BUDGET))
    for t, lab in ((T[0], "Claude + confidence"), (T[1], "GPT-4.1 + confidence")):
        order = sorted(arts, key=lambda a: conf[t][a])
        routed = set(order[:k])
        out[lab] = np.array([True if a in routed else pred[t][a] == e[a] for a in arts])
    ag = {a: pred[T[0]][a] == pred[T[1]][a] for a in arts}
    out["protocol, two models"] = np.array(
        [True if not ag[a] else pred[T[0]][a] == e[a] for a in arts])
    cons, pick = {}, {}
    for a in arts:
        votes = [pred[m][a] for m in M6]
        pick[a], cons[a] = Counter(votes).most_common(1)[0]
    # tie-robust: fractional keep within the boundary consensus level, so the
    # mean equals the committed expected value (analysis/phase2_analyses.py G).
    slots = len(arts) - k          # number kept
    vec = {}
    kept = 0
    for lvl in sorted(set(cons.values()), reverse=True):
        grp = [a for a in arts if cons[a] == lvl]
        take = min(len(grp), slots - kept)
        frac = take / len(grp) if grp else 0.0
        for a in grp:
            vec[a] = frac * float(pick[a] == e[a]) + (1 - frac) * 1.0
        kept += take
    out["protocol, six models"] = np.array([vec[a] for a in arts])
    return arts, out

def ci(vec, nb=10_000):
    idx = rng.integers(0, len(vec), size=(nb, len(vec)))
    errs = 1 - vec[idx].mean(axis=1)
    return 1 - vec.mean(), np.percentile(errs, 2.5), np.percentile(errs, 97.5)

def style(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)

# ---------------- deck A: the ladder ----------------
def deck_a(ax):
    arts, out = strategy_outcomes()
    rows = ["Claude alone", "GPT-4.1 alone", "Claude + confidence",
            "GPT-4.1 + confidence", "protocol, two models", "protocol, six models"]
    ys = np.arange(len(rows))[::-1]
    for y, lab in zip(ys, rows):
        m, lo, hi = ci(out[lab])
        col = BLUE if lab.startswith("protocol") else DGRAY
        ax.plot([lo, hi], [y, y], "-", color=col, lw=1.1)
        ax.plot([m], [y], "o", ms=4.5, color=col)
        ax.annotate(f"{m:.0%}", (hi, y), xytext=(5, 0), textcoords="offset points",
                    va="center", fontsize=7, color=col)
    ax.axvline(0.102, ls=":", color=GRAY, lw=0.9)
    ax.set_ylim(-0.5, len(rows) - 0.1)
    ax.annotate("oracle", (0.107, len(rows) - 0.55), fontsize=6.5, color=DGRAY,
                ha="left")
    ax.set_yticks(ys); ax.set_yticklabels(rows)
    ax.set_xlim(0, 0.55); ax.set_xticks([0, .1, .2, .3, .4, .5])
    ax.set_xticklabels(["0", "10", "20", "30", "40", "50%"])
    ax.set_xlabel("wrong labels shown to readers (%)", fontsize=7.5)
    style(ax)

# ---------------- deck B: primitives ----------------
KAPPA = [("opinion as fact", .533, BLUE), ("subj. adjectives", .473, BLUE),
         ("mind reading", .427, GRAY), ("word choice", .382, BLUE),
         ("ad hominem", .357, GRAY), ("sensationalism", .354, GRAY),
         ("slant", .349, GRAY), ("elite vs populist", .286, GRAY),
         ("negativity", .255, GRAY), ("spin", .242, GRAY),
         ("flawed logic", .229, GRAY), ("omitted attribution", .227, ORANGE),
         ("story placement", .196, ORANGE), ("omission", .149, ORANGE),
         ("unsubst. claims", .076, ORANGE)]

def deck_b(axs):
    a1, a2, a3 = axs
    # (i) agreement -> accuracy, 15 pairs
    import itertools
    for m1, m2 in itertools.combinations(M6, 2):
        cm = [a for a in c6 if a in pred[m1] and a in pred[m2]]
        agp = [pred[m1][a] == exp5(a) for a in cm if pred[m1][a] == pred[m2][a]]
        dip = [pred[m1][a] == exp5(a) for a in cm if pred[m1][a] != pred[m2][a]]
        a1.plot([0, 1], [np.mean(dip), np.mean(agp)], "-o", color=BLUE,
                alpha=0.35, lw=0.9, ms=2.5)
    a1.set_xlim(-0.25, 1.25); a1.set_ylim(0, 1)
    a1.set_xticks([0, 1]); a1.set_xticklabels(["disagree", "agree"])
    a1.set_ylabel("lean-label accuracy", fontsize=7.5)
    a1.annotate("15 model pairs,\nfour labs", (0.03, 0.9), fontsize=6.5,
                color=DGRAY, va="top")
    style(a1)
    # (ii) bias-form kappa
    ys = np.arange(len(KAPPA))[::-1]
    for y, (lab, k, col) in zip(ys, KAPPA):
        a2.plot([0, k], [y, y], "-", color=col, lw=1.0, alpha=0.85)
        a2.plot([k], [y], "o", ms=3.2, color=col)
    a2.set_yticks(ys); a2.set_yticklabels([k[0] for k in KAPPA], fontsize=6.3)
    a2.set_xlim(0, 0.62); a2.set_xticks([0, .2, .4, .6])
    a2.set_xlabel("cross-model agreement ($\\kappa$)", fontsize=7.5)
    a2.annotate("word-anchored", (0.60, ys[0]), color=BLUE, fontsize=6.5, ha="right")
    a2.annotate("needs unobserved\nreference", (0.60, ys[-1] + 1.2), color=ORANGE,
                fontsize=6.5, ha="right")
    style(a2)
    # (iii) gate: committee size -> coverage/accuracy
    pts = [(2, 0.62, 0.74), (4, 0.44, 0.87), (6, 0.35, 0.90)]
    for kk, cov, acc in pts:
        a3.plot([cov], [acc], "o", ms=5, color=BLUE)
        a3.annotate(f"{kk} models", (cov, acc), xytext=(6, -2),
                    textcoords="offset points", fontsize=6.5, color=DGRAY)
    a3.plot([p[1] for p in pts], [p[2] for p in pts], "-", color=BLUE, lw=1.0,
            alpha=0.5)
    a3.set_xlim(0.25, 0.75); a3.set_ylim(0.65, 0.97)
    a3.set_xlabel("share auto-cleared", fontsize=7.5)
    a3.set_ylabel("accuracy of cleared set", fontsize=7.5)
    a3.set_xticks([.3, .5, .7]); a3.set_xticklabels(["30%", "50%", "70%"])
    style(a3)

# ---------------- render ----------------
# A
fig, ax = plt.subplots(figsize=(3.6, 2.2))
deck_a(ax); fig.tight_layout()
fig.savefig(OUT / "crown_a.pdf"); fig.savefig(OUT / "crown_a.png", dpi=170)
# B
fig, axs = plt.subplots(1, 3, figsize=(6.8, 2.2),
                        gridspec_kw={"width_ratios": [1, 1.35, 1]})
deck_b(axs); fig.tight_layout()
fig.savefig(OUT / "crown_b.pdf"); fig.savefig(OUT / "crown_b.png", dpi=170)
# C
fig = plt.figure(figsize=(6.8, 4.6))
gs = fig.add_gridspec(2, 3, height_ratios=[1, 1], hspace=0.55, wspace=0.45,
                      width_ratios=[1, 1.35, 1])
axA = fig.add_subplot(gs[0, :])
deck_a(axA)
axs = [fig.add_subplot(gs[1, i]) for i in range(3)]
deck_b(axs)
for ax_, letter in ((axA, "a"), (axs[0], "b"), (axs[1], "c"), (axs[2], "d")):
    ax_.annotate(letter, xy=(0, 1), xycoords="axes fraction", xytext=(-28, 6),
                 textcoords="offset points", fontsize=10, fontweight="bold")
fig.savefig(OUT / "crown_c.pdf", bbox_inches="tight")
fig.savefig(OUT / "crown_c.png", dpi=170, bbox_inches="tight")
print("wrote crown_a/b/c to", OUT)
