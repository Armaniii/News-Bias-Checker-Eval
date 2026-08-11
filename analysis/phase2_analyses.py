#!/usr/bin/env python3
"""phase2_analyses.py — the panel's 'free' analyses for Paper 2 revision
(paper/notes/panel_review_p2.md P1 items 12 / DA-M3 / R1 special charge).
All v3-only. Outputs: printed report + data/phase2_analyses.json.

A. Per-condition router: agree/disagree accuracy + AURC (disagree, conf,
   combined) in each of the 5 prompt conditions (router transfer check).
B. Unanimous-error composition: for the two-vendor 4-model committee and the
   4-lab 6-model committee (baseline), the true-class composition of items
   they clear unanimously BUT get wrong — does the gate auto-clear the
   Lean-Right misreads? (DA-M3 coherence check)
C. Boundary-exclusion check: Lean-Right accuracy on 'core' articles (middle
   50% of the observed Lean-Right continuous-rating range) vs all — is the
   Lean-Right hole a class-boundary artifact? (R1)
"""
import json, glob, csv, sys, pathlib
import numpy as np
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "analysis"))
csv.field_size_limit(10**7)
from triage_router import L5, V3, exp5, TARGETS, CONDS, load, rows_for, aurc

JUDGES = ("claude-sonnet-4-6", "gpt-5", "qwen3-235b", "deepseek-v32")
INV = {v: k for k, v in L5.items()}
R = {}

# ---------- A. per-condition router ----------
print("A. ROUTER PER CONDITION (v3-only)")
R["per_condition"] = {}
for c in CONDS:
    rows = rows_for(c)
    ag = [r["correct"] for r in rows if r["agree"]]
    di = [r["correct"] for r in rows if not r["agree"]]
    a = {"n": len(rows), "agree_acc": round(float(np.mean(ag)), 3),
         "disagree_acc": round(float(np.mean(di)), 3),
         "aurc_disagree": round(aurc(rows, lambda r: (r["agree"], 0)), 3),
         "aurc_conf": round(aurc(rows, lambda r: (0, r["minc"])), 3),
         "aurc_combined": round(aurc(rows, lambda r: (r["agree"], r["minc"])), 3)}
    R["per_condition"][c] = a
    print(f"  {c:14s} n={a['n']} agree={a['agree_acc']} disagree={a['disagree_acc']} "
          f"AURC d/c/comb={a['aurc_disagree']}/{a['aurc_conf']}/{a['aurc_combined']}")

# ---------- B. unanimous-error composition ----------
def lean_committee():
    pred = {}
    d0 = load("baseline")
    for t in TARGETS:
        pred[t] = {a: v[0] for a, v in d0[t].items()}
    for j in JUDGES:
        p = {}
        for f in glob.glob(str(ROOT / f"results/article_ratings/{j}/*.json")):
            d = json.load(open(f)); pl = d.get("predicted_lean")
            if pl in L5 and d.get("article_id") in V3:
                p[d["article_id"]] = L5[pl]
        if p: pred[j] = p
    return pred

pred = lean_committee()
print("\nB. UNANIMOUS-ERROR COMPOSITION (baseline lean)")
R["unanimous_errors"] = {}
for label, models in [("4-model (two-vendor)", list(TARGETS) + list(JUDGES[:2])),
                      ("6-model (four-lab)", list(TARGETS) + list(JUDGES))]:
    common = [a for a in set.intersection(*[set(pred[m]) for m in models])
              if exp5(a) is not None]
    unan = [a for a in common if len({pred[m][a] for m in models}) == 1]
    errs = [a for a in unan if pred[models[0]][a] != exp5(a)]
    comp = {INV[c]: sum(1 for a in errs if exp5(a) == c) for c in range(-2, 3)}
    comp = {k: v for k, v in comp.items() if v}
    R["unanimous_errors"][label] = {
        "n_common": len(common), "n_unanimous": len(unan), "n_errors": len(errs),
        "gate_acc": round(1 - len(errs) / len(unan), 3) if unan else None,
        "error_true_class": comp}
    print(f"  {label}: unanimous {len(unan)}/{len(common)}, errors {len(errs)} "
          f"(acc {R['unanimous_errors'][label]['gate_acc']}), true-class of errors: {comp}")

# ---------- C. boundary-exclusion Lean-Right check ----------
print("\nC. LEAN-RIGHT BOUNDARY CHECK (baseline, per target)")
lr = [(a, float(V3[a]["lean_rating"])) for a in V3
      if V3[a].get("labeled_lean") == "Lean Right" and V3[a].get("lean_rating")]
ratings = sorted(r for _, r in lr)
q1, q3 = np.percentile(ratings, [25, 75])
core = {a for a, r in lr if q1 <= r <= q3}
R["boundary_check"] = {"lr_rating_range": [min(ratings), max(ratings)],
                       "core_band": [round(q1, 2), round(q3, 2)], "n_core": len(core),
                       "n_all": len(lr)}
