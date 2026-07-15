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


# ---------------------------------------------------------------------------
# Batch API path (50% pricing). Mirrors rate_articles.py / run_eval.py:
#   batch_submit()   -> build request files + manifest, submit both providers
#   batch_status()   -> poll
#   batch_download() -> fetch results, append parsed verdicts to the SAME
#                       cache jsonl the sync path uses. Parse failures are NOT
#                       cached, so a follow-up sync run (resume) patches them.
# custom_ids are positional ("j0", "j1", ...) with a manifest.json mapping
# back to (item_id, judge, meta) — sidesteps Anthropic's 64-char cid limit.
# ---------------------------------------------------------------------------

def _clients():
    import anthropic
    from openai import OpenAI
    import os
    return (anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"]),
            OpenAI(api_key=os.environ["OPENAI_API_KEY"]))


def batch_submit(jobs, judges=None, cache_path=None, batch_dir=None,
                 max_tokens=None, dry_run=False, force=False):
    """Submit uncached (job x judge) pairs as provider batches."""
    judges = judges or cfg.JUDGES
    max_tokens = max_tokens or cfg.JUDGE_MAX_TOKENS
    registry = load_model_registry()
    batch_dir = pathlib.Path(batch_dir); batch_dir.mkdir(parents=True, exist_ok=True)
    # Double-submit guard: re-submitting overwrites manifest.json while the
    # prior batch is still in flight — its positional custom_ids would then
    # resolve against the NEW manifest on download, silently assigning
    # verdicts to the wrong items. Download (or archive the dir) first.
    if (batch_dir / "batch_ids.json").exists() and not (dry_run or force):
        raise SystemExit(
            f"  REFUSING to submit: {batch_dir}/batch_ids.json exists — a prior "
            f"batch may be in flight and re-submitting would overwrite its "
            f"manifest (wrong-item contamination on download). Run --batch "
            f"download first, or archive/delete the batch dir, or pass force.")
    registry_chk = load_model_registry()
    hf_judges = [j for j in judges
                 if resolve_model(j, registry_chk).startswith("hf/")]
    if hf_judges:
        raise SystemExit(
            f"  HF judges {hf_judges} have no batch API — run them with the "
            f"SYNCHRONOUS path (run_jobs / the runner's --ext flag), not --batch.")
    done = _cache_load(pathlib.Path(cache_path))
    work = [(job, judge) for job in jobs for judge in judges
            if (job["item_id"], judge) not in done]
    print(f"  batch: {len(jobs)} jobs x {len(judges)} judges; "
          f"{len(done)} cached, {len(work)} to submit")
    if not work:
        return None

    manifest, anth_reqs, oa_lines = {}, [], []
    for i, (job, judge) in enumerate(work):
        cid = f"j{i}"
        meta = {k: v for k, v in job.items() if k not in ("system", "user")}
        meta.update({"item_id": job["item_id"], "judge": judge,
                     "judge_family": cfg.JUDGE_FAMILY.get(judge, "?")})
        manifest[cid] = meta
        full = resolve_model(judge, registry)
        provider, model = full.split("/", 1)
        if provider == "anthropic":
            # cache_control: every request in an instrument's batch shares the
            # same system prompt (>1024 tok post-v3.4.x) — cache reads bill at
            # 10% of input, stacking with the 50% batch discount (best-effort
            # hits within a batch). No-op if the prompt is under the minimum.
            anth_reqs.append({"custom_id": cid, "params": {
                "model": model, "max_tokens": max_tokens,
                "system": [{"type": "text", "text": job["system"],
                            "cache_control": {"type": "ephemeral"}}],
                "messages": [{"role": "user", "content": job["user"]}]}})
        else:
            oa_lines.append({"custom_id": cid, "method": "POST",
                "url": "/v1/chat/completions", "body": {
                    "model": model, "max_completion_tokens": max_tokens,
                    "messages": [{"role": "system", "content": job["system"]},
                                 {"role": "user", "content": job["user"]}]}})

    if dry_run and (batch_dir / "batch_ids.json").exists():
        # Never overwrite the manifest of a possibly-in-flight batch, even on
        # dry-run — stale manifest + live batch = wrong-item contamination.
        print(f"  --dry-run: would submit anthropic={len(anth_reqs)} "
              f"openai={len(oa_lines)} (files NOT written: prior batch_ids.json "
              f"present in {batch_dir})")
        return None
    (batch_dir / "manifest.json").write_text(json.dumps(manifest))
    oa_path = batch_dir / "openai_requests.jsonl"
    with open(oa_path, "w", encoding="utf-8") as f:
        for line in oa_lines:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    print(f"  prepared: anthropic={len(anth_reqs)} openai={len(oa_lines)} "
          f"(manifest + files in {batch_dir})")
    if dry_run:
        print("  --dry-run: not submitting.")
        return None

    anth_client, oa_client = _clients()
    ids = {}
    if anth_reqs:
        b = anth_client.messages.batches.create(requests=anth_reqs)
        ids["anthropic"] = b.id
        print(f"  Anthropic batch: {b.id}")
    if oa_lines:
        up = oa_client.files.create(file=open(oa_path, "rb"), purpose="batch")
        b = oa_client.batches.create(input_file_id=up.id,
                                     endpoint="/v1/chat/completions",
                                     completion_window="24h")
        ids["openai"] = b.id
        print(f"  OpenAI batch: {b.id}")
    (batch_dir / "batch_ids.json").write_text(json.dumps(ids))
    return ids


