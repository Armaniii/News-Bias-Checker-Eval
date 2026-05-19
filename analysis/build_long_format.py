"""
Phase 1 — Long-format data builder.

Reads existing judgment + verification JSON files and produces three tidy
DataFrames (one row per observation), saved as Parquet for fast reload by
downstream statistical modules. No model calls are made.

Outputs (written to data/):
    long_bps.parquet       — BPS + custom_scores per (article, eval, target, judge)
    long_verdict.parquet   — verdict per (article, target, judge, detection_idx)
    long_meta.parquet      — meta_judgment dimensions per (article, target, judge)
"""

from __future__ import annotations
import json, pathlib, sys
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

EVALS    = ["a", "b", "c"]
TARGETS  = ["claude-sonnet-4-5", "gpt-4.1"]
JUDGES   = ["claude-opus-4-6", "gpt-5"]
TARGET_SHORT = {"claude-sonnet-4-5": "sonnet", "gpt-4.1": "gpt"}
JUDGE_SHORT  = {"claude-opus-4-6": "opus", "gpt-5": "gpt5"}

BAD_ARTICLES = {
    "article_24346", "article_42780", "article_51657",
    "article_37862", "article_28565",
}

NORMALIZE_BIAS = {
    "Spin": "Spin", "Slant": "Slant", "Word Choice": "Word Choice",
    "Opinion Statements Presented as Fact": "Opinion as Fact",
    "Opinion as Fact": "Opinion as Fact",
    "Subjective Qualifying Adjectives": "Subj. Adj.",
    "Subjective Adjectives": "Subj. Adj.",
    "Sensationalism and Emotionalism": "Sensationalism",
    "Sensationalism": "Sensationalism",
    "Sensationalism/Emotionalism": "Sensationalism",
    "Bias by Omission": "Omission",
    "Negativity Bias": "Negativity",
    "Unsubstantiated Claims": "Unsubst. Claims",
    "Unsubstantiated claims": "Unsubst. Claims",
    "Mind Reading": "Mind Reading", "Mind reading": "Mind Reading",
    "Mudslinging/Ad Hominem": "Mudslinging", "Mudslinging": "Mudslinging",
    "Ad Hominem": "Mudslinging",
    "Elite vs. Populist Bias": "Elite/Populist",
    "Elite / Populist Bias": "Elite/Populist",
}

VERDICT_VALID = {"confirmed", "plausible"}
VERDICT_ORDINAL = {"hallucinated": 1, "unsupported": 2, "plausible": 3, "confirmed": 4}


def build_bps_long() -> pd.DataFrame:
    rows = []
    base = ROOT / "results" / "judgment"
    for eval_letter in EVALS:
        for target in TARGETS:
            for judge in JUDGES:
                d = base / f"eval-{eval_letter}" / "full" / target / judge
                if not d.exists():
                    continue
                for f in sorted(d.glob("*.json")):
                    try:
                        r = json.load(open(f))
                    except Exception as e:
                        print(f"WARN: {f}: {e}", file=sys.stderr)
                        continue
                    aid = r.get("article_id", "")
                    if aid in BAD_ARTICLES:
                        continue
                    bps = r.get("behavior_presence_score")
                    if bps is None:
                        continue
                    row = {
                        "article_id": aid,
                        "eval": eval_letter,
                        "condition": r.get("condition", "full"),
                        "target": TARGET_SHORT[target],
                        "judge": JUDGE_SHORT[judge],
                        "target_family": "anthropic" if target.startswith("claude") else "openai",
                        "judge_family":  "anthropic" if judge.startswith("claude")  else "openai",
                        "same_family":   ("anthropic" if target.startswith("claude") else "openai") ==
                                         ("anthropic" if judge.startswith("claude")  else "openai"),
                        "bps": float(bps),
                        "labeled_lean": r.get("labeled_lean", ""),
                    }
                    cs = r.get("custom_scores") or {}
                    for k, v in cs.items():
                        if isinstance(v, (int, float)):
                            row[f"cs_{k}"] = float(v)
                    rows.append(row)
    return pd.DataFrame(rows)


def _load_opus_article_leans() -> dict:
    """Returns {article_id: {'lean': str, 'rating': float}} from Opus ratings."""
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


