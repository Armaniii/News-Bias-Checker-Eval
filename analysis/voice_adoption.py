"""
voice_adoption.py — Stage-1 VAR (Voice Adoption Rate) judge runner.

For each Eval A detection `explanation`, the cross-family judge pair
(Sonnet 4.6 + GPT-5) labels the explanation `describing` vs `inheriting`
(prompts.VAR_JUDGE_PROMPT). VAR = proportion `inheriting` per cell.

Serves H22, H23, H27 (+ H31, D-HCoT-A). Edge case (METHODS §1.5): zero-detection
rollouts contribute no explanations → the cell is simply absent (marked missing,
not VAR=0) — handled naturally since we emit one row per detection.

Usage:
  python3 analysis/voice_adoption.py --dry-run                 # validate pipeline, no API
  python3 analysis/voice_adoption.py --limit 20                # small live test
  python3 analysis/voice_adoption.py                           # full Stage-1 pass
  python3 analysis/voice_adoption.py --stage2                  # use v3 corpus + new arms
"""

from __future__ import annotations
import argparse, json, pathlib, sys
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import paper1_config as cfg
import judge_common as jc
from prompts import VAR_JUDGE_PROMPT

OUT = cfg.DATA / "voice_adoption.parquet"
CACHE = cfg.DATA / "voice_adoption.cache.jsonl"


def build_jobs(corpus_csv, conditions, targets):
    src = jc.load_source_texts(corpus_csv)
    jobs, missing_src = [], 0
    # Empty/whitespace explanations are filtered BEFORE job creation and
    # counted per (condition, target): they are most likely in the reframing
    # arm (H27/H23), so force-labeling or silently nulling them is an MNAR
    # risk in the direction of the load-bearing finding. They are excluded
    # from the VAR denominator and reported per cell (v3.4.0, 2026-06-08).
    empty_excluded = {}
    for d in jc.iter_rollouts("a", conditions=conditions, targets=targets):
        aid = d["article_id"]
        source = src.get(aid)
        if not source:
            missing_src += 1
            continue
        dets = d["parsed_output"]
        # reframing_cot Eval A wraps detections under "detections"
        if isinstance(dets, dict):
            dets = dets.get("detections", [])
        if not isinstance(dets, list):
            continue
        for i, det in enumerate(dets):
            if not isinstance(det, dict):
                continue
            if not (det.get("explanation") or "").strip():
                key = (d["condition"], d["model"])
                empty_excluded[key] = empty_excluded.get(key, 0) + 1
                continue
            user = VAR_JUDGE_PROMPT["user_template"].format(
                source_text=source,
                bias_type=det.get("biasType", ""),
                biased_text=det.get("biasedText", ""),
                explanation=det.get("explanation", ""))
            jobs.append({
                "item_id": f"{aid}__{d['condition']}__{d['model']}__det{i}",
                "system": VAR_JUDGE_PROMPT["system"],
                "user": user,
                "article_id": aid,
                "condition": d["condition"],
                "target": d["model"],
                "source_lean": d.get("labeled_lean", ""),
                "bias_type": det.get("biasType", ""),
                "detection_idx": i,
            })
    if missing_src:
        print(f"  WARN: {missing_src} rollouts had no source text in corpus")
    if empty_excluded:
        print("  empty-explanation detections excluded (condition, target -> n):")
        for k, v in sorted(empty_excluded.items()):
            print(f"    {k}: {v}")
    return jobs


def assemble(records) -> pd.DataFrame:
    rows = []
    for r in records:
        p = r.get("parsed") or {}
        voice = (p.get("voice") or "").strip().lower() if isinstance(p, dict) else ""
        rows.append({
            "item_id": r["item_id"], "article_id": r.get("article_id"),
            "condition": r.get("condition"), "target": r.get("target"),
            "source_lean": r.get("source_lean"),
            "source_lean3": cfg.LEAN_3.get(r.get("source_lean"), ""),
            "bias_type": r.get("bias_type"), "detection_idx": r.get("detection_idx"),
            "judge": r["judge"], "judge_family": r.get("judge_family"),
            # uncodable is a valid judge label (v3.4.0): kept in `voice` for
            # per-cell reporting, excluded from the VAR denominator via
            # inheriting=None.
            "voice": voice if voice in ("describing", "inheriting", "uncodable") else None,
            "inheriting": 1 if voice == "inheriting" else (0 if voice == "describing" else None),
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--stage2", action="store_true", help="use v3 corpus + reframing/reframing_cot arms")
    ap.add_argument("--conditions", nargs="+", default=None)
    args = ap.parse_args()

    corpus = cfg.STAGE2_CORPUS if args.stage2 else cfg.STAGE1_CORPUS
    print(f"VAR runner | corpus={corpus.name} | judges={cfg.JUDGES}")
    jobs = build_jobs(corpus, args.conditions, cfg.TARGETS)
    print(f"  built {len(jobs)} VAR jobs (one per detection)")

    records = jc.run_jobs(jobs, cache_path=CACHE, dry_run=args.dry_run,
                          limit=args.limit, workers=args.workers, max_tokens=200)
    if args.dry_run:
        return
    df = assemble(records)
    df.to_parquet(OUT, index=False)

    ok = df[df["inheriting"].notna()]
    print(f"\n  wrote {OUT} ({len(df)} rows, {df['voice'].isna().sum()} unparsed)")
    if len(ok):
        cell = (ok.groupby(["target", "condition", "source_lean3"])["inheriting"]
                  .mean().round(3))
        print("  VAR (proportion inheriting) by target x condition x lean3:")
        print(cell.to_string())


if __name__ == "__main__":
    main()
