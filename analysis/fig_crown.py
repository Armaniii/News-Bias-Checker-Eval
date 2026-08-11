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

TRACE_NAMES = {"opinion as fact": "opinion statements presented as fact",
    "subj. adjectives": "subjective qualifying adjectives",
    "mind reading": "mind reading", "word choice": "word choice",
    "ad hominem": "mudslinging/ad hominem",
    "sensationalism": "sensationalism/emotionalism", "slant": "slant",
    "elite vs populist": "elite vs. populist", "negativity": "negativity",
    "spin": "spin", "flawed logic": "flawed logic",
    "omitted attribution": "omission of source attribution",
    "story placement": "bias by story choice and placement",
    "omission": "bias by omission", "unsubst. claims": "unsubstantiated claims"}

def span_traceability():
    """share of flagged spans verbatim-present in the source, per bias type
    (deterministic; eval-A ablation, v3-only)."""
    import re
    srcs = {a: (V3[a].get("text_clean") or V3[a].get("text") or "").lower()
            for a in V3}
    tot, hit = {}, {}
    for fp in glob.glob(str(ROOT / "results/rollout/eval-a/ablation/*/*.json")):
        d = json.load(open(fp)); a = d.get("article_id"); po = d.get("parsed_output")
        if a not in V3 or not isinstance(po, list): continue
        for x in po:
            if not isinstance(x, dict) or not x.get("biasType") or not x.get("biasedText"):
                continue
            ty = re.sub(r"\s+", " ", x["biasType"].strip().lower()).replace(" bias", "")
            bt = re.sub(r"\s+", " ", x["biasedText"].strip().lower())
            if len(bt) < 8: continue
            tot[ty] = tot.get(ty, 0) + 1
            hit[ty] = hit.get(ty, 0) + (bt in srcs[a])
    return {ty: hit[ty] / tot[ty] for ty in tot if tot[ty] >= 40}

def criterion_rho():
    """Spearman: per-article count of type-X flags vs expert |lean_rating|
    (both targets pooled; eval-A ablation, v3-only)."""
    import re
    from scipy import stats as _st
    inten = {a: abs(float(V3[a]["lean_rating"])) for a in V3
             if V3[a].get("lean_rating")}
    cnt = {}
    for fp in glob.glob(str(ROOT / "results/rollout/eval-a/ablation/*/*.json")):
        d = json.load(open(fp)); a = d.get("article_id"); po = d.get("parsed_output")
        if a not in inten or not isinstance(po, list): continue
        for x in po:
            if isinstance(x, dict) and x.get("biasType"):
                ty = re.sub(r"\s+", " ", x["biasType"].strip().lower()).replace(" bias", "")
                cnt.setdefault(ty, {})[a] = cnt.setdefault(ty, {}).get(a, 0) + 1
    arts = sorted(inten)
    out = {}
    for ty, c in cnt.items():
        if sum(c.values()) < 40: continue
        rho, p = _st.spearmanr([inten[a] for a in arts], [c.get(a, 0) for a in arts])
        out[ty] = (rho, p)
    return out

def deck_b(axs):
    a1, a2, a2b, a2c, a3 = axs
    # (i) agreement -> accuracy, 15 pairs
    import itertools
    for m1, m2 in itertools.combinations(M6, 2):
        cm = [a for a in c6 if a in pred[m1] and a in pred[m2]]
        agp = [pred[m1][a] == exp5(a) for a in cm if pred[m1][a] == pred[m2][a]]
        # disagree side: pair-MEAN accuracy (symmetric; mechanically <= 0.5,
        # since at most one member can match the single true label)
        dip = [(int(pred[m1][a] == exp5(a)) + int(pred[m2][a] == exp5(a))) / 2
               for a in cm if pred[m1][a] != pred[m2][a]]
        a1.plot([0, 1], [np.mean(dip), np.mean(agp)], "-o", color=BLUE,
                alpha=0.35, lw=0.9, ms=2.5)
    a1.set_xlim(-0.25, 1.25); a1.set_ylim(0, 1)
    a1.set_xticks([0, 1]); a1.set_xticklabels(["disagree", "agree"])
    a1.set_ylabel("lean-label accuracy", fontsize=7.5)
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
    # (ii-b) aligned deterministic check: flagged span found verbatim in source
    tr = span_traceability()
    for y, (lab, _, col) in zip(ys, KAPPA):
        v = tr.get(TRACE_NAMES[lab])
        if v is None: continue
        a2b.plot([0.55, v], [y, y], "-", color=col, lw=1.0, alpha=0.55)
        a2b.plot([v], [y], "o", ms=3.2, color=col)
    a2b.set_yticks(ys); a2b.set_yticklabels([])
    a2b.set_ylim(a2.get_ylim())
    a2b.set_xlim(0.55, 0.95); a2b.set_xticks([.6, .9])
    a2b.set_xticklabels(["60", "90%"])
    a2b.set_xlabel("span found\nin text", fontsize=7)
    style(a2b)
    # (ii-c) criterion validity: flag count tracks expert-rated intensity
    cr = criterion_rho()
    for y, (lab, _, col) in zip(ys, KAPPA):
        v = cr.get(TRACE_NAMES[lab])
        if v is None: continue
        rho, p = v
        mfc = col if p < .01 else "white"
        a2c.plot([0, rho], [y, y], "-", color=col, lw=1.0, alpha=0.55)
        a2c.plot([rho], [y], "o", ms=3.2, color=col, mfc=mfc, mew=0.9)
    a2c.set_yticks(ys); a2c.set_yticklabels([])
    a2c.set_ylim(a2.get_ylim())
    a2c.set_xlim(0, 0.62); a2c.set_xticks([0, .3, .6])
    a2c.set_xlabel("tracks expert\nrating ($\\rho$)", fontsize=7)
    style(a2c)
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
fig, axs = plt.subplots(1, 5, figsize=(7.4, 2.2),
                        gridspec_kw={"width_ratios": [1, 1.35, 0.5, 0.5, 1]})
deck_b(axs); fig.tight_layout()
fig.savefig(OUT / "crown_b.pdf"); fig.savefig(OUT / "crown_b.png", dpi=170)
# C
fig = plt.figure(figsize=(6.8, 4.6))
gs = fig.add_gridspec(2, 5, height_ratios=[1, 1], hspace=0.55, wspace=0.5,
                      width_ratios=[1, 1.35, 0.5, 0.5, 1])
axA = fig.add_subplot(gs[0, :])
deck_a(axA)
axs = [fig.add_subplot(gs[1, i]) for i in range(5)]
deck_b(axs)
for ax_, letter in ((axA, "a"), (axs[0], "b"), (axs[1], "c"), (axs[4], "d")):
    ax_.annotate(letter, xy=(0, 1), xycoords="axes fraction", xytext=(-28, 6),
                 textcoords="offset points", fontsize=10, fontweight="bold")
fig.savefig(OUT / "crown_c.pdf", bbox_inches="tight")
fig.savefig(OUT / "crown_c.png", dpi=170, bbox_inches="tight")
print("wrote crown_a/b/c to", OUT)
