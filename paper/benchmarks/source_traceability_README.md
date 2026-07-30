# Source-Traceability of Judge-Cited Evidence — a deterministic LLM-judge benchmark

**Scorer:** `analysis/bench_source_traceability.py` · **no human ground truth, no second model required.**

## What it measures
When an LLM judge justifies a verdict by quoting phrases ("…the source calls
it 'X'…"), a minimal reliability requirement is that those phrases **exist in
the source**. A judge that cites phrases absent from the source is fabricating
evidence. This benchmark scores that property deterministically: boundary-aware
regex quote-extraction from the judge's `reason`, then lowercase substring
matching against the source article. It generalizes the pilot artifact check
(`analysis/verify_var_artifact.py`) into a scorer for *any* set of judge
verdicts.

## Metrics (per judge; lower is better)
Over verdicts whose reason cites ≥1 quoted phrase:
- **fabrication_rate** — fraction where *every* cited quote is absent from the source.
- **quote-untraceable** — fraction of *individual* cited quotes absent from the source.

## Reference leaderboard (VAR verdicts, 200 expert-rated news articles, 4 judge families)
| Judge family | scorable verdicts | fabrication_rate | quote-untraceable |
|---|---|---|---|
| **Qwen3-235B (Alibaba)** | 6,976 | **15.7%** | **19.4%** |
| Claude Sonnet 4.6 (Anthropic) | 11,262 | 43.2% | 55.4% |
| DeepSeek-V3.2 (DeepSeek) | 10,971 | 51.3% | 61.7% |
| GPT-5 (OpenAI) | 36 | 52.8%* | 52.5%* |

\*GPT-5 rarely cites quoted evidence at all (only 36 scorable verdicts) — **too
few to rank**; reported for completeness only. The headline finding is the
**3× spread** among the well-sampled judges: Qwen cites real quotes far more
reliably than the others.

## How to run (add any judge by pointing at its verdict cache)
```
python3 analysis/bench_source_traceability.py \
    --caches data/voice_adoption.cache.jsonl data/voice_adoption.ext.cache.jsonl
```
Each cache row needs `article_id`, `judge`, and `parsed.reason`. Contaminated
pilot articles (PRE_REGISTRATION §6.8.9) are excluded automatically.

## Scope & limitations (honest)
- **Conditional on citing quotes.** It scores traceability *given* the judge
  cites quoted evidence; a judge that rarely quotes (e.g. GPT-5 here) has few
  scorable verdicts and should not be ranked on it.
- **Existence, not correctness.** A traceable quote can still support a wrong
  verdict; an absent quote is usually fabrication but can be a close paraphrase.
  This is a necessary-not-sufficient reliability check — it catches a concrete
  failure (evidence hallucination) cheaply, not overall judge validity.
- **Deterministic and reproducible:** boundary-aware quote regex (no
  possessive-apostrophe false positives), lowercase substring match, fixed
  corpus. Same inputs → same numbers, no model in the loop.
