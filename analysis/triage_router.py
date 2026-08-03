#!/usr/bin/env python3
"""triage_router.py — canonical, committed reproduction of Paper 2's triage
protocol numbers, computed ONLY on the stated v3 corpus (N=200).

Written after panel review (paper/notes/panel_review_p2.md) found the draft's
S5/Table-2 numbers were computed on a mixed set including ~100 legacy-corpus
rollouts whose prompts contained HEADLINE/SOURCE (label leakage). This script
is the single source of truth for the revision. Conventions (stated per R1-W4):
  - unit of analysis = ARTICLE; bootstrap resamples articles (10k, seed 20260803)
  - committee pick on disagreement = higher-confidence model's label (tie->model A)
  - error = committee pick != expert 5-class label (AllSides outlet-anchored)
Outputs: printed report + data/triage_router_results.json
"""
import json, glob, csv, sys, pathlib
import numpy as np
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "analysis"))
csv.field_size_limit(10**7)
L5 = {"Left": -2, "Lean Left": -1, "Center": 0, "Lean Right": 1, "Right": 2}
SEED, NBOOT = 20260803, 10_000
V3 = {r["id"]: r for r in csv.DictReader(open(ROOT / "articles_v3.csv", encoding="utf-8"))}
def exp5(a): return L5.get(V3.get(a, {}).get("labeled_lean"))
TARGETS = ("claude-sonnet-4-5", "gpt-4.1")
CONDS = ("baseline", "ablation", "reframing", "full", "reframing_cot")


def load(cond):
    d = {t: {} for t in TARGETS}
    for f in glob.glob(str(ROOT / f"results/rollout/eval-c/{cond}/*/*.json")):
        j = json.load(open(f)); m = j.get("model"); po = j.get("parsed_output")
        a = j.get("article_id")
        if m not in d or not isinstance(po, dict) or a not in V3:   # V3-ONLY
            continue
        try: c = float(po.get("confidence"))
        except (TypeError, ValueError): c = None
        if po.get("lean") in L5 and c is not None:
            d[m][a] = (L5[po["lean"]], c)
    return d


def rows_for(cond):
    d = load(cond)
    out = []
    for a in sorted(set(d[TARGETS[0]]) & set(d[TARGETS[1]])):
        e = exp5(a)
        if e is None: continue
        (l1, c1), (l2, c2) = d[TARGETS[0]][a], d[TARGETS[1]][a]
        agree = l1 == l2
        pick = l1 if (agree or c1 >= c2) else l2
        out.append(dict(a=a, agree=agree, minc=min(c1, c2),
                        correct=(pick == e), l1ok=(l1 == e), l2ok=(l2 == e),
                        conf1=c1, l1=l1, l2=l2, e=e, cond=cond))
    return out


