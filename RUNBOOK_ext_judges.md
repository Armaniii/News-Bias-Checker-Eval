# Runbook — four-family judge panel (Qwen + DeepSeek via HF Pro)

Adds two open-weight judges (Alibaba Qwen, DeepSeek) alongside the
pre-registered Claude Sonnet 4.6 + GPT-5 pair, as **judges only** (no
target re-run). Non-destructive: new verdicts go to separate `.ext`
caches / new `results/article_ratings/` dirs; the pre-registered
two-judge analyses (which read `cfg.JUDGES`) are byte-for-byte unchanged.

## 0. One-time
```bash
export HF_TOKEN=hf_xxx          # your HF Pro token
```
Verify the two repo ids are currently served on HF Inference Providers
(open each model page → "Deploy → Inference Providers"). If a newer tag
exists, edit `shared/models.json` (keys `qwen3-235b`, `deepseek-r1`).
**Smoke-test one call first** (catches token/serving/format issues cheaply):
```bash
HF_TOKEN=$HF_TOKEN python3 analysis/rate_articles_ext.py --limit 1
```

## 1. Lean classification — the Paper-2 committee piece (~400 calls, ~$0.15–2)
```bash
HF_TOKEN=$HF_TOKEN python3 analysis/rate_articles_ext.py
# writes results/article_ratings/{qwen3-235b,deepseek-r1}/*.json
```
This makes the classification committee 6 models (2 targets + 4 judges).

## 2. Judge instruments — Paper-1 gates replication (sync path, no --batch)
```bash
HF_TOKEN=$HF_TOKEN python3 analysis/directional_rd.py       --ext --stage2
HF_TOKEN=$HF_TOKEN python3 analysis/voice_adoption.py       --ext --stage2
HF_TOKEN=$HF_TOKEN python3 analysis/frame_distance_coding.py --ext --stage2
# -> data/{directional_rd,voice_adoption,frame_distance_coding}.ext.cache.jsonl
#    + *.ext.parquet
```
Each is resumable (skips cached rows). `--limit N` to test. Full
replication total ≈ $5–30 depending on provider/model tier.

## 3. Analysis (after data lands)
- Committee / triage (Paper 2): point the analysis judge list at
  `cfg.JUDGES_EXT` (all four) instead of `cfg.JUDGES`.
- Gates (Paper 1): recompute cross-family κ on the four-family panel from
  the `.ext` caches merged with the originals; report per-family-pair.

## Caveats
1. **DeepSeek-R1 is a reasoning model** — emits long chain-of-thought
   before the JSON. `JUDGE_MAX_TOKENS=6000` should suffice, but if parse
   rates are low, raise it or switch `deepseek-r1` to a non-reasoning
   chat checkpoint (e.g. DeepSeek-V3.2) in `shared/models.json` — for a
   structured-output judge, a non-reasoning model is often more reliable.
2. **Reproducibility**: HF routes to a serving provider that may quantize;
   record the provider + model revision in the paper's methods.
3. **Rate limits**: Pro raises them; the sync path uses 6 workers. If you
   hit 429s, lower `--workers`.
4. No batch API for HF → no 50% batch discount; volume is small so it
   doesn't matter.

## What changed in the code (all reversible)
- `run_eval.py::call_llm` — added `hf/` branch (OpenAI-compatible router).
- `shared/models.json` — `qwen3-235b`, `deepseek-r1` entries.
- `analysis/paper1_config.py` — `JUDGES_EXT_NEW`, `JUDGES_EXT`,
  `JUDGE_FAMILY` (+2), `ext_cache()`. `JUDGES` unchanged (pre-registered).
- `analysis/{directional_rd,voice_adoption,frame_distance_coding}.py` —
  `--ext` flag (new judges → `.ext` cache/parquet, sync only).
- `analysis/judge_common.py::batch_submit` — guard: HF judges rejected
  from the batch path with a clear message.
- `analysis/rate_articles_ext.py` — NEW standalone lean classifier for the
  HF judges (same prompt files, same output schema).
