"""
rate_articles.py

Article-level bias rating using AllSides methodology.
Sends each article to judge models (Opus 4.6 + GPT-5) via batch API.

Usage:
  python rate_articles.py --prepare --submit    # Generate JSONL + submit
  python rate_articles.py --status              # Check batch status
  python rate_articles.py --download            # Download results + save
"""

import argparse
import csv
import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone

csv.field_size_limit(sys.maxsize)

# Load .env
_env_path = pathlib.Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

ROOT = pathlib.Path(__file__).resolve().parent
OUT_DIR = ROOT / "results" / "article_ratings"
BATCH_DIR = OUT_DIR / "batch"

# Anthropic-side judge revised Opus 4.6 -> Sonnet 4.6 (Path-B canonical pair,
# PRE_REGISTRATION §1.1; propagated here 2026-06-08 v3.4.0 amendment — the
# prior Opus ratings were also on the superseded legacy-100 corpus and must be
# regenerated on articles_v3.csv regardless).
MODELS = {
    "claude-sonnet-4-6": {
        "provider": "anthropic",
        "api_model": "claude-sonnet-4-6",
    },
    "gpt-5": {
        "provider": "openai",
        "api_model": "gpt-5",
    },
}

LEAN_BOUNDARIES = [
    (-9.00, -3.00, "Left"),
    (-2.99, -1.00, "Lean Left"),
    (-0.99,  0.99, "Center"),
    ( 1.00,  2.99, "Lean Right"),
    ( 3.00,  9.00, "Right"),
]


def classify_rating(rating):
    if rating <= -3.00: return "Left"
    if rating <= -1.00: return "Lean Left"
    if rating <=  0.99: return "Center"
    if rating <=  2.99: return "Lean Right"
    return "Right"


def load_articles(path):
    articles = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            articles.append(row)
    return articles


def load_prompts():
    sys_prompt = (ROOT / "rate-article-system.txt").read_text(encoding="utf-8")
    usr_template = (ROOT / "rate-article-user.txt").read_text(encoding="utf-8")
    return sys_prompt, usr_template


def build_user_prompt(usr_template, article):
    # HEADLINE/SOURCE removed 2026-06-08 (v3.4.0 de-leak): outlet name leaks
    # the AllSides label to the ground-truth judge. Article text only, prefer
    # the boundary-cleaned column.
    text = ((article.get("text_clean") or "").strip()
            or article.get("text", "").strip())
    return usr_template + "\n\n" + text


# =============================================================================
# BATCH PREPARATION
# =============================================================================

def prepare(articles_path):
    articles = load_articles(articles_path)
    sys_prompt, usr_template = load_prompts()
    BATCH_DIR.mkdir(parents=True, exist_ok=True)

    anthropic_reqs = []
    openai_reqs = []

    for article in articles:
        aid = article["id"]
        user_msg = build_user_prompt(usr_template, article)

        for model_key, mcfg in MODELS.items():
            # Skip if result already exists
            out_file = OUT_DIR / model_key / f"{aid}.json"
            if out_file.exists():
                continue

            cid = f"rate__{model_key}__{aid}"
            # Shorten for Anthropic 64-char limit
            short_cid = (cid
                         .replace("claude-sonnet-4-6", "cso46")
                         .replace("article_", "a", 1))

            if mcfg["provider"] == "anthropic":
                anthropic_reqs.append({
                    "custom_id": short_cid,
                    "params": {
                        "model": mcfg["api_model"],
                        "max_tokens": 2000,
                        "system": sys_prompt,
                        "messages": [{"role": "user", "content": user_msg}],
                    }
                })
            elif mcfg["provider"] == "openai":
                body = {
                    "model": mcfg["api_model"],
                    "max_completion_tokens": 16000,
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_msg},
                    ],
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "article_rating",
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "rating": {"type": "number"},
                                    "lean": {
                                        "type": "string",
                                        "enum": ["Left", "Lean Left", "Center",
                                                 "Lean Right", "Right"],
                                    },
                                    "explanation": {"type": "string"},
                                },
                                "required": ["rating", "lean", "explanation"],
                                "additionalProperties": False,
                            },
                        },
                    },
                }
                openai_reqs.append({
                    "custom_id": cid,
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": body,
                })

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    files = {}

    if anthropic_reqs:
        fp = BATCH_DIR / f"anthropic_rate_{ts}.jsonl"
        with open(fp, "w", encoding="utf-8") as f:
            for req in anthropic_reqs:
                f.write(json.dumps(req, ensure_ascii=False) + "\n")
        files["anthropic"] = fp
        print(f"  Anthropic: {len(anthropic_reqs)} requests -> {fp.name}")

    if openai_reqs:
        fp = BATCH_DIR / f"openai_rate_{ts}.jsonl"
        with open(fp, "w", encoding="utf-8") as f:
            for req in openai_reqs:
                f.write(json.dumps(req, ensure_ascii=False) + "\n")
        files["openai"] = fp
        print(f"  OpenAI:    {len(openai_reqs)} requests -> {fp.name}")

    if not files:
        print("  No requests to prepare (all results exist).")

    return files


