"""
frame_distance_coding.py — Stage-1 FDC (Frame-Distance Coding) judge runner.

For each Eval C `reasoning` field, the cross-family judge pair (Sonnet 4.6 +
GPT-5) scores two axes on 1-7 (prompts.FDC_JUDGE_PROMPT): attribution discipline
and schema adoption. Higher = more frame distance; lower = more inheritance.

Serves H25, H27b (+ H31, D-HCoT-C). Per METHODS §1.6: key_indicators are
excluded by construction; only the `reasoning` field is scored. Empty/refused
reasoning → cell missing.

Usage: see voice_adoption.py (same flags: --dry-run / --limit / --stage2).
"""

from __future__ import annotations
import argparse, pathlib, sys
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import paper1_config as cfg
import judge_common as jc
from prompts import FDC_JUDGE_PROMPT

OUT = cfg.DATA / "frame_distance_coding.parquet"
CACHE = cfg.DATA / "frame_distance_coding.cache.jsonl"


def build_jobs(corpus_csv, conditions, targets):
    src = jc.load_source_texts(corpus_csv)
    jobs, missing_src, no_reason = [], 0, 0
    for d in jc.iter_rollouts("c", conditions=conditions, targets=targets):
        aid = d["article_id"]
        source = src.get(aid)
        if not source:
            missing_src += 1
            continue
        out = d["parsed_output"]
        if not isinstance(out, dict):
            continue
        reasoning = (out.get("reasoning") or "").strip()
        if not reasoning:
            no_reason += 1
            continue
        user = FDC_JUDGE_PROMPT["user_template"].format(
            source_text=source,
            predicted_lean=out.get("lean", ""),
            reasoning_text=reasoning)
        jobs.append({
            "item_id": f"{aid}__{d['condition']}__{d['model']}",
            "system": FDC_JUDGE_PROMPT["system"],
            "user": user,
            "article_id": aid, "condition": d["condition"], "target": d["model"],
            "source_lean": d.get("labeled_lean", ""),
            "predicted_lean": out.get("lean", ""),
        })
    if missing_src:
        print(f"  WARN: {missing_src} rollouts had no source text")
    if no_reason:
        print(f"  note: {no_reason} rollouts had empty reasoning (cell missing)")
    return jobs


def _axis(p, key):
    if not isinstance(p, dict):
        return None
    v = p.get(key)
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if cfg.FDC_SCALE_MIN <= v <= cfg.FDC_SCALE_MAX else None


def assemble(records) -> pd.DataFrame:
    rows = []
    for r in records:
        p = r.get("parsed")
        rows.append({
            "item_id": r["item_id"], "article_id": r.get("article_id"),
            "condition": r.get("condition"), "target": r.get("target"),
            "source_lean": r.get("source_lean"),
            "source_lean3": cfg.LEAN_3.get(r.get("source_lean"), ""),
            "predicted_lean": r.get("predicted_lean"),
            "judge": r["judge"], "judge_family": r.get("judge_family"),
            "fdc_attribution": _axis(p, "attribution"),
            "fdc_schema": _axis(p, "schema"),
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--stage2", action="store_true")
    ap.add_argument("--conditions", nargs="+", default=None)
    args = ap.parse_args()

    corpus = cfg.STAGE2_CORPUS if args.stage2 else cfg.STAGE1_CORPUS
    print(f"FDC runner | corpus={corpus.name} | judges={cfg.JUDGES} | scale 1-7")
    jobs = build_jobs(corpus, args.conditions, cfg.TARGETS)
    print(f"  built {len(jobs)} FDC jobs (one per Eval C reasoning)")

    records = jc.run_jobs(jobs, cache_path=CACHE, dry_run=args.dry_run,
                          limit=args.limit, workers=args.workers, max_tokens=200)
    if args.dry_run:
        return
    df = assemble(records)
    df.to_parquet(OUT, index=False)

    ok = df[df["fdc_schema"].notna()]
    print(f"\n  wrote {OUT} ({len(df)} rows, {df['fdc_schema'].isna().sum()} unparsed)")
    if len(ok):
        cell = (ok.groupby(["target", "condition", "source_lean3"])[["fdc_attribution", "fdc_schema"]]
                  .mean().round(2))
        print("  FDC (mean axes, 1-7) by target x condition x lean3:")
        print(cell.to_string())


if __name__ == "__main__":
    main()
