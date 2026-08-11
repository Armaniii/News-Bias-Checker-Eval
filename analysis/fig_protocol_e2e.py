#!/usr/bin/env python3
"""fig_protocol_e2e.py — Paper 2 Figure 2: end-to-end protocol effectiveness.

Residual overall error after spending the same human-review budget (38.7%,
the protocol's natural workload) under each strategy; the no-triage committee
error is the reference line. Values from data/phase2_analyses.json
(section F of analysis/phase2_analyses.py). Humans assumed correct.
"""
import json, sys, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = pathlib.Path(__file__).resolve().parent.parent
R = json.loads((ROOT / "data" / "phase2_analyses.json").read_text())
P = R["protocol_end_to_end"]

bars = [  # (label, value, color)
    ("single model + confidence\n(if you pick GPT-4.1)",  P["single_model_residual"]["gpt-4.1"], "#c3c2b7"),
    ("Protocol 1\n(committee, model-agnostic)",           P["residual_err"],                      "#2a78d6"),
    ("committee + confidence only\n(no disagreement signal)", P["conf_only_residual"],            "#c3c2b7"),
    ("single model + confidence\n(if you pick the other)", P["single_model_residual"]["claude-sonnet-4-5"], "#c3c2b7"),
]
fig, ax = plt.subplots(figsize=(5.2, 2.7))
y = range(len(bars))[::-1]
for yi, (lab, val, col) in zip(y, bars):
    ax.barh(yi, val, height=0.62, color=col, zorder=3)
    ax.annotate(f"{val:.1%}", (val, yi), xytext=(4, 0), textcoords="offset points",
                va="center", fontsize=8.5, color="#3b3a33")
ax.axvline(P["no_triage_err"], ls="--", color="#9a9a92", lw=1.1)
ax.annotate(f"no triage\n{P['no_triage_err']:.1%}", (P["no_triage_err"], 3.35),
            xytext=(-4, 0), textcoords="offset points", ha="right", va="top",
            fontsize=7.5, color="#6b6a60")
ax.set_yticks(list(y)); ax.set_yticklabels([b[0] for b in bars], fontsize=8)
ax.set_xlim(0, 0.47)
ax.set_xticks([0, .1, .2, .3, .4]); ax.set_xticklabels(["0", "10%", "20%", "30%", "40%"])
ax.set_xlabel(f"overall error after the same {P['workload']:.0%} human-review budget",
              fontsize=8.5)
ax.tick_params(labelsize=8)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(axis="x", color="#e4e2d5", lw=0.6, zorder=0)
ax.set_axisbelow(True)
fig.tight_layout()
out = ROOT / "paper" / "figures"
fig.savefig(out / "fig_protocol_e2e.pdf")
fig.savefig(out / "fig_protocol_e2e.png", dpi=160)
print("wrote", out / "fig_protocol_e2e.pdf")