# =============================================================================
# SUBMIT
# =============================================================================

def submit(batch_files=None):
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    batch_ids = {}

    # If no files passed, find the most recent ones
    if not batch_files:
        batch_files = {}
        for provider in ("anthropic", "openai"):
            candidates = sorted(BATCH_DIR.glob(f"{provider}_rate_*.jsonl"))
            if candidates:
                batch_files[provider] = candidates[-1]

    if "anthropic" in batch_files:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        fp = batch_files["anthropic"]
        requests = []
        with open(fp, encoding="utf-8") as f:
            for line in f:
                requests.append(json.loads(line))
        batch = client.messages.batches.create(requests=requests)
        batch_ids["anthropic"] = batch.id
        print(f"  Anthropic batch submitted: {batch.id}")

    if "openai" in batch_files:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        fp = batch_files["openai"]
        upload = client.files.create(file=open(fp, "rb"), purpose="batch")
        batch = client.batches.create(
            input_file_id=upload.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        batch_ids["openai"] = batch.id
        print(f"  OpenAI batch submitted: {batch.id}")

    if batch_ids:
        ids_file = BATCH_DIR / "batch_ids.json"
        existing = {}
        if ids_file.exists():
            with open(ids_file) as f:
                existing = json.load(f)
        existing.update(batch_ids)
        with open(ids_file, "w") as f:
            json.dump(existing, f, indent=2)
        print(f"  Batch IDs saved to {ids_file}")


# =============================================================================
# STATUS
# =============================================================================

def status():
    ids_file = BATCH_DIR / "batch_ids.json"
    if not ids_file.exists():
        print("  No batch_ids.json found.")
        return

    with open(ids_file) as f:
        batch_ids = json.load(f)

    for provider, bid in batch_ids.items():
        if provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
            batch = client.messages.batches.retrieve(bid)
            counts = batch.request_counts
            print(f"  Anthropic {bid}: {batch.processing_status}"
                  f" (succeeded={counts.succeeded}, errored={counts.errored},"
                  f" processing={counts.processing})")
        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            batch = client.batches.retrieve(bid)
            print(f"  OpenAI {bid}: {batch.status}"
                  f" (completed={batch.request_counts.completed},"
                  f" failed={batch.request_counts.failed},"
                  f" total={batch.request_counts.total})")


# =============================================================================
# DOWNLOAD
# =============================================================================

def _expand_cid(cid):
    """Expand shortened custom_id back to full form.

    Handles both legacy numeric ids (a1056 -> article_1056) and v3 composite
    ids (aarticles_22548 -> article_articles_22548, abackup7_101004 ->
    article_backup7_101004)."""
    s = cid
    s = s.replace("cso46", "claude-sonnet-4-6")
    # Idempotent: OpenAI custom_ids are stored full-form (never shortened) —
    # only expand when the id is actually in shortened form, otherwise
    # "__article_x" would be re-expanded into "__article_rticle_x".
    if "__article_" not in s:
        s = re.sub(r"__a(?=[\w])", "__article_", s, count=1)
    return s


def _extract_json(text):
    """Extract JSON from model response."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()
    try:
        return json.loads(text), None
    except json.JSONDecodeError as e:
        # Try to find JSON object in the text
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group()), None
            except json.JSONDecodeError:
                pass
        return None, str(e)


def _save_result(custom_id, raw_text, articles_by_id):
    """Save a single rating result."""
    full_cid = _expand_cid(custom_id)
    # Format: rate__{model}__{article_id}
    parts = full_cid.split("__", 2)
    if len(parts) < 3 or parts[0] != "rate":
        print(f"    Unexpected custom_id: {custom_id}")
        return 0

    model_key = parts[1]
    article_id = parts[2]

    parsed, parse_err = _extract_json(raw_text)

    article = articles_by_id.get(article_id, {})

    result = {
        "article_id": article_id,
        "model": model_key,
        "labeled_lean": article.get("labeled_lean", ""),
        "source": article.get("source", ""),
        "title": article.get("title", ""),
        "raw_response": raw_text,
        "parsed_output": parsed,
        "parse_error": parse_err,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Extract structured fields if parsed
    if parsed and isinstance(parsed, dict):
        result["rating"] = parsed.get("rating")
        result["predicted_lean"] = parsed.get("lean", "")
        result["explanation"] = parsed.get("explanation", "")
        # Validate lean matches rating
        if result["rating"] is not None:
            expected_lean = classify_rating(float(result["rating"]))
            if result["predicted_lean"] != expected_lean:
                result["lean_mismatch"] = True
                result["corrected_lean"] = expected_lean

    out_dir = OUT_DIR / model_key
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{article_id}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return 1


def download(articles_path):
    ids_file = BATCH_DIR / "batch_ids.json"
    if not ids_file.exists():
        print("  No batch_ids.json found.")
        return

    with open(ids_file) as f:
        batch_ids = json.load(f)

    # Load articles for metadata
    articles = load_articles(articles_path)
    articles_by_id = {a["id"]: a for a in articles}

    total_saved = 0

    for provider, bid in batch_ids.items():
        if provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
            batch = client.messages.batches.retrieve(bid)
            if batch.processing_status != "ended":
                print(f"  Anthropic {bid}: still {batch.processing_status}, skipping")
                continue
            for result in client.messages.batches.results(bid):
                cid = result.custom_id
                if result.result.type == "succeeded":
                    text = result.result.message.content[0].text
                    total_saved += _save_result(cid, text, articles_by_id)
                else:
                    print(f"    {cid}: {result.result.type}")

        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            batch = client.batches.retrieve(bid)
            if batch.status != "completed":
                print(f"  OpenAI {bid}: still {batch.status}, skipping")
                continue
            content = client.files.content(batch.output_file_id)
            for line in content.text.strip().split("\n"):
                entry = json.loads(line)
                cid = entry["custom_id"]
                resp = entry.get("response", {})
                if resp.get("status_code") == 200:
                    text = resp["body"]["choices"][0]["message"]["content"]
                    total_saved += _save_result(cid, text, articles_by_id)
                else:
                    print(f"    {cid}: error {resp.get('status_code')}")

    print(f"  Saved {total_saved} results")

    # Generate summary
    if total_saved > 0:
        _generate_summary()


def _generate_summary():
    """Generate a summary CSV and comparison table."""
    rows = []
    for model_dir in sorted(OUT_DIR.iterdir()):
        if not model_dir.is_dir() or model_dir.name == "batch":
            continue
        for jf in sorted(model_dir.glob("*.json")):
            with open(jf) as f:
                r = json.load(f)
            rows.append({
                "article_id": r.get("article_id"),
                "model": r.get("model"),
                "source": r.get("source"),
                "labeled_lean": r.get("labeled_lean"),
                "rating": r.get("rating"),
                "predicted_lean": r.get("corrected_lean", r.get("predicted_lean", "")),
            })

    if not rows:
        return

    # Save summary CSV
    csv_path = OUT_DIR / "article_ratings_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"  Summary CSV: {csv_path}")

    # Print comparison table
    from collections import defaultdict
    by_article = defaultdict(dict)
    for r in rows:
        by_article[r["article_id"]][r["model"]] = r

    models = sorted(set(r["model"] for r in rows))
    lean_order = ["Left", "Lean Left", "Center", "Lean Right", "Right"]

    print(f"\n  {'Article':<15} {'Outlet Lean':<12}", end="")
    for m in models:
        short = m.replace("claude-sonnet-4-6", "Sonnet").replace("gpt-5", "GPT-5")
        print(f"  {short:>15}", end="")
    print(f"  {'Agree?':>8}")
    print("  " + "-" * 70)

    agree_count = 0
    total = 0
    for aid in sorted(by_article.keys()):
        data = by_article[aid]
        first = list(data.values())[0]
        print(f"  {aid:<15} {first['labeled_lean']:<12}", end="")
        leans = []
        for m in models:
            d = data.get(m, {})
            rating = d.get("rating", "")
            lean = d.get("predicted_lean", "")
            print(f"  {rating:>5} ({lean:>3})", end="") if rating else print(f"  {'':>15}", end="")
            if lean:
                leans.append(lean)
        agree = len(set(leans)) == 1 if len(leans) == len(models) else False
        if agree:
            agree_count += 1
        total += 1
        print(f"  {'Yes' if agree else 'No':>8}")

    if total:
        print(f"\n  Inter-judge agreement: {agree_count}/{total} ({agree_count/total*100:.0f}%)")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Article-level bias rating via batch API")
    parser.add_argument("--input", default="articles_v3.csv",
                        help="Articles CSV (default: articles_v3.csv)")
    parser.add_argument("--prepare", action="store_true",
                        help="Prepare batch JSONL files")
    parser.add_argument("--submit", action="store_true",
                        help="Submit batch files to APIs")
    parser.add_argument("--status", action="store_true",
                        help="Check batch status")
    parser.add_argument("--download", action="store_true",
                        help="Download results")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be prepared without writing files")
    args = parser.parse_args()

    if not any([args.prepare, args.submit, args.status, args.download, args.dry_run]):
        parser.print_help()
        return

    if args.dry_run:
        articles = load_articles(args.input)
        total = len(articles) * len(MODELS)
        existing = sum(1 for m in MODELS
                       for a in articles
                       if (OUT_DIR / m / f"{a['id']}.json").exists())
        print(f"  Articles: {len(articles)}")
        print(f"  Models: {', '.join(MODELS.keys())}")
        print(f"  Total requests: {total}")
        print(f"  Already complete: {existing}")
        print(f"  Remaining: {total - existing}")
        return

    if args.prepare:
        print("Preparing batch files...")
        batch_files = prepare(args.input)
        if args.submit and batch_files:
            print("\nSubmitting batches...")
            submit(batch_files)
            print("\nNext steps:")
            print(f"  python rate_articles.py --status")
            print(f"  python rate_articles.py --download --input {args.input}")
        elif batch_files:
            print("\nTo submit:")
            print(f"  python rate_articles.py --submit")
        return

    if args.submit:
        print("Submitting most recent batch files...")
        submit()
        return

    if args.status:
        print("Checking batch status...")
        status()
        return

    if args.download:
        print("Downloading results...")
        download(args.input)
        return


if __name__ == "__main__":
    main()
