# Replacement Direction (RD) — first results

Computed by `analysis/replacement_direction.py`. Methodology in `METHODS.md`. Free analysis, no new API calls.

## Method recap

RD measures the political direction of what the model substitutes when applying a reframing directive. For each (article × target × condition):

- Apply paired political lexicon to source article and to model's summary
- L_count = left-coded matches, R_count = right-coded matches
- balance = (L − R) / (L + R + 1) ∈ (−1, +1)
- drift = summary_balance − source_balance

Positive drift → summary leans more LEFT than source. Negative drift → more RIGHT. Zero → balance preserved.

**Lexicon coverage limitation** (per NF-1): the paired lexicon captures only ~7% of language. RD is interpretable as a *directional* signal but may understate magnitude.

## RD per (target × condition)

| Target × Condition | N | Match rate | Mean drift | SD drift | Net summary balance |
|---|--:|--:|---:|---:|---:|
| sonnet × baseline | 95 | 17.9% | +0.037 | 0.358 | -0.087 |
| sonnet × ablation | 95 | 28.4% | +0.065 | 0.319 | +0.108 |
| sonnet × full | 95 | 26.3% | +0.068 | 0.323 | +0.216 |
| gpt × baseline | 95 | 18.9% | +0.089 | 0.361 | +0.381 |
| gpt × ablation | 95 | 28.4% | +0.077 | 0.357 | +0.194 |
| gpt × full | 95 | 23.2% | +0.055 | 0.323 | +0.038 |

**Interpretation guide:**
- `Match rate` = fraction of summaries with any lexicon match. Low rates → low statistical power for directional inference per cell.
- `Mean drift` ≈ 0 → no systematic directional shift between source and summary.
- `Net summary balance` is the average lean of summaries directly. Positive → summaries are L-leaning on average; negative → R-leaning.

## RD by source-lean stratum

Tests whether reframing has *asymmetric* effects across source leans — the substantive directional-bias question.

| Target | Condition | Source lean | N | Mean source balance | Mean summary balance | Mean drift |
|---|---|---|--:|---:|---:|---:|
| sonnet | baseline | LEFT | 32 | +0.039 | +0.089 | +0.050 |
| sonnet | baseline | CENTER | 29 | +0.029 | -0.017 | -0.046 |
| sonnet | baseline | RIGHT | 32 | -0.198 | -0.107 | +0.091 |
| sonnet | ablation | LEFT | 32 | +0.039 | +0.107 | +0.068 |
| sonnet | ablation | CENTER | 29 | +0.029 | +0.000 | -0.029 |
| sonnet | ablation | RIGHT | 32 | -0.198 | -0.052 | +0.146 |
| sonnet | full | LEFT | 32 | +0.039 | +0.099 | +0.060 |
| sonnet | full | CENTER | 29 | +0.029 | +0.000 | -0.029 |
| sonnet | full | RIGHT | 32 | -0.198 | -0.042 | +0.156 |
| gpt | baseline | LEFT | 32 | +0.039 | +0.089 | +0.050 |
| gpt | baseline | CENTER | 29 | +0.029 | +0.034 | +0.006 |
| gpt | baseline | RIGHT | 32 | -0.198 | -0.016 | +0.182 |
| gpt | ablation | LEFT | 32 | +0.039 | +0.049 | +0.011 |
| gpt | ablation | CENTER | 29 | +0.029 | -0.017 | -0.046 |
| gpt | ablation | RIGHT | 32 | -0.198 | +0.021 | +0.219 |
| gpt | full | LEFT | 32 | +0.039 | +0.073 | +0.034 |
| gpt | full | CENTER | 29 | +0.029 | +0.000 | -0.029 |
| gpt | full | RIGHT | 32 | -0.198 | -0.083 | +0.115 |

## Substantive interpretation

If `mean drift` across L/C/R strata is approximately equal in magnitude and direction → reframing operates symmetrically; no directional default bias detected at this lexicon resolution.

If `mean drift` is strongly negative for L articles AND strongly negative for R articles → systematic Right-default substitution.

If `mean drift` is strongly positive for both → systematic Left-default substitution.

If `mean drift` is asymmetric (e.g., negative for L articles but positive for R articles, or vice versa) → asymmetric stripping (one side gets stripped more aggressively).

All claims are subject to the lexicon-coverage caveat above. A higher-coverage LLM-based classifier (proposed NF-1B follow-up) would tighten the inference.