def batch_status(batch_dir):
    batch_dir = pathlib.Path(batch_dir)
    ids = json.loads((batch_dir / "batch_ids.json").read_text())
    anth_client, oa_client = _clients()
    out = {}
    if "anthropic" in ids:
        b = anth_client.messages.batches.retrieve(ids["anthropic"])
        c = b.request_counts
        out["anthropic"] = b.processing_status
        print(f"  Anthropic {ids['anthropic']}: {b.processing_status} "
              f"(ok={c.succeeded} err={c.errored} run={c.processing})")
    if "openai" in ids:
        b = oa_client.batches.retrieve(ids["openai"])
        out["openai"] = b.status
        print(f"  OpenAI {ids['openai']}: {b.status} "
              f"(ok={b.request_counts.completed} err={b.request_counts.failed} "
              f"total={b.request_counts.total})")
    return out


def batch_download(batch_dir, cache_path):
    """Fetch results, append successfully-parsed verdicts to the cache jsonl.

    Returns (saved, failed). Failures are left uncached so a sync run
    (run_jobs, resume mode) patches them with its built-in retry."""
    batch_dir = pathlib.Path(batch_dir)
    ids = json.loads((batch_dir / "batch_ids.json").read_text())
    manifest = json.loads((batch_dir / "manifest.json").read_text())
    anth_client, oa_client = _clients()
    already = _cache_load(pathlib.Path(cache_path))   # idempotent re-download
    fh = open(cache_path, "a", encoding="utf-8")
    saved = failed = skipped = 0

    def _save(cid, raw):
        nonlocal saved, failed, skipped
        meta = manifest.get(cid)
        if meta is None:
            failed += 1; return
        if (meta["item_id"], meta["judge"]) in already:
            skipped += 1; return
        parsed, _ = extract_json(raw or "")
        if parsed is None:
            failed += 1; return
        rec = dict(meta); rec.update({"raw": raw, "parsed": parsed})
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n"); saved += 1

    if "anthropic" in ids:
        for r in anth_client.messages.batches.results(ids["anthropic"]):
            if r.result.type == "succeeded":
                _save(r.custom_id, r.result.message.content[0].text)
            else:
                failed += 1
    if "openai" in ids:
        b = oa_client.batches.retrieve(ids["openai"])
        if b.output_file_id:
            for line in oa_client.files.content(b.output_file_id).text.splitlines():
                if not line.strip():
                    continue
                d = json.loads(line)
                body = (d.get("response") or {}).get("body") or {}
                ch = (body.get("choices") or [{}])[0]
                _save(d.get("custom_id"), (ch.get("message") or {}).get("content"))
    fh.close()
    print(f"  batch download: {saved} verdicts cached, {failed} failed/unparsed, "
          f"{skipped} already-cached skipped "
          f"(patch failures by re-running WITHOUT --batch — sync mode resumes from cache)")
    return saved, failed


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
             limit=None, workers=6, max_tokens=None):
    if max_tokens is None:
        # GPT-5 reasoning consumes the completion budget before visible
        # output — small caps return EMPTY content (see cfg.JUDGE_MAX_TOKENS).
        max_tokens = cfg.JUDGE_MAX_TOKENS
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
        if parsed is None:
            # One retry on parse failure (v3.4.0): silently-dropped NULLs
            # bias cell estimates invisibly if failures correlate with
            # content (e.g. messier reframing-arm outputs).
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