d0 = load("baseline")
for t in TARGETS:
    allacc = [d0[t][a][0] == 1 for a, _ in lr if a in d0[t]]
    coreacc = [d0[t][a][0] == 1 for a in core if a in d0[t]]
    R["boundary_check"][t] = {"all": round(float(np.mean(allacc)), 3),
                              "core": round(float(np.mean(coreacc)), 3),
                              "n_all": len(allacc), "n_core": len(coreacc)}
    print(f"  {t}: all {np.mean(allacc):.3f} (n={len(allacc)}) vs core-band "
          f"{np.mean(coreacc):.3f} (n={len(coreacc)})  [band {q1:.1f}..{q3:.1f}]")

# ---------- D. target contrast: pole accuracy (paired McNemar) + engagement ----------
print("\nD. TARGET CONTRAST (baseline): pole accuracy + rationale engagement")
from scipy import stats as _st
d0 = load("baseline")
poles = [a for a in set(d0[TARGETS[0]]) & set(d0[TARGETS[1]]) if exp5(a) in (-2, 2)]
s = [d0[TARGETS[0]][a][0] == exp5(a) for a in sorted(poles)]
g = [d0[TARGETS[1]][a][0] == exp5(a) for a in sorted(poles)]
b = sum(1 for x, y in zip(s, g) if x and not y)
c = sum(1 for x, y in zip(s, g) if y and not x)
mc = _st.binomtest(b, b + c).pvalue if b + c else float("nan")
R["pole_contrast"] = {"n": len(poles), "sonnet": round(float(np.mean(s)), 3),
                      "gpt41": round(float(np.mean(g)), 3),
                      "mcnemar_b": b, "mcnemar_c": c, "p_exact": round(float(mc), 4)}
print(f"  poles (|lean|=2, n={len(poles)}): Sonnet {np.mean(s):.3f} vs GPT-4.1 "
      f"{np.mean(g):.3f}; McNemar {b}:{c}, exact p={mc:.4f}")
words = {t: [] for t in TARGETS}
for cnd in CONDS:
    for f in glob.glob(str(ROOT / f"results/rollout/eval-c/{cnd}/*/*.json")):
        j = json.load(open(f)); m = j.get("model"); po = j.get("parsed_output")
        if m in words and isinstance(po, dict) and j.get("article_id") in V3:
            r = po.get("reasoning") or ""
            if r: words[m].append(len(r.split()))
R["rationale_words"] = {t: round(float(np.mean(v)), 1) for t, v in words.items()}
print(f"  rationale words (all conds, v3): "
      + ", ".join(f"{t} {np.mean(v):.0f}" for t, v in words.items()))

# ---------- E. bias-type cross-model kappa, v3-only (Table 1 recompute) ----------
print("\nE. BIAS-TYPE KAPPA v3-only (eval-A ablation, both targets)")
import re as _re
def _norm(s): return _re.sub(r"\s+", " ", s.strip().lower()).replace(" bias", "")
bt = {t: {} for t in TARGETS}
for f in glob.glob(str(ROOT / "results/rollout/eval-a/ablation/*/*.json")):
    j = json.load(open(f)); m = j.get("model"); po = j.get("parsed_output")
    a = j.get("article_id")
    if m not in bt or not isinstance(po, list) or a not in V3: continue
    bt[m][a] = {_norm(x["biasType"]) for x in po
                if isinstance(x, dict) and x.get("biasType")}
sh = sorted(set(bt[TARGETS[0]]) & set(bt[TARGETS[1]]))
def _kap(typ):
    x = [typ in bt[TARGETS[0]][a] for a in sh]
    y = [typ in bt[TARGETS[1]][a] for a in sh]
    po_ = np.mean([i == j for i, j in zip(x, y)])
    px, py = np.mean(x), np.mean(y)
    pe = px * py + (1 - px) * (1 - py)
    return (po_ - pe) / (1 - pe) if pe < 1 else float("nan")
from collections import Counter as _C
allt = _C()
for t in TARGETS:
    for s_ in bt[t].values(): allt.update(s_)
R["biastype_kappa_v3"] = {"n_shared": len(sh)}
for typ, _ in allt.most_common():
    either = sum(1 for a in sh if typ in bt[TARGETS[0]][a] or typ in bt[TARGETS[1]][a])
    if either >= 15:
        R["biastype_kappa_v3"][typ] = round(float(_kap(typ)), 3)
print(f"  n_shared={len(sh)}; " + "; ".join(f"{k} {v}" for k, v in
      sorted(R["biastype_kappa_v3"].items(), key=lambda kv: -kv[1]
             if isinstance(kv[1], float) else 0) if k != "n_shared"))

(ROOT / "data" / "phase2_analyses.json").write_text(json.dumps(R, indent=2))
print("\nwrote data/phase2_analyses.json")
