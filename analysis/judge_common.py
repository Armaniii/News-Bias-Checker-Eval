"""
judge_common.py — shared infrastructure for the Stage-1 LLM-judge runners
(voice_adoption.py / frame_distance_coding.py / directional_rd.py).

Provides:
  * load_source_texts(corpus_csv)   -> {article_id: text}
  * iter_rollouts(eval_letter, ...)  -> yields parsed rollout transcripts
  * run_jobs(jobs, judges, ...)      -> calls BOTH judges per job, concurrently,
                                        with a resumable jsonl cache + dry-run,
                                        returns a list of verdict records.

Each job is a dict: {"item_id", "system", "user", **meta}. Every meta key is
carried through to the output records, so the per-runner DataFrame assembly has
everything it needs (article_id, condition, target, source_lean, idx, ...).

Reuses run_eval.call_llm / resolve_model / load_model_registry and
validate_structured_output.extract_json — one source of truth for model
resolution + JSON parsing.
"""

from __future__ import annotations
import csv, json, pathlib, sys, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from run_eval import call_llm, resolve_model, load_model_registry  # noqa: E402
from validate_structured_output import extract_json                 # noqa: E402
import paper1_config as cfg                                          # noqa: E402
from analysis.curate_v3_200 import clean_text                        # noqa: E402

csv.field_size_limit(10_000_000)


def load_source_texts(corpus_csv: pathlib.Path) -> dict[str, str]:
    """Map article_id -> source text from a corpus CSV (cleaned + capped).

    Prefers the `text_clean` column when present (LLM boundary-stripped body,
    deterministically verified — see data/clean_v2 + clean-v2 workflow). Falls
    back to clean_text(text), which repairs JSON-escape / whitespace artifacts
    (idempotent on the already-clean v3 corpus)."""
    out = {}
    with open(corpus_csv, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            tc = (r.get("text_clean") or "").strip()
            text = tc if tc else clean_text(r.get("text") or "")
            out[r["id"]] = text[: cfg.SOURCE_TEXT_MAXCHARS]
    return out


def iter_rollouts(eval_letter: str, conditions=None, targets=None,
                  rollout_dir: pathlib.Path = None):
    """Yield parsed rollout transcript dicts for an eval.

    Layout: results/rollout/eval-{x}/{condition}/{target}/*.json
    Only transcripts that parsed successfully (parsed_output present) are yielded.
    """
    rollout_dir = rollout_dir or cfg.ROLLOUT
    base = rollout_dir / f"eval-{eval_letter}"
    if not base.exists():
        return
    targets = targets or cfg.TARGETS
    for cond_dir in sorted(base.iterdir()):
        if not cond_dir.is_dir():
            continue
        if conditions and cond_dir.name not in conditions:
            continue
        for target in targets:
            tdir = cond_dir / target
            if not tdir.is_dir():
                continue
            for jf in sorted(tdir.glob("*.json")):
                try:
                    d = json.load(open(jf, encoding="utf-8"))
                except Exception:
                    continue
                if d.get("parsed_output") is None:
                    continue
                d.setdefault("condition", cond_dir.name)
                d.setdefault("model", target)
                yield d


def _cache_load(cache_path: pathlib.Path) -> dict:
    done = {}
    if cache_path.exists():
        for line in open(cache_path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                done[(rec["item_id"], rec["judge"])] = rec
            except Exception:
                continue
    return done


def run_jobs(jobs, judges=None, cache_path=None, dry_run=False,
             limit=None, workers=6, max_tokens=400):
    """Run each job under each judge, concurrently, resumable.

    Returns a list of records: {item_id, judge, judge_family, raw, parsed, **meta}.
    parsed is the extract_json result (dict) or None on parse failure.
    """
    judges = judges or cfg.JUDGES
    registry = load_model_registry()
    cache_path = pathlib.Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if limit:
        jobs = jobs[:limit]

    done = _cache_load(cache_path)
    work = [(job, judge) for job in jobs for judge in judges
            if (job["item_id"], judge) not in done]

    print(f"  jobs={len(jobs)} judges={len(judges)} -> {len(jobs)*len(judges)} "
          f"verdicts; {len(done)} cached, {len(work)} to run")

    if dry_run:
        if work:
            j, jd = work[0]
            print("  --dry-run: sample job ->", jd)
            print("   item_id:", j["item_id"])
            print("   system[:120]:", j["system"][:120].replace("\n", " "))
            print("   user[:200]:", j["user"][:200].replace("\n", " "))
        print("  --dry-run: no API calls made.")
        return list(done.values())

    lock = threading.Lock()
    fh = open(cache_path, "a", encoding="utf-8")

    def _one(job, judge):
        full = resolve_model(judge, registry)
        raw = call_llm(job["system"], job["user"], full, max_tokens=max_tokens)
        parsed, _ = extract_json(raw)
        rec = {k: v for k, v in job.items() if k not in ("system", "user")}
        rec.update({"item_id": job["item_id"], "judge": judge,
                    "judge_family": cfg.JUDGE_FAMILY.get(judge, "?"),
                    "raw": raw, "parsed": parsed})
        with lock:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
        return rec

    done_n = err = 0
    total = len(work)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(_one, j, jd): (j["item_id"], jd) for j, jd in work}
        for fut in as_completed(futs):
            done_n += 1
            try:
                fut.result()
            except Exception as e:
                err += 1
                if err <= 10:
                    print(f"    ERR {futs[fut]}: {e}")
            if done_n % 50 == 0 or done_n == total:
                print(f"  [{done_n}/{total}] judged ({err} errors)")
    fh.close()
    print(f"  done: {done_n} calls, {err} errors. cache: {cache_path.name}")
    return list(_cache_load(cache_path).values())
