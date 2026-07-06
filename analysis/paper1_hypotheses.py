"""
paper1_hypotheses.py — the three registered confirmatory tests, frozen pre-data.

Implements PRE_REGISTRATION §6.6.10 as amended (§6.8.8/§6.8.9 demotions;
§6.8.11 H26 primary structure). Family = {H26, H28, H29}, BH-FDR q=.05.

  H26  Directional RD asymmetry (Eval C reasonings, both judges pooled,
       article-level clustering): P(left_sub | Right-lean source) >
       P(right_sub | Left-lean source), one-sided Welch t on per-article
       proportions. Confirmation additionally requires per-judge sign
       consistency (§6.8.11); a significant pooled test with discordant
       per-judge signs is NON-confirmation. no_signal excluded from the
       directional-rate denominator; coverage reported by arm and stratum.
  H28  Equivalence (paired TOST, |Δ| < H28_EQUIV_BOUND detections/article)
       of Eval-A detection counts, reframing vs ablation, paired within
       article x target.
  H29  Stability of Eval-C lean labels across reframing vs ablation:
       Cohen's kappa with bootstrap CI (5000 resamples over articles);
       equivalence claimed iff the lower CI bound >= H29_KAPPA_FLOOR.

Stage-2 scoping: the instrument runners append Stage-1 (pilot) and Stage-2
rows to the same caches/parquets, so every loader here filters to the ids
in articles_v3.csv. Pilot rows never enter these tests.

Usage:
  python3 analysis/paper1_hypotheses.py            # Stage-2 confirmatory run
  python3 analysis/paper1_hypotheses.py --pilot    # mechanics check on pilot
                                                   # data (NOT a hypothesis test)
"""

from __future__ import annotations
import argparse, csv, json, pathlib, sys
import numpy as np
import pandas as pd
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "analysis"))
import paper1_config as cfg
import judge_common as jc
from reliability import _cohens_kappa

DIRS = {"left_substitution", "right_substitution"}
N_BOOT = 5000
SEED = 20260623


def v3_ids() -> set:
    csv.field_size_limit(10_000_000)
    with open(cfg.STAGE2_CORPUS, encoding="utf-8") as f:
        return {r["id"] for r in csv.DictReader(f)}


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (ctr - hw, ctr + hw)


# ---------------------------------------------------------------- H26 ----
def h26(ids: set, pilot=False) -> dict:
    df = pd.read_parquet(cfg.DATA / "directional_rd.parquet")
    df = df[df["article_id"].isin(ids)] if not pilot else \
         df[~df["article_id"].isin(ids) &
            ~df["article_id"].isin(cfg.STAGE1_CONTAMINATED_ARTICLES)]
    ok = df[df["direction"].notna()].copy()
    if ok.empty:
        return {"error": "no RD rows in scope"}

    # coverage diagnostics (registered reporting: by arm and by stratum)
    cov = {}
    for key, g in ok.groupby("condition"):
        cov[f"no_signal_rate[{key}]"] = round((g["direction"] == "no_signal").mean(), 3)
    for key, g in ok.groupby("source_lean3"):
        cov[f"no_signal_rate[{key}]"] = round((g["direction"] == "no_signal").mean(), 3)

    # directional-rate denominator excludes no_signal
    ok = ok[ok["direction"] != "no_signal"]

    def art_props(sub: pd.DataFrame, direction: str) -> pd.Series:
        return sub.groupby("article_id")["direction"] \
                  .apply(lambda s: (s == direction).mean())

    def asym(sub: pd.DataFrame):
        x = art_props(sub[sub["source_lean3"] == "Right"], "left_substitution")
        y = art_props(sub[sub["source_lean3"] == "Left"], "right_substitution")
        if len(x) < 2 or len(y) < 2:
            return None
        t, p2 = stats.ttest_ind(x, y, equal_var=False)
        p1 = p2 / 2 if t > 0 else 1 - p2 / 2       # one-sided, predicted sign
        return {"n_right_articles": int(len(x)), "n_left_articles": int(len(y)),
                "rate_leftsub_on_right": round(float(x.mean()), 4),
                "rate_rightsub_on_left": round(float(y.mean()), 4),
                "asymmetry": round(float(x.mean() - y.mean()), 4),
                "t": round(float(t), 3), "p_one_sided": float(p1)}

    pooled = asym(ok)                                # judges pooled (primary)
    per_judge = {jf: asym(g) for jf, g in ok.groupby("judge_family")}
    signs = [pj["asymmetry"] > 0 for pj in per_judge.values() if pj]
    sign_consistent = len(signs) == 2 and all(signs)

    return {"pooled": pooled, "per_judge": per_judge,
            "sign_consistent": sign_consistent,
            "p": pooled["p_one_sided"] if pooled else float("nan"),
            "coverage": cov}