def build_verdict_long() -> pd.DataFrame:
    from analysis.political_lexicon import classify_text  # local import — optional dependency
    article_leans = _load_opus_article_leans()
    rows = []
    base = ROOT / "results" / "verification" / "stage2"
    for judge in JUDGES:
        d = base / judge
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                r = json.load(open(f))
            except Exception as e:
                print(f"WARN: {f}: {e}", file=sys.stderr)
                continue
            aid = r.get("article_id", "")
            if aid in BAD_ARTICLES:
                continue
            parsed = r.get("parsed_output") or {}
            if not isinstance(parsed, dict):
                continue
            article_lean = article_leans.get(aid, {})
            for review_key, target in [("sonnet_review", "sonnet"), ("gpt_review", "gpt")]:
                items = parsed.get(review_key) or []
                for i, item in enumerate(items):
                    if not isinstance(item, dict):
                        continue
                    verdict = (item.get("verdict") or "").strip().lower()
                    if verdict not in VERDICT_ORDINAL:
                        continue
                    raw_bt = item.get("biasType", "")
                    bt = NORMALIZE_BIAS.get(raw_bt, raw_bt)
                    biased_text = item.get("biasedText", "") or ""
                    cls = classify_text(biased_text)
                    rows.append({
                        "article_id": aid,
                        "judge": JUDGE_SHORT[judge],
                        "target": target,
                        "detection_idx": i,
                        "bias_type": bt,
                        "biased_text": biased_text[:300],  # truncate for parquet size
                        "verdict": verdict,
                        "verdict_valid": int(verdict in VERDICT_VALID),
                        "verdict_ordinal": VERDICT_ORDINAL[verdict],
                        "flagged_direction": cls["direction"],   # left/right/both/neither
                        "is_left_coded":     int(cls["is_left"]),
                        "is_right_coded":    int(cls["is_right"]),
                        "article_lean_opus": article_lean.get("lean", ""),
                        "article_rating_opus": article_lean.get("rating", float("nan")),
                        "target_family": "anthropic" if target == "sonnet" else "openai",
                        "judge_family":  "anthropic" if judge == "claude-opus-4-6" else "openai",
                        "same_family":   ("anthropic" if target == "sonnet" else "openai") ==
                                         ("anthropic" if judge == "claude-opus-4-6" else "openai"),
                    })
    return pd.DataFrame(rows)


def build_meta_long() -> pd.DataFrame:
    rows = []
    base = ROOT / "results" / "verification" / "stage2"
    for judge in JUDGES:
        d = base / judge
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                r = json.load(open(f))
            except Exception as e:
                print(f"WARN: {f}: {e}", file=sys.stderr)
                continue
            aid = r.get("article_id", "")
            if aid in BAD_ARTICLES:
                continue
            parsed = r.get("parsed_output") or {}
            mj = parsed.get("meta_judgment") if isinstance(parsed, dict) else None
            if not isinstance(mj, dict):
                continue
            for target_key, target in [("sonnet", "sonnet"), ("gpt", "gpt")]:
                target_block = mj.get(target_key)
                if not isinstance(target_block, dict):
                    continue
                for dim, score in target_block.items():
                    if not isinstance(score, (int, float)):
                        continue
                    rows.append({
                        "article_id": aid,
                        "judge": JUDGE_SHORT[judge],
                        "target": target,
                        "dimension": dim,
                        "score": float(score),
                        "target_family": "anthropic" if target == "sonnet" else "openai",
                        "judge_family":  "anthropic" if judge == "claude-opus-4-6" else "openai",
                        "same_family":   ("anthropic" if target == "sonnet" else "openai") ==
                                         ("anthropic" if judge == "claude-opus-4-6" else "openai"),
                    })
    return pd.DataFrame(rows)


def build_pr_long() -> pd.DataFrame:
    """
    Per-article precision/recall/F1 at (article × target × judge).

    Definitions (per the verification stage 2 schema):
      TP = detections with verdict in {confirmed, plausible}
      FP = detections with verdict in {unsupported, hallucinated}
      FN = entries in {sonnet,gpt}_false_negatives for that target × judge

    Precision = TP / (TP + FP)            'of what I said, how much was right'
    Recall    = TP / (TP + FN)            'of what was there, how much did I catch'
    F1        = 2 * P * R / (P + R)
    """
    rows = []
    base = ROOT / "results" / "verification" / "stage2"
    for judge in JUDGES:
        d = base / judge
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                r = json.load(open(f))
            except Exception:
                continue
            aid = r.get("article_id", "")
            if aid in BAD_ARTICLES:
                continue
            parsed = r.get("parsed_output") or {}
            if not isinstance(parsed, dict):
                continue
            for review_key, fn_key, target in [
                ("sonnet_review", "sonnet_false_negatives", "sonnet"),
                ("gpt_review",    "gpt_false_negatives",    "gpt"),
            ]:
                items = parsed.get(review_key) or []
                fn_items = parsed.get(fn_key) or []
                tp = fp = 0
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    v = (item.get("verdict") or "").strip().lower()
                    if v in ("confirmed", "plausible"):
                        tp += 1
                    elif v in ("unsupported", "hallucinated"):
                        fp += 1
                fn = len(fn_items)
                detections = tp + fp
                # Define P=NaN if model made zero detections; R=NaN if there was nothing to catch.
                # F1=NaN if either is NaN. Models with TP+FP==0 *and* FN==0 produced no error
                # but also nothing to evaluate; we keep them as NaN to avoid spurious 1.0s.
                p = tp / (tp + fp) if (tp + fp) > 0 else float("nan")
                rr = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
                if (not pd.isna(p)) and (not pd.isna(rr)) and (p + rr) > 0:
                    f1 = 2 * p * rr / (p + rr)
                else:
                    f1 = float("nan")
                rows.append({
                    "article_id": aid,
                    "target": target,
                    "judge": JUDGE_SHORT[judge],
                    "tp": tp, "fp": fp, "fn": fn,
                    "n_detections": detections,
                    "precision": p, "recall": rr, "f1": f1,
                    "target_family": "anthropic" if target == "sonnet" else "openai",
                    "judge_family":  "anthropic" if judge == "claude-opus-4-6" else "openai",
                    "same_family":   ("anthropic" if target == "sonnet" else "openai") ==
                                     ("anthropic" if judge == "claude-opus-4-6" else "openai"),
                })
    return pd.DataFrame(rows)


