"""
NF-1 extension — direction asymmetry across the 3 Eval A conditions.

The original NF-1 ran on the `full` condition only. This version applies the
political lexicon to detections from baseline, ablation, AND full conditions
to test:

  Q1: Does removing the attribution rule (full → ablation → baseline)
      asymmetrically increase flagging of one political direction over the
      other? (Hypothesis: in partisan articles, quoted opponents are
      inflammatory — without attribution rule, detections expand to include
      those quotes, with article-lean-conditional direction.)

  Q2: Do targets differ in attribution-rule responsiveness?
      (condition × target interaction)

  Q3: Does removing the rule increase total detection count more on one
      side of the political spectrum than the other?
      (condition × target × article_lean three-way)

Reads:  results/rollout/eval-a/{baseline,ablation,full}/{target}/*.json
        results/article_ratings/claude-opus-4-6/*.json   (article lean)
Writes: data/long_condition_asym.parquet
        appended to data/decomp_summary.json (or stats report)
"""

from __future__ import annotations
import json, pathlib, warnings
from collections import defaultdict
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

import sys
sys.path.insert(0, str(ROOT))
from analysis.political_lexicon import classify_text

BAD = {"article_24346", "article_42780", "article_51657",
       "article_37862", "article_28565"}

CONDITIONS = ["baseline", "ablation", "full"]
TARGETS = {"claude-sonnet-4-5": "sonnet", "gpt-4.1": "gpt"}


def _load_opus_article_leans() -> dict:
    out = {}
    d = ROOT / "results" / "article_ratings" / "claude-opus-4-6"
    if not d.exists():
        return out
    for f in sorted(d.glob("*.json")):
        try:
            r = json.load(open(f))
        except Exception:
            continue
        aid = r.get("article_id", "")
        parsed = r.get("parsed_output") or {}
        if isinstance(parsed, dict):
            out[aid] = {
                "lean": parsed.get("lean") or "",
                "rating": parsed.get("rating") if parsed.get("rating") is not None else float("nan"),
            }
    return out


def build_long_detections() -> pd.DataFrame:
    """One row per detection across all conditions × targets."""
    article_leans = _load_opus_article_leans()
    rows = []
    base = ROOT / "results" / "rollout" / "eval-a"
    for cond in CONDITIONS:
        for target_full, target_s in TARGETS.items():
            d = base / cond / target_full
            if not d.exists():
                continue
            for f in sorted(d.glob("*.json")):
                try:
                    r = json.load(open(f))
                except Exception:
                    continue
                aid = r.get("article_id", "")
                if aid in BAD:
                    continue
                # parsed_output is the detection list; varies in format
                parsed = r.get("parsed_output")
                if isinstance(parsed, dict) and "detections" in parsed:
                    detections = parsed.get("detections") or []
                elif isinstance(parsed, list):
                    detections = parsed
                else:
                    detections = []
                article_lean = article_leans.get(aid, {})
                for i, item in enumerate(detections):
                    if not isinstance(item, dict):
                        continue
                    biased_text = item.get("biasedText") or item.get("biased_text") or ""
                    bias_type = item.get("biasType") or item.get("bias_type") or ""
                    cls = classify_text(biased_text)
                    rows.append({
                        "article_id": aid,
                        "target": target_s,
                        "condition": cond,
                        "detection_idx": i,
                        "bias_type": bias_type,
                        "is_left_coded": int(cls["is_left"]),
                        "is_right_coded": int(cls["is_right"]),
                        "flagged_direction": cls["direction"],
                        "article_lean_opus": article_lean.get("lean", ""),
                        "article_rating_opus": article_lean.get("rating", float("nan")),
                    })
    df = pd.DataFrame(rows)
    return df


