"""
Continuous source–summary fidelity correlation (NF-3 follow-on).

Where NF-3 binarized source/summary presence at threshold ≥ 5, this version
keeps both signals continuous:

  source_intensity = count of bias-type detections in the source per the judge
                     (confirmed + plausible across both targets' reviews
                      ∪ false_negatives the judge added for either target)
  summary_intensity = Eval B custom_score for that bias type (1-10)

For each (target, judge, condition), compute Pearson and Spearman correlation
between source_intensity and summary_intensity across all (article × bias_type)
cells. Interpretation:
  ρ ≈ 1   → faithful preservation: more source bias → more summary bias
  ρ ≈ 0   → stripping: summary bias decoupled from source
  ρ < 0   → counter-faithful: model amplifies on clean articles, suppresses
            on biased ones (theoretically possible)

Bonus: regress summary_score on source_count via OLS — slope captures
fidelity-as-amplification: slope > 1 means amplification, slope < 1 stripping.
"""

from __future__ import annotations
import json, pathlib
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BAD = {"article_24346", "article_42780", "article_51657",
       "article_37862", "article_28565"}

JUDGE_SHORT = {"claude-opus-4-6": "opus", "gpt-5": "gpt5"}
TARGET_SHORT = {"claude-sonnet-4-5": "sonnet", "gpt-4.1": "gpt"}

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


def count_source_intensity_per_judge() -> dict:
    """
    Returns {(article_id, judge_short, bias_type): count}.
    Counts confirmed + plausible from either target's review,
    plus false_negatives the judge added for either target.
    """
    out = defaultdict(int)
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
            # Confirmed/plausible reviewed detections
            for review_key in ["sonnet_review", "gpt_review"]:
                for item in (parsed.get(review_key) or []):
                    if not isinstance(item, dict):
                        continue
                    v = (item.get("verdict") or "").strip().lower()
                    if v not in ("confirmed", "plausible"):
                        continue
                    bt_eval_b = BIAS_MAP.get(item.get("biasType", ""))
                    if bt_eval_b:
                        out[(aid, judge_s, bt_eval_b)] += 1
            # False-negatives the judge proposed
            for fn_key in ["sonnet_false_negatives", "gpt_false_negatives"]:
                for item in (parsed.get(fn_key) or []):
                    if not isinstance(item, dict):
                        continue
                    bt_eval_b = BIAS_MAP.get(item.get("biasType", ""))
                    if bt_eval_b:
                        out[(aid, judge_s, bt_eval_b)] += 1
    return dict(out)


def load_summary_scores(conditions=("baseline", "ablation", "full")) -> dict:
    """
    Returns {(article_id, target, judge, condition, bias_type): score 1-10}.
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
                    for bt in BIAS_TYPES_EVAL_B:
                        if bt in cs and isinstance(cs[bt], (int, float)):
                            out[(aid, target_s, judge_s, condition, bt)] = float(cs[bt])
    return out


def build_continuous_fidelity_long() -> pd.DataFrame:
    """One row per (article, target, judge, condition, bias_type)."""
    src = count_source_intensity_per_judge()
    summ = load_summary_scores()
    rows = []
    for (aid, target_s, judge_s, condition, bt), score in summ.items():
        src_intensity = src.get((aid, judge_s, bt), 0)
        rows.append({
            "article_id": aid,
            "target": target_s,
            "judge": judge_s,
            "condition": condition,
            "bias_type": bt,
            "source_intensity": int(src_intensity),
            "summary_intensity": float(score),
            "source_present": int(src_intensity > 0),
        })
    return pd.DataFrame(rows)


def correlations_per_cell(df: pd.DataFrame) -> dict:
    """Per (target, judge, condition) compute Pearson, Spearman, and OLS slope."""
    out = {}
    for (cond, tgt, jdg), sub in df.groupby(["condition", "target", "judge"]):
        x = sub["source_intensity"].astype(float).values
        y = sub["summary_intensity"].astype(float).values
        # Pearson
        try:
            r_p, p_p = stats.pearsonr(x, y)
        except Exception:
            r_p, p_p = float("nan"), float("nan")
        # Spearman (more robust to skew)
        try:
            r_s, p_s = stats.spearmanr(x, y)
        except Exception:
            r_s, p_s = float("nan"), float("nan")
        # OLS slope: how many summary score units per +1 source detection
        try:
            slope, intercept, *_ = stats.linregress(x, y)
        except Exception:
            slope, intercept = float("nan"), float("nan")
        out[f"{cond}__{tgt}__{jdg}"] = {
            "condition": cond, "target": tgt, "judge": jdg,
            "n_obs": int(len(sub)),
            "n_articles": int(sub["article_id"].nunique()),
            "pearson_r": float(r_p), "pearson_p": float(p_p),
            "spearman_r": float(r_s), "spearman_p": float(p_s),
            "ols_slope": float(slope), "ols_intercept": float(intercept),
            "mean_source_intensity": float(x.mean()),
            "mean_summary_intensity": float(y.mean()),
        }
    return out


def correlations_per_bias_type(df: pd.DataFrame) -> dict:
    """Per (condition, target, judge, bias_type) — finer-grained."""
    out = {}
    for (cond, tgt, jdg, bt), sub in df.groupby(
            ["condition", "target", "judge", "bias_type"]):
        if len(sub) < 5:
            continue
        x = sub["source_intensity"].astype(float).values
        y = sub["summary_intensity"].astype(float).values
        try:
            r_p, p_p = stats.pearsonr(x, y)
        except Exception:
            r_p, p_p = float("nan"), float("nan")
        out[f"{cond}__{tgt}__{jdg}__{bt}"] = {
            "condition": cond, "target": tgt, "judge": jdg,
            "bias_type": bt, "n_obs": int(len(sub)),
            "pearson_r": float(r_p), "pearson_p": float(p_p),
            "mean_src": float(x.mean()), "mean_sum": float(y.mean()),
        }
    return out


def main():
    print("=== fidelity_correlation.py ===\n")
    df = build_continuous_fidelity_long()
    print(f"Rows: {len(df):,}, articles: {df.article_id.nunique()}, "
          f"conditions: {sorted(df.condition.unique())}")

    print(f"\nSource intensity distribution: "
          f"mean={df.source_intensity.mean():.2f}, "
          f"max={df.source_intensity.max()}, "
          f"non-zero rate={(df.source_intensity > 0).mean():.1%}")

    cell_corr = correlations_per_cell(df)
    print("\n=== Source × Summary correlation per cell ===")
    print(f"{'condition':>10} | {'target':>7} | {'judge':>5} | "
          f"{'Pearson r':>10} | {'p':>8} | {'Spearman':>8} | {'slope':>7}")
    print("-" * 80)
    for k in sorted(cell_corr):
        r = cell_corr[k]
        print(f"{r['condition']:>10} | {r['target']:>7} | {r['judge']:>5} | "
              f"{r['pearson_r']:>10.3f} | {r['pearson_p']:>8.3g} | "
              f"{r['spearman_r']:>8.3f} | {r['ols_slope']:>7.3f}")

    bt_corr = correlations_per_bias_type(df)

    df.to_parquet(DATA / "long_fidelity.parquet", index=False)
    out_path = DATA / "fidelity_summary.json"
    out_path.write_text(json.dumps({
        "per_cell": cell_corr,
        "per_bias_type": bt_corr,
    }, indent=2, default=float))
    print(f"\nSaved data/long_fidelity.parquet and {out_path.name}")


if __name__ == "__main__":
    main()