def build_lean_long() -> pd.DataFrame:
    """
    Eval C lean classification — target's predicted lean joined to each judge's
    article-level rating as ground truth. Long format: one row per
    (article, target, judge_truth) tuple.
    """
    rows = []
    rollout_base = ROOT / "results" / "rollout" / "eval-c" / "full"
    rating_base = ROOT / "results" / "article_ratings"

    target_preds = {}  # (target_short, article_id) -> predicted_lean
    for target in TARGETS:
        d = rollout_base / target
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                r = json.load(open(f))
            except Exception:
                continue
            aid = r.get("article_id", "")
            if aid in BAD_ARTICLES:
                continue
            parsed = r.get("parsed_output") or {}
            pred = parsed.get("lean") if isinstance(parsed, dict) else None
            if pred:
                target_preds[(TARGET_SHORT[target], aid)] = pred

    judge_truths = {}  # (judge_short, article_id) -> judge's lean
    for judge in JUDGES:
        d = rating_base / judge
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                r = json.load(open(f))
            except Exception:
                continue
            aid = r.get("article_id", "")
            if aid in BAD_ARTICLES:
                continue
            parsed = r.get("parsed_output") or {}
            jl = parsed.get("lean") if isinstance(parsed, dict) else None
            if jl:
                judge_truths[(JUDGE_SHORT[judge], aid)] = jl

    for (target_s, aid), pred in target_preds.items():
        for (judge_s, aid2), truth in judge_truths.items():
            if aid != aid2:
                continue
            rows.append({
                "article_id": aid,
                "target": target_s,
                "judge_truth": judge_s,
                "predicted_lean": pred,
                "ground_truth_lean": truth,
                "lean_correct": int(pred == truth),
                "target_family": "anthropic" if target_s == "sonnet" else "openai",
                "judge_family":  "anthropic" if judge_s == "opus"   else "openai",
                "same_family":   ("anthropic" if target_s == "sonnet" else "openai") ==
                                 ("anthropic" if judge_s == "opus"   else "openai"),
            })
    return pd.DataFrame(rows)


def main():
    print("Building df_bps ...")
    df_bps = build_bps_long()
    print(f"  rows: {len(df_bps)}, articles: {df_bps['article_id'].nunique()}")

    print("Building df_verdict ...")
    df_verdict = build_verdict_long()
    print(f"  rows: {len(df_verdict)}, articles: {df_verdict['article_id'].nunique()}")

    print("Building df_meta ...")
    df_meta = build_meta_long()
    print(f"  rows: {len(df_meta)}, articles: {df_meta['article_id'].nunique()}")

    print("Building df_lean ...")
    df_lean = build_lean_long()
    print(f"  rows: {len(df_lean)}, articles: {df_lean['article_id'].nunique()}")

    print("Building df_pr (precision/recall/F1) ...")
    df_pr = build_pr_long()
    print(f"  rows: {len(df_pr)}, articles: {df_pr['article_id'].nunique()}")

    # Sanity checks
    expected_bps = 95 * 3 * 2 * 2  # 1140
    print(f"\nExpected df_bps rows (if 95 articles): {expected_bps}; actual: {len(df_bps)}")

    df_bps.to_parquet(DATA / "long_bps.parquet", index=False)
    df_verdict.to_parquet(DATA / "long_verdict.parquet", index=False)
    df_meta.to_parquet(DATA / "long_meta.parquet", index=False)
    df_lean.to_parquet(DATA / "long_lean.parquet", index=False)
    df_pr.to_parquet(DATA / "long_pr.parquet", index=False)
    print(f"\nWrote 5 Parquet files to {DATA}")
    return df_bps, df_verdict, df_meta, df_lean, df_pr


if __name__ == "__main__":
    main()
