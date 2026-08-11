#!/usr/bin/env python3
"""fig_risk_coverage.py — Paper 2 Figure 1: risk-coverage operating curves.

Curves for the three routing signals (combined, confidence, disagreement) plus
oracle/random reference bounds, baseline condition, v3-only, identical
tie-robust expected-risk treatment as analysis/triage_router.py::aurc.
x = coverage (fraction auto-cleared, most-trusted first); y = error rate among
cleared items. Review budget = 1 - coverage; the practical 20-30% budget band
is shaded. Output: paper/figures/fig_risk_coverage.pdf (+ .png proof).
"""
import sys, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from itertools import groupby
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "analysis"))
from triage_router import rows_for, aurc

rows = rows_for("baseline")
rng = np.random.default_rng(20260803)

def curve(trust):
    rs = sorted(rows, key=trust, reverse=True)
    seq = []
    for _, grp in groupby(rs, key=trust):
        g = list(grp)
        seq.extend([np.mean([not r["correct"] for r in g])] * len(g))
    risk = np.cumsum(seq) / np.arange(1, len(seq) + 1)
    cov = np.arange(1, len(seq) + 1) / len(seq)
    return cov, risk

SIGNALS = [   # (label, trust key, color)
    ("combined",     lambda r: (r["agree"], r["minc"]),  "#2a78d6"),
    ("confidence",   lambda r: (0, r["minc"]),           "#eb6834"),
    ("disagreement", lambda r: (r["agree"], 0),          "#1baf7a"),
]

fig, ax = plt.subplots(figsize=(5.2, 3.3))
ax.axvspan(0.70, 0.80, color="#f2efe4", zorder=0)
ax.text(0.75, 0.455, "20\u201330%\nreview budget", ha="center", va="top",
        fontsize=7.5, color="#6b6a60")

# reference bounds: analytic random (flat at base error) + oracle
base_err = np.mean([not r["correct"] for r in rows])
ax.axhline(base_err, ls="--", color="#9a9a92", lw=1.1)
ax.annotate("random", (0.03, base_err), xytext=(0, 4), textcoords="offset points",
            fontsize=7.5, color="#6b6a60")
covo, risko = curve(lambda r: (r["correct"], 0))
ax.plot(covo, risko, "--", color="#9a9a92", lw=1.1)
ax.annotate("oracle", (0.66, 0.035), fontsize=7.5, color="#6b6a60")

for name, trust, col in SIGNALS:
    cov, risk = curve(trust)
    ax.plot(cov, risk, "-", color=col, lw=2.0, solid_capstyle="round")
a_comb = aurc(rows, SIGNALS[0][1]); a_conf = aurc(rows, SIGNALS[1][1]); a_dis = aurc(rows, SIGNALS[2][1])
ax.annotate(f"disagreement (AURC {a_dis:.2f})", (0.10, 0.262), xytext=(0, 6),
            textcoords="offset points", fontsize=8, color="#128a5e")
ax.annotate(f"confidence ({a_conf:.2f})", (0.56, 0.295), xytext=(0, 12),
            textcoords="offset points", fontsize=8, color="#eb6834", ha="center")
ax.annotate(f"combined ({a_comb:.2f})", (0.60, 0.145), xytext=(0, -14),
            textcoords="offset points", fontsize=8, color="#2a78d6", ha="center")

# protocol operating point: clear the agreement set (61% coverage), route the rest
agree_cov = np.mean([r["agree"] for r in rows])
agree_err = np.mean([not r["correct"] for r in rows if r["agree"]])
ax.plot([agree_cov], [agree_err], "o", ms=7, mfc="white", mec="#2a78d6", mew=1.8, zorder=5)
ax.annotate("protocol operating point\n(clear agreements; route the rest)",
            (agree_cov, agree_err), xytext=(0.33, 0.345), textcoords="data",
            fontsize=7.5, color="#1d5aa8", ha="center",
            arrowprops=dict(arrowstyle="-", color="#1d5aa8", lw=0.8,
                            shrinkB=4))

ax.set_xlim(0, 1.02); ax.set_ylim(0, 0.48)
ax.set_xticks([0, .25, .5, .75, 1.0]); ax.set_xticklabels(["0", "25%", "50%", "75%", "100%"])
ax.set_xlabel("coverage (share of articles auto-cleared, most-trusted first)", fontsize=8.5)
ax.set_ylabel("error rate among cleared articles", fontsize=8.5)
ax.tick_params(labelsize=8)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(axis="y", color="#e4e2d5", lw=0.6, zorder=0)
ax.set_axisbelow(True)
fig.tight_layout()
out = ROOT / "paper" / "figures"; out.mkdir(exist_ok=True)
fig.savefig(out / "fig_risk_coverage.pdf")
fig.savefig(out / "fig_risk_coverage.png", dpi=160)
print("wrote", out / "fig_risk_coverage.pdf")