def auc(flag_hi_risk, err):
    """AUC of a risk score for predicting an error (ties handled by rank)."""
    from scipy.stats import rankdata
    r = rankdata(flag_hi_risk)
    pos = np.asarray(err, bool)
    n1, n0 = pos.sum(), (~pos).sum()
    return (r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def capture(rows, key, frac):
    """% of committee errors captured routing worst-first by `key`."""
    rs = sorted(rows, key=key, reverse=True)
    k = int(round(len(rs) * frac))
    tot = sum(not r["correct"] for r in rows)
    return sum(not r["correct"] for r in rs[:k]) / tot if tot else float("nan")


def aurc(rows, trust):
    """Tie-robust expected AURC: within a tie-group of the trust score the
    ordering is arbitrary, so we accrue error at the group's mean rate
    (the expectation over within-group orderings) rather than an arbitrary
    realized order. For continuous scores this equals the usual AURC."""
    from itertools import groupby
    rs = sorted(rows, key=trust, reverse=True)      # most trusted first
    seq = []
    for _, grp in groupby(rs, key=trust):
        g = list(grp)
        rate = np.mean([not r["correct"] for r in g])
        seq.extend([rate] * len(g))
    risk = np.cumsum(seq) / np.arange(1, len(seq) + 1)
    return float(np.trapz(risk, np.arange(1, len(seq) + 1) / len(seq)))


def boot_articles(rows, stat, rng):
    arts = sorted({r["a"] for r in rows})
    by = {}
    for r in rows: by.setdefault(r["a"], []).append(r)
    out = []
    for _ in range(NBOOT):
        pick = rng.choice(arts, size=len(arts), replace=True)
        out.append(stat([x for a in pick for x in by[a]]))
    return np.array(out)


def main():
    rng = np.random.default_rng(SEED)
    R = {}
    base = rows_for("baseline")
    n = len(base); nag = sum(r["agree"] for r in base)
    acc_ag = np.mean([r["correct"] for r in base if r["agree"]])
    acc_di = np.mean([r["correct"] for r in base if not r["agree"]])
    print(f"BASELINE v3-only: n={n} articles | agree={nag} ({nag/n:.1%})")
    print(f"  acc|agree={acc_ag:.3f}  acc|disagree(pick=higher-conf)={acc_di:.3f}")
    gap = boot_articles(base, lambda rs: (np.mean([r['correct'] for r in rs if r['agree']] or [np.nan])
                                          - np.mean([r['correct'] for r in rs if not r['agree']] or [np.nan])), rng)
    print(f"  gap={acc_ag-acc_di:.3f}  95% CI [{np.nanpercentile(gap,2.5):.3f},{np.nanpercentile(gap,97.5):.3f}]")
    print("  NOTE structural cap: on a disagreement at most one label can be correct.")
    err = [not r["correct"] for r in base]
    a_dis = auc([0 if r["agree"] else 1 for r in base], err)
    a_cnf = auc([-r["minc"] for r in base], err)
    print(f"  AUC(disagree)={a_dis:.3f}  AUC(min-conf)={a_cnf:.3f}  diff={a_dis-a_cnf:+.3f}")
    print("\n  capture@budget (route worst-first):  disagree | min-conf")
    caps = {}
    for f in (.1, .2, .3, .4, .5):
        cd = capture(base, lambda r: (not r["agree"], -r["minc"]), f)
        cc = capture(base, lambda r: -r["minc"], f)
        caps[f] = (cd, cc)
        d = boot_articles(base, lambda rs: capture(rs, lambda r: (not r["agree"], -r["minc"]), f)
                                          - capture(rs, lambda r: -r["minc"], f), rng)
        p = float(np.mean(d <= 0) * 2)   # two-sided
        print(f"    {f:.0%}: {cd:.3f} | {cc:.3f}  diff={cd-cc:+.3f} p={min(p,1):.3f}")
    au = {k: aurc(base, t) for k, t in [
        ("disagreement", lambda r: (r["agree"], 0)),
        ("confidence", lambda r: (0, r["minc"])),
        ("combined", lambda r: (r["agree"], r["minc"])),
        ("oracle", lambda r: (r["correct"], 0))]}
    au["random"] = aurc(base, lambda r: (rng.random(),))
    print("  AURC:", {k: round(v, 3) for k, v in au.items()})

    # calibration per target (baseline, v3-only)
    print("\nCALIBRATION (v3-only, baseline):")
    calib = {}
    for i, t in enumerate(TARGETS):
        ok = np.array([r["l1ok"] if i == 0 else r["l2ok"] for r in base])
        cf = np.array([r["conf1"] if i == 0 else min(r["minc"], 1) for r in base]) if i == 0 else None
        # reload cleanly for target confidences
    d0 = load("baseline")
    for t in TARGETS:
        pairs = [(v[1], v[0] == exp5(a)) for a, v in d0[t].items() if exp5(a) is not None]
        cfs = np.array([p[0] for p in pairs]); oks = np.array([p[1] for p in pairs])
        bins = np.linspace(0, 1, 11); ece = 0.0
        for lo, hi in zip(bins, bins[1:]):
            m = (cfs > lo) & (cfs <= hi)
            if m.sum(): ece += m.mean() * abs(oks[m].mean() - cfs[m].mean())
        brier = float(np.mean((cfs - oks) ** 2))
        calib[t] = dict(n=len(pairs), acc=float(oks.mean()), conf=float(cfs.mean()),
                        ece=round(float(ece), 4), brier=round(brier, 4))
        print(f"  {t}: {calib[t]}")

    # pooled 5 conditions, article-clustered (power fix)
    pooled = [r for c in CONDS for r in rows_for(c)]
    print(f"\nPOOLED 5 CONDITIONS (article-clustered): rows={len(pooled)}")
    for f in (.2, .3):
        d = boot_articles(pooled, lambda rs: capture(rs, lambda r: (not r["agree"], -r["minc"]), f)
                                            - capture(rs, lambda r: -r["minc"], f), rng)
        est = capture(pooled, lambda r: (not r["agree"], -r["minc"]), f) - capture(pooled, lambda r: -r["minc"], f)
        print(f"  capture diff @{f:.0%}: {est:+.3f}  95% CI [{np.percentile(d,2.5):+.3f},{np.percentile(d,97.5):+.3f}]  p={min(float(np.mean(d<=0)*2),1):.4f}")

    R = dict(seed=SEED, n_baseline=n, agree=nag, acc_agree=round(float(acc_ag), 4),
             acc_disagree=round(float(acc_di), 4), auc_disagree=round(a_dis, 4),
             auc_minconf=round(a_cnf, 4), capture={f"{int(f*100)}": [round(x, 4) for x in v] for f, v in caps.items()},
             aurc={k: round(v, 4) for k, v in au.items()}, calibration=calib)
    (ROOT / "data" / "triage_router_results.json").write_text(json.dumps(R, indent=2))
    print("\nwrote data/triage_router_results.json")


if __name__ == "__main__":
    main()