# ---------------------------------------------------------------- H28 ----
def _rollout_frames(ids, pilot=False):
    """(eval-a detection counts, eval-c lean labels) per article x target x arm."""
    a_rows, c_rows = [], []
    for fam, sink in (("a", a_rows), ("c", c_rows)):
        for d in jc.iter_rollouts(fam, conditions=None, targets=cfg.TARGETS):
            in_v3 = d["article_id"] in ids
            if in_v3 == pilot:
                continue
            out = d.get("parsed_output")
            if fam == "a":
                dets = out.get("detections", out) if isinstance(out, dict) else out
                n = len(dets) if isinstance(dets, list) else np.nan
                sink.append({"article_id": d["article_id"], "target": d["model"],
                             "condition": d["condition"], "n_det": n,
                             "lean3": cfg.LEAN_3.get(d.get("labeled_lean"), "")})
            else:
                lean = out.get("lean") if isinstance(out, dict) else None
                sink.append({"article_id": d["article_id"], "target": d["model"],
                             "condition": d["condition"], "lean": lean})
    return pd.DataFrame(a_rows), pd.DataFrame(c_rows)


def _arms(df: pd.DataFrame, pilot: bool):
    """Registered contrast arms; in --pilot mechanics mode fall back to the
    'full' arm as a stand-in treatment (pilot data predates 'reframing')."""
    treat = cfg.ARM_TREATMENT
    if pilot and treat not in set(df["condition"]):
        print(f"  [pilot mechanics] '{treat}' absent; using 'full' as stand-in")
        treat = "full"
    return treat, cfg.ARM_CONTROL


def h28(a_df: pd.DataFrame, pilot=False) -> dict:
    treat, ctrl = _arms(a_df, pilot)
    sub = a_df[a_df["condition"].isin([treat, ctrl])]
    piv = sub.pivot_table(index=["article_id", "target"], columns="condition",
                          values="n_det", aggfunc="first").dropna()
    if len(piv) < 10 or treat not in piv or ctrl not in piv:
        return {"error": f"insufficient paired cells (n={len(piv)})"}
    d = (piv[treat] - piv[ctrl]).to_numpy(float)
    n, m, se = len(d), d.mean(), d.std(ddof=1) / np.sqrt(len(d))
    b = cfg.H28_EQUIV_BOUND
    t_lo = (m + b) / se          # H0: m <= -b
    t_hi = (b - m) / se          # H0: m >= +b
    p = max(1 - stats.t.cdf(t_lo, n - 1), 1 - stats.t.cdf(t_hi, n - 1))
    return {"n_pairs": n, "mean_diff": round(float(m), 3),
            "ci90": [round(float(m - 1.6449 * se), 3), round(float(m + 1.6449 * se), 3)],
            "bound": b, "p": float(p), "equivalent": bool(p < 0.05)}


