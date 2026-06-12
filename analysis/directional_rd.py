"""
directional_rd.py — Stage-1 LLM-judge directional Replacement-Direction runner.

For each Eval C `reasoning` text, the cross-family judge pair labels the
direction of framing substitution vs the source (prompts.DIRECTIONAL_RD_JUDGE_PROMPT):
left_substitution / right_substitution / neutral / no_signal. Higher coverage
than lexicon RD on short text; lexicon RD (analysis/replacement_direction.py)
is the sensitivity instrument.

Serves H26: drift(RIGHT-source) > drift(LEFT-source) — i.e. right-source
articles produce more left_substitution reasoning than left-source produce
right_substitution. `no_signal` rows are reported but excluded from the
directional rate denominator (coverage tracked — see COVERAGE GAP in the review).

Usage: see voice_adoption.py (same flags).
"""

from __future__ import annotations
import argparse, pathlib, sys
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import paper1_config as cfg
import judge_common as jc
from prompts import DIRECTIONAL_RD_JUDGE_PROMPT

OUT = cfg.DATA / "directional_rd.parquet"
CACHE = cfg.DATA / "directional_rd.cache.jsonl"
VALID_DIR = {"left_substitution", "right_substitution", "neutral", "no_signal"}


def build_jobs(corpus_csv, conditions, targets):
    src = jc.load_source_texts(corpus_csv)
    jobs, missing_src = [], 0
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
            continue
        user = DIRECTIONAL_RD_JUDGE_PROMPT["user_template"].format(
            source_text=source, output_type="eval-c reasoning", output_text=reasoning)
        jobs.append({
            "item_id": f"{aid}__{d['condition']}__{d['model']}",
            "system": DIRECTIONAL_RD_JUDGE_PROMPT["system"],
            "user": user,
            "article_id": aid, "condition": d["condition"], "target": d["model"],
            "source_lean": d.get("labeled_lean", ""),
        })
    if missing_src:
        print(f"  WARN: {missing_src} rollouts had no source text")
    return jobs


VALID_MECH = {"strip", "amplify", "both", "na"}


def assemble(records) -> pd.DataFrame:
    rows = []
    for r in records:
        p = r.get("parsed") or {}
        direction = (p.get("direction") or "").strip().lower() if isinstance(p, dict) else ""
        mech = (p.get("mechanism") or "").strip().lower() if isinstance(p, dict) else ""
        rows.append({
            "item_id": r["item_id"], "article_id": r.get("article_id"),
            "condition": r.get("condition"), "target": r.get("target"),
            "source_lean": r.get("source_lean"),
            "source_lean3": cfg.LEAN_3.get(r.get("source_lean"), ""),
            "judge": r["judge"], "judge_family": r.get("judge_family"),
            "direction": direction if direction in VALID_DIR else None,
            # v3.4.0: strip vs amplify split — LEFT_SUBSTITUTION alone
            # conflates strip-right with amplify-left; the C4 directional-
            # default story needs the mechanism to distinguish them.
            "mechanism": mech if mech in VALID_MECH else None,
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--stage2", action="store_true")
    ap.add_argument("--conditions", nargs="+", default=None)
    ap.add_argument("--batch", choices=["submit", "status", "download"], default=None)
    args = ap.parse_args()

    batch_dir = cfg.DATA / "batch_stage1" / "rd"
    if args.batch == "status":
        jc.batch_status(batch_dir); return

    corpus = cfg.STAGE2_CORPUS if args.stage2 else cfg.STAGE1_CORPUS
    print(f"Directional-RD runner | corpus={corpus.name} | judges={cfg.JUDGES}")
    jobs = build_jobs(corpus, args.conditions, cfg.TARGETS)
    print(f"  built {len(jobs)} directional-RD jobs (one per Eval C reasoning)")

    if args.batch == "submit":
        jc.batch_submit(jobs, cache_path=CACHE, batch_dir=batch_dir,
                        dry_run=args.dry_run)
        return
    if args.batch == "download":
        jc.batch_download(batch_dir, CACHE)
        records = list(jc._cache_load(CACHE).values())
    else:
        records = jc.run_jobs(jobs, cache_path=CACHE, dry_run=args.dry_run,
                              limit=args.limit, workers=args.workers,
                              max_tokens=cfg.JUDGE_MAX_TOKENS)
    if args.dry_run and not args.batch:
        return
    df = assemble(records)
    df.to_parquet(OUT, index=False)

    ok = df[df["direction"].notna()]
    cov = (ok["direction"] != "no_signal").mean() if len(ok) else 0
    print(f"\n  wrote {OUT} ({len(df)} rows, {df['direction'].isna().sum()} unparsed)")
    print(f"  directional coverage (non-no_signal): {cov:.1%}  "
          f"[if low, H26 effective N collapses — review COVERAGE GAP]")
    if len(ok):
        dist = pd.crosstab(ok["source_lean3"], ok["direction"])
        print("  direction by source lean3:")
        print(dist.to_string())


if __name__ == "__main__":
    main()
