#!/usr/bin/env python3
"""rate_articles_ext.py — lean classification by the two extended HF judges.

Adds the four-family judge panel's lean labels (Qwen, DeepSeek) using the
SAME prompt files as the pre-registered judges (rate-article-{system,user}.txt,
article-text-only de-leak), so the labels are directly comparable. Writes to
results/article_ratings/{model_key}/{article_id}.json in the identical schema
the committee analysis already reads (fields: article_id, model,
predicted_lean, rating, explanation, parsed_output).

HF Inference Providers is synchronous (no batch API), so this runs concurrently
via call_llm. Requires HF_TOKEN. Resumable (skips existing outputs).

  python3 analysis/rate_articles_ext.py --dry-run          # no API calls
  HF_TOKEN=hf_xxx python3 analysis/rate_articles_ext.py     # run both judges
  HF_TOKEN=hf_xxx python3 analysis/rate_articles_ext.py --judges qwen3-235b
"""
import argparse, csv, json, os, sys, pathlib, threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "analysis"))
csv.field_size_limit(10**7)
import paper1_config as cfg
from run_eval import call_llm, resolve_model, load_model_registry
from rate_articles import classify_rating, _extract_json, load_prompts, build_user_prompt

OUT_DIR = ROOT / "results" / "article_ratings"


def rate_one(article, judge, full, sys_prompt, usr_template, dry):
    aid = article["id"]
    out_dir = OUT_DIR / judge
    out_file = out_dir / f"{aid}.json"
    if out_file.exists():
        return "cached"
    user_msg = build_user_prompt(usr_template, article)
    if dry:
        return "dry"
    try:
        raw = call_llm(sys_prompt, user_msg, full, max_tokens=cfg.JUDGE_MAX_TOKENS)
    except Exception as e:
        return f"error:{e}"
    parsed, parse_err = _extract_json(raw or "")
    result = {
        "article_id": aid, "model": judge,
        "labeled_lean": article.get("labeled_lean", ""),
        "source": article.get("source", ""), "title": article.get("title", ""),
        "raw_response": raw, "parsed_output": parsed, "parse_error": parse_err,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if parsed and isinstance(parsed, dict):
        result["rating"] = parsed.get("rating")
        result["predicted_lean"] = parsed.get("lean", "")
        result["explanation"] = parsed.get("explanation", "")
        if result.get("rating") is not None:
            try:
                exp = classify_rating(float(result["rating"]))
                if result["predicted_lean"] != exp:
                    result["lean_mismatch"] = True
                    result["corrected_lean"] = exp
            except (TypeError, ValueError):
                pass
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return "ok" if parsed else "unparsed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="articles_v3.csv")
    ap.add_argument("--judges", nargs="+", default=cfg.JUDGES_EXT_NEW,
                    help=f"default: {cfg.JUDGES_EXT_NEW}")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    articles = list(csv.DictReader(open(ROOT / args.input, encoding="utf-8")))
    if args.limit:
        articles = articles[:args.limit]
    sys_prompt, usr_template = load_prompts()
    registry = load_model_registry()
    resolved = {j: resolve_model(j, registry) for j in args.judges}
    print(f"lean-ext | {len(articles)} articles x {len(args.judges)} judges "
          f"-> {len(articles)*len(args.judges)} ratings")
    for j, full in resolved.items():
        print(f"  {j:14s} -> {full}"
              + ("  [needs HF_TOKEN]" if full.startswith("hf/") else ""))
    if args.dry_run:
        print("  --dry-run: no API calls."); return
    if any(f.startswith("hf/") for f in resolved.values()) and not os.environ.get("HF_TOKEN"):
        raise SystemExit("  HF_TOKEN not set — export your HF Pro token first.")

    lock = threading.Lock(); tally = {}
    def _work(a, j, full):
        r = rate_one(a, j, full, sys_prompt, usr_template, False)
        with lock:
            key = r.split(":")[0]; tally[key] = tally.get(key, 0) + 1
    tasks = [(a, j, resolved[j]) for a in articles for j in args.judges]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(lambda t: _work(*t), tasks))
    print("  done:", tally)


if __name__ == "__main__":
    main()