# ---------------------------------------------------------------- H29 ----
def h29(c_df: pd.DataFrame, pilot=False) -> dict:
    treat, ctrl = _arms(c_df, pilot)
    sub = c_df[c_df["condition"].isin([treat, ctrl])]
    piv = sub.pivot_table(index=["article_id", "target"], columns="condition",
                          values="lean", aggfunc="first").dropna()
    if len(piv) < 10 or treat not in piv or ctrl not in piv:
        return {"error": f"insufficient paired cells (n={len(piv)})"}
    y1 = piv[treat].tolist()
    y2 = piv[ctrl].tolist()
    k = _cohens_kappa(y1, y2)
    arts = piv.index.get_level_values("article_id").to_numpy()
    uniq = np.unique(arts)
    rng = np.random.default_rng(SEED)
    boots = []
    for _ in range(N_BOOT):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        mask = np.concatenate([np.flatnonzero(arts == a) for a in pick])
        boots.append(_cohens_kappa([y1[i] for i in mask], [y2[i] for i in mask]))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"n_pairs": int(len(piv)), "kappa": round(float(k), 4),
            "ci95": [round(float(lo), 4), round(float(hi), 4)],
            "floor": cfg.H29_KAPPA_FLOOR,
            "equivalent": bool(lo >= cfg.H29_KAPPA_FLOOR)}


# ----------------------------------------------------------- D-JA (3) ----
def d_ja_indicator3(a_df: pd.DataFrame) -> dict:
    """§6.8.10 third intensity indicator: the models' own BASELINE detection
    counts per article, by source-lean stratum (Left vs Right balance)."""
    base = a_df[(a_df["condition"] == "baseline") & a_df["n_det"].notna()]
    if base.empty:
        return {"error": "no baseline eval-a rollouts in scope"}
    per_art = base.groupby(["article_id", "lean3"])["n_det"].mean().reset_index()
    out = {f"mean_dets[{s}]": round(float(g["n_det"].mean()), 3)
           for s, g in per_art.groupby("lean3")}
    L = per_art[per_art["lean3"] == "Left"]["n_det"]
    R = per_art[per_art["lean3"] == "Right"]["n_det"]
    if len(L) > 1 and len(R) > 1:
        t, p = stats.ttest_ind(L, R, equal_var=False)
        sd = np.sqrt((L.var() + R.var()) / 2)
        out.update({"welch_p_L_vs_R": round(float(p), 4),
                    "cohens_d_R_minus_L": round(float((R.mean() - L.mean()) / sd), 3)})
    return out


# ------------------------------------------------------------- family ----
def bh(pvals: dict, q=cfg.BH_Q) -> dict:
    """Benjamini-Hochberg over the p-valued tests (H26, H28). H29's registered
    decision rule is its CI bound, reported alongside."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    out, thresh = {}, 0.0
    for i, (name, p) in enumerate(items, 1):
        if p <= q * i / m:
            thresh = q * i / m
    for name, p in items:
        out[name] = {"p": p, "reject": bool(p <= thresh and thresh > 0)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true",
                    help="mechanics check on pilot rows (NOT a hypothesis test)")
    args = ap.parse_args()
    ids = v3_ids()
    scope = "PILOT (mechanics check only)" if args.pilot else "STAGE-2 CONFIRMATORY"
    print(f"paper1_hypotheses | scope: {scope} | family: {sorted(cfg.BH_FAMILY)}")

    r26 = h26(ids, pilot=args.pilot)
    a_df, c_df = _rollout_frames(ids, pilot=args.pilot)
    r28 = h28(a_df, pilot=args.pilot) if len(a_df) else {"error": "no eval-a rollouts in scope"}
    r29 = h29(c_df, pilot=args.pilot) if len(c_df) else {"error": "no eval-c rollouts in scope"}

    pvals = {}
    if "p" in r26 and np.isfinite(r26.get("p", np.nan)):
        pvals["H26"] = r26["p"]
    if "p" in r28:
        pvals["H28"] = r28["p"]
    fam = bh(pvals) if pvals else {}

    report = {"scope": scope, "H26": r26, "H28": r28, "H29": r29, "BH": fam,
              "D_JA_indicator3": d_ja_indicator3(a_df) if len(a_df) else {}}
    if "pooled" in r26 and r26["pooled"]:
        report["H26_confirmed"] = bool(
            fam.get("H26", {}).get("reject") and r26["sign_consistent"])
    out = cfg.DATA / ("hypotheses_pilot_check.json" if args.pilot
                      else "hypotheses_stage2.json")
    out.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report, indent=2, default=str))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
