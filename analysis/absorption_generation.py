"""
NF-3 — Absorption vs Generation decomposition for Eval B.

Specified in eval-b-susceptibility/seed.yaml:12-19 but never computed in the
existing pipeline. The decomposition:

  For each (article, target, judge, bias_type):
    source_present  = judge says this bias type exists in the source article
    summary_present = judge scores this bias type ≥ threshold in target's summary

  Cell decomposition:
    absorbed   = source_present AND summary_present     ('parroted source bias')
    generated  = NOT source_present AND summary_present ('introduced new bias')
    resisted   = source_present AND NOT summary_present ('filtered source bias')
    clean      = neither                                 ('nothing to absorb or add')

Source-bias signal per (judge, article):
  Union of (a) all confirmed/plausible detections from either target's review,
  (b) all false_negatives the judge added for either target. These together
  represent the judge's complete view of bias types present in the source.

Summary-bias signal per (judge, target, article, bias_type):
  Eval B custom_scores from results/judgment/eval-b/full/{target}/{judge}/.
  Threshold ≥ 5 (multiple instances per the 1-10 rubric) for primary;
  ≥ 3 (any presence) reported as sensitivity check.

Produces per-target rates:
  absorption_rate = sum(absorbed)  / sum(source_present)
  generation_rate = sum(generated) / sum(summary_present)
  resistance_rate = sum(resisted)  / sum(source_present)

Outputs: data/long_decomp.parquet (one row per article × target × bias_type
× threshold) plus aggregate rates per (target, judge, threshold) attached to
stats_report.json.
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
BAD = {"article_24346", "article_42780", "article_51657",
       "article_37862", "article_28565"}

# Map Eval A biasType strings → Eval B custom_scores keys
BIAS_MAP = {
    "Spin": "spin",
    "Unsubstantiated Claims": "unsubstantiated_claims",
    "Unsubstantiated claims": "unsubstantiated_claims",
    "Opinion Statements Presented as Fact": "opinion_as_fact",
    "Opinion as Fact": "opinion_as_fact",
    "Sensationalism/Emotionalism": "sensationalism",
    "Sensationalism": "sensationalism",
    "Sensationalism and Emotionalism": "sensationalism",
    "Mudslinging/Ad Hominem": "mudslinging",
    "Mudslinging": "mudslinging",
    "Ad Hominem": "mudslinging",
    "Mind Reading": "mind_reading",
    "Mind reading": "mind_reading",
    "Slant": "slant",
    "Bias by Omission": "bias_by_omission",
    "Subjective Qualifying Adjectives": "subjective_adjectives",
    "Subjective Adjectives": "subjective_adjectives",
    "Word Choice": "word_choice",
    "Negativity Bias": "negativity_bias",
    "Elite vs. Populist Bias": "elite_populist_bias",
    "Elite / Populist Bias": "elite_populist_bias",
}

BIAS_TYPES_EVAL_B = ["spin", "unsubstantiated_claims", "opinion_as_fact",
    "sensationalism", "mudslinging", "mind_reading", "slant",
    "bias_by_omission", "subjective_adjectives", "word_choice",
    "negativity_bias", "elite_populist_bias"]

JUDGE_SHORT = {"claude-opus-4-6": "opus", "gpt-5": "gpt5"}
TARGET_SHORT = {"claude-sonnet-4-5": "sonnet", "gpt-4.1": "gpt"}


def load_source_bias_per_judge() -> dict:
    """
    Returns {(article_id, judge_short): set_of_bias_types_present_in_source}.

    Source-bias-presence pools confirmed/plausible detections from either
    target's review with all false_negatives the judge added — the judge's
    complete view of bias in the source article.
    """
    out = defaultdict(set)
    base = ROOT / "results" / "verification" / "stage2"
    for judge_full, judge_s in JUDGE_SHORT.items():
        d = base / judge_full
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
            parsed = r.get("parsed_output") or {}
            if not isinstance(parsed, dict):
                continue
            # confirmed/plausible from either review
            for review_key in ["sonnet_review", "gpt_review"]:
                for item in (parsed.get(review_key) or []):
                    if not isinstance(item, dict):
                        continue
                    v = (item.get("verdict") or "").strip().lower()
                    if v not in ("confirmed", "plausible"):
                        continue
                    bt = item.get("biasType", "")
                    bt_eval_b = BIAS_MAP.get(bt)
                    if bt_eval_b:
                        out[(aid, judge_s)].add(bt_eval_b)
            # false_negatives the judge added for either target
            for fn_key in ["sonnet_false_negatives", "gpt_false_negatives"]:
                for item in (parsed.get(fn_key) or []):
                    if not isinstance(item, dict):
                        continue
                    bt = item.get("biasType", "")
                    bt_eval_b = BIAS_MAP.get(bt)
                    if bt_eval_b:
                        out[(aid, judge_s)].add(bt_eval_b)
    return out


def load_summary_scores(conditions=("full",)) -> dict:
    """
    Returns {(article_id, target, judge, condition): {bias_type: score 1-10}}.
    Reads results/judgment/eval-b/{condition}/{target}/{judge}/.
    """
    out = {}
    base = ROOT / "results" / "judgment" / "eval-b"
    for condition in conditions:
        for target_full, target_s in TARGET_SHORT.items():
            for judge_full, judge_s in JUDGE_SHORT.items():
                d = base / condition / target_full / judge_full
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
                    cs = r.get("custom_scores") or {}
                    if not isinstance(cs, dict):
                        continue
                    keep = {k: float(v) for k, v in cs.items()
                            if k in BIAS_TYPES_EVAL_B and isinstance(v, (int, float))}
                    if keep:
                        out[(aid, target_s, judge_s, condition)] = keep
    return out


def build_decomposition(threshold: int = 5,
                        conditions=("full",)) -> pd.DataFrame:
    """One row per (article, target, judge, condition, bias_type)."""
    src = load_source_bias_per_judge()
    summ = load_summary_scores(conditions=conditions)
    rows = []
    for (aid, target_s, judge_s, condition), scores in summ.items():
        source_set = src.get((aid, judge_s), set())
        for bt in BIAS_TYPES_EVAL_B:
            score = scores.get(bt)
            if score is None:
                continue
            source_present = bt in source_set
            summary_present = score >= threshold
            cell = ("absorbed"  if (source_present and summary_present)
                    else "generated" if (not source_present and summary_present)
                    else "resisted"  if (source_present and not summary_present)
                    else "clean")
            rows.append({
                "article_id": aid,
                "target": target_s,
                "judge": judge_s,
                "condition": condition,
                "bias_type": bt,
                "score_eval_b": float(score),
                "threshold": threshold,
                "source_present": int(source_present),
                "summary_present": int(summary_present),
                "absorbed": int(cell == "absorbed"),
                "generated": int(cell == "generated"),
                "resisted": int(cell == "resisted"),
                "clean": int(cell == "clean"),
                "cell": cell,
            })
    return pd.DataFrame(rows)


def aggregate_rates(df: pd.DataFrame) -> dict:
    """Per (condition, target, judge, threshold) summary rates."""
    out = {}
    for (cond, tgt, jdg, thr), sub in df.groupby(
            ["condition", "target", "judge", "threshold"]):
        absorbed = int(sub["absorbed"].sum())
        generated = int(sub["generated"].sum())
        resisted = int(sub["resisted"].sum())
        clean = int(sub["clean"].sum())
        source_present = int(sub["source_present"].sum())
        summary_present = int(sub["summary_present"].sum())
        key = f"{cond}__{tgt}__{jdg}__t{thr}"
        out[key] = {
            "condition": cond, "target": tgt, "judge": jdg, "threshold": thr,
            "n_cells": int(len(sub)),
            "n_articles": int(sub["article_id"].nunique()),
            "absorbed": absorbed, "generated": generated,
            "resisted": resisted, "clean": clean,
            "source_present_total": source_present,
            "summary_present_total": summary_present,
            "absorption_rate": absorbed / source_present if source_present else 0.0,
            "generation_rate": generated / summary_present if summary_present else 0.0,
            "resistance_rate": resisted / source_present if source_present else 0.0,
        }
    return out


def fit_decomposition_lmms(df: pd.DataFrame, with_condition: bool = False) -> dict:
    """
    GEE-logit models per outcome.
    If with_condition=True, includes condition as a fixed effect with target.
    """
    df = df.copy()
    df["target"] = pd.Categorical(df["target"], categories=["sonnet", "gpt"])
    df["judge"]  = pd.Categorical(df["judge"],  categories=["opus", "gpt5"])
    if with_condition:
        df["condition"] = pd.Categorical(
            df["condition"], categories=["full", "ablation", "baseline"])
        formula = "{dv} ~ C(condition) * C(target) + C(judge)"
    else:
        formula = "{dv} ~ C(target) * C(judge)"

    out = {}
    for outcome_label, sub_df, dv in [
        ("absorbed_given_source", df[df.source_present == 1], "summary_present"),
        ("generated_given_no_source", df[df.source_present == 0], "summary_present"),
    ]:
        if len(sub_df) < 20:
            out[outcome_label] = {"status": "insufficient", "n": len(sub_df)}
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                gee = smf.gee(formula.format(dv=dv), "article_id",
                              data=sub_df, family=sm.families.Binomial(),
                              cov_struct=sm.cov_struct.Exchangeable())
                res = gee.fit()
        except Exception as e:
            out[outcome_label] = {"status": "fit_failed", "error": str(e)}
            continue
        params, pvals, bse, ci = res.params, res.pvalues, res.bse, res.conf_int()

        def pull(name):
            if name not in params.index:
                return None
            return {
                "log_odds": float(params[name]),
                "odds_ratio": float(np.exp(params[name])),
                "se": float(bse[name]),
                "ci_low_or": float(np.exp(ci.loc[name, 0])),
                "ci_high_or": float(np.exp(ci.loc[name, 1])),
                "p": float(pvals[name]),
            }

        result = {
            "status": "ok",
            "n_obs": int(len(sub_df)),
            "n_articles": int(sub_df["article_id"].nunique()),
            "model": formula.format(dv=dv) + ", GEE logit + exchangeable on article_id",
            "target_main": pull("C(target)[T.gpt]"),
            "judge_main":  pull("C(judge)[T.gpt5]"),
        }
        if with_condition:
            result["ablation_main"] = pull("C(condition)[T.ablation]")
            result["baseline_main"] = pull("C(condition)[T.baseline]")
            result["ablation_x_target"] = pull("C(condition)[T.ablation]:C(target)[T.gpt]")
            result["baseline_x_target"] = pull("C(condition)[T.baseline]:C(target)[T.gpt]")
        else:
            result["interaction"] = pull("C(target)[T.gpt]:C(judge)[T.gpt5]")
        out[outcome_label] = result
    return out


def main():
    print("=== absorption_generation.py (NF-3 + 3-arm extension) ===\n")
    CONDITIONS = ("baseline", "ablation", "full")

    results = {"thresholds": {}}
    for thr in (5, 3):
        df = build_decomposition(threshold=thr, conditions=CONDITIONS)
        print(f"\n=== threshold ≥ {thr} ===")
        print(f"Rows: {len(df)}, articles: {df['article_id'].nunique()}, "
              f"conditions: {sorted(df.condition.unique())}")
        rates = aggregate_rates(df)
        print(f"\nPer-cell rates (threshold {thr}):")
        # Pretty-print: for each (target, judge), show baseline → ablation → full
        for tgt in ("sonnet", "gpt"):
            for jdg in ("opus", "gpt5"):
                print(f"\n  --- {tgt} × {jdg} ---")
                for cond in CONDITIONS:
                    k = f"{cond}__{tgt}__{jdg}__t{thr}"
                    v = rates.get(k)
                    if not v: continue
                    print(f"    {cond:>9}: absorbed={v['absorbed']:>4}  "
                          f"generated={v['generated']:>4}  resisted={v['resisted']:>4}  "
                          f"| abs_rate={v['absorption_rate']:.2%}  "
                          f"gen_rate={v['generation_rate']:.2%}")

        # Single-condition LMMs (per condition)
        per_cond_models = {}
        for cond in CONDITIONS:
            sub = df[df.condition == cond]
            if len(sub) > 0:
                per_cond_models[cond] = fit_decomposition_lmms(sub, with_condition=False)

        # Combined LMM with condition × target
        combined = fit_decomposition_lmms(df, with_condition=True)
        print(f"\n  Combined LMM (condition × target + judge):")
        for outcome, m in combined.items():
            if m.get("status") != "ok": continue
            for k in ["target_main", "judge_main", "ablation_main", "baseline_main",
                      "ablation_x_target", "baseline_x_target"]:
                eff = m.get(k)
                if eff is None: continue
                sig = "**" if eff["p"] < 0.05 else "  "
                print(f"    {sig} {outcome}/{k:>20}: OR={eff['odds_ratio']:.2f} "
                      f"[{eff['ci_low_or']:.2f}, {eff['ci_high_or']:.2f}] "
                      f"(p={eff['p']:.3f})")

        results["thresholds"][f"t{thr}"] = {
            "rates": rates,
            "per_condition_lmms": per_cond_models,
            "combined_lmm": combined,
        }
        if thr == 5:
            df.to_parquet(DATA / "long_decomp.parquet", index=False)
            print(f"\nSaved data/long_decomp.parquet (3-arm, threshold={thr})")

    out_path = DATA / "decomp_summary.json"
    out_path.write_text(json.dumps(results, indent=2, default=float))
    print(f"\nSaved {out_path}")


if __name__ == "__main__":
    main()