def fit_condition_models(df: pd.DataFrame) -> dict:
    """
    Two GEE-logit models per outcome (is_left_coded, is_right_coded):
      * outcome ~ C(condition) * C(target) + lean_ordinal
      * outcome ~ C(condition) * lean_ordinal     (per target separately)

    Plus aggregate count comparisons by condition.
    """
    LEAN_ORD = {"Left": -2, "Lean Left": -1, "Center": 0,
                "Lean Right": +1, "Right": +2}

    df = df[df["article_lean_opus"].isin(LEAN_ORD)].copy()
    df["lean_ordinal"] = df["article_lean_opus"].map(LEAN_ORD)
    df["target"] = pd.Categorical(df["target"], categories=["sonnet", "gpt"])
    df["condition"] = pd.Categorical(df["condition"],
                                     categories=["full", "ablation", "baseline"])

    out = {
        "n_detections_total": int(len(df)),
        "by_condition_target": {
            f"{c}__{t}": int(n) for (c, t), n in
            df.groupby(["condition", "target"], observed=False).size().items()
        },
    }

    # Per-condition direction rates by target × article_lean
    desc = (df.groupby(["condition", "target", "article_lean_opus"],
                       observed=False)
              [["is_left_coded", "is_right_coded"]].mean().round(4))
    out["descriptive"] = {
        f"{c}__{t}__{l}": v for (c, t, l), v in desc.to_dict("index").items()
    }

    # Combined model: pooled across targets
    out["models_pooled"] = {}
    for outcome in ["is_left_coded", "is_right_coded"]:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                gee = smf.gee(
                    f"{outcome} ~ C(condition) * C(target) + lean_ordinal",
                    "article_id", data=df, family=sm.families.Binomial(),
                    cov_struct=sm.cov_struct.Exchangeable())
                res = gee.fit()
            params, pvals, bse, ci = res.params, res.pvalues, res.bse, res.conf_int()

            def pull(name):
                if name not in params.index: return None
                return {
                    "log_odds": float(params[name]),
                    "odds_ratio": float(np.exp(params[name])),
                    "se": float(bse[name]),
                    "ci_low_or": float(np.exp(ci.loc[name, 0])),
                    "ci_high_or": float(np.exp(ci.loc[name, 1])),
                    "p": float(pvals[name]),
                }

            out["models_pooled"][outcome] = {
                "status": "ok",
                "n_obs": int(len(df)),
                "intercept": pull("Intercept"),
                "ablation_main": pull("C(condition)[T.ablation]"),
                "baseline_main": pull("C(condition)[T.baseline]"),
                "target_main": pull("C(target)[T.gpt]"),
                "lean_main": pull("lean_ordinal"),
                "ablation_x_target": pull("C(condition)[T.ablation]:C(target)[T.gpt]"),
                "baseline_x_target": pull("C(condition)[T.baseline]:C(target)[T.gpt]"),
                "model": f"{outcome} ~ C(condition) * C(target) + lean_ordinal, GEE logit",
            }
        except Exception as e:
            out["models_pooled"][outcome] = {"status": "fit_failed", "error": str(e)}

    # Per-target models — does condition effect on direction differ by target?
    out["models_per_target"] = {}
    for tgt in ["sonnet", "gpt"]:
        sub = df[df.target == tgt].copy()
        for outcome in ["is_left_coded", "is_right_coded"]:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    gee = smf.gee(
                        f"{outcome} ~ C(condition) + lean_ordinal",
                        "article_id", data=sub,
                        family=sm.families.Binomial(),
                        cov_struct=sm.cov_struct.Exchangeable())
                    res = gee.fit()
                params, pvals, bse, ci = res.params, res.pvalues, res.bse, res.conf_int()

                def pull(name):
                    if name not in params.index: return None
                    return {
                        "log_odds": float(params[name]),
                        "odds_ratio": float(np.exp(params[name])),
                        "ci_low_or": float(np.exp(ci.loc[name, 0])),
                        "ci_high_or": float(np.exp(ci.loc[name, 1])),
                        "p": float(pvals[name]),
                    }

                out["models_per_target"][f"{tgt}__{outcome}"] = {
                    "status": "ok",
                    "n_obs": int(len(sub)),
                    "ablation_main": pull("C(condition)[T.ablation]"),
                    "baseline_main": pull("C(condition)[T.baseline]"),
                    "lean_main": pull("lean_ordinal"),
                }
            except Exception as e:
                out["models_per_target"][f"{tgt}__{outcome}"] = {
                    "status": "fit_failed", "error": str(e)}
    return out


def main():
    print("=== condition_asymmetry.py (NF-1 extension) ===\n")
    df = build_long_detections()
    print(f"Total detections (all 3 conditions × 2 targets): {len(df)}")
    print(f"By condition × target:")
    print(df.groupby(["condition", "target"]).size().unstack(fill_value=0))
    print(f"\nBy direction × condition (overall):")
    print(df.groupby(["condition", "flagged_direction"]).size().unstack(fill_value=0))

    df.to_parquet(DATA / "long_condition_asym.parquet", index=False)
    print(f"\nSaved data/long_condition_asym.parquet")

    fits = fit_condition_models(df)

    print(f"\n=== Pooled models ({fits['n_detections_total']} detections) ===")
    for outcome, m in fits["models_pooled"].items():
        if m.get("status") != "ok":
            print(f"  {outcome}: {m.get('status')}")
            continue
        print(f"\n  {outcome}:")
        for k in ["ablation_main", "baseline_main", "target_main", "lean_main",
                  "ablation_x_target", "baseline_x_target"]:
            eff = m.get(k)
            if eff is None:
                continue
            sig = "**" if eff["p"] < 0.05 else "  "
            print(f"    {sig} {k:>22}: OR={eff['odds_ratio']:.2f} "
                  f"[{eff['ci_low_or']:.2f}, {eff['ci_high_or']:.2f}] "
                  f"(p={eff['p']:.3f})")

    print(f"\n=== Per-target models ===")
    for k, m in fits["models_per_target"].items():
        if m.get("status") != "ok":
            print(f"  {k}: {m.get('status')}")
            continue
        ab = m.get("ablation_main") or {}
        bs = m.get("baseline_main") or {}
        print(f"  {k} (n={m['n_obs']}): "
              f"abl OR={ab.get('odds_ratio',float('nan')):.2f} (p={ab.get('p',1):.3f}), "
              f"base OR={bs.get('odds_ratio',float('nan')):.2f} (p={bs.get('p',1):.3f})")

    out_path = DATA / "condition_asym_summary.json"
    out_path.write_text(json.dumps(fits, indent=2, default=float))
    print(f"\nSaved {out_path}")


if __name__ == "__main__":
    main()
