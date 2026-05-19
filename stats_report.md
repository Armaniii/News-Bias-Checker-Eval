# Statistics Report

Computed by `analysis/run_all_stats.py`. Confirmatory analyses
specified in `PRE_REGISTRATION.md`. Replaces ad-hoc thresholds
and unsupported claims with proper inferential tests.

Report version: `v3`. Pre-registration: `PRE_REGISTRATION.md`.

## FDR-corrected confirmatory tests (Benjamini-Hochberg, q=0.05)

| Hypothesis | p (raw) | p (BH-FDR) | Significant |
|------------|--------:|-----------:|:-----------:|
| `H_BPS_favoritism_eval_c` | 0.0000 | 0.0000 | ✓ |
| `H_BPS_target_eval_b` | 0.0001 | 0.0003 | ✓ |
| `H_BPS_target_eval_c` | 0.0011 | 0.0045 | ✓ |
| `H_BPS_favoritism_eval_a` | 0.0209 | 0.0627 |   |
| `H_validity_favoritism` | 0.1346 | 0.3231 |   |
| `H_explanation_quality_target` | 0.1995 | 0.3796 |   |
| `H_lean_target` | 0.2476 | 0.3796 |   |
| `H_lean_favoritism` | 0.2531 | 0.3796 |   |
| `H_explanation_quality_favoritism` | 0.3643 | 0.4858 |   |
| `H_BPS_favoritism_eval_b` | 0.5408 | 0.6490 |   |
| `H_validity_target` | 0.6614 | 0.7216 |   |
| `H_BPS_target_eval_a` | 0.9013 | 0.9013 |   |

`✓` = BH-corrected p < 0.05. Significant hypotheses are *confirmed*
under the pre-registered family-wise correction.

## Per-eval BPS model — `bps ~ target × judge` with article clustering

Reference levels: target = sonnet, judge = opus. Positive `target_main` β
means GPT-4.1's BPS is *higher* (worse) than Sonnet's *when judged by Opus*.
Positive `interaction` β means the GPT-5 judge widens the GPT-4.1 − Sonnet
gap relative to Opus — a same-family-favoritism signal.

BPS scoring: 1 = no failures, 10 = systematic failures (lower = better).

Method falls back from LMM to OLS+cluster-robust SE when the article-level
random intercept is singular (ICC ≈ 0). Both methods cluster on `article_id`.

| Eval | Method | N obs | N articles | ICC | Target main β [95% CI] (p) | Judge main β [95% CI] (p) | Interaction β [95% CI] (p) |
|------|--------|------:|-----------:|----:|----------------------|----------------------|----------------------|
| A | LMM | 356 | 95 | 0.19 | -0.03 [-0.53, +0.47] (p=0.901) | **+1.95** [+1.43, +2.47] (p=0.000) | **-0.86** [-1.60, -0.13] (p=0.021) |
| B | OLS+CR | 379 | 95 | 0.00 | **-0.41** [-0.61, -0.21] (p=0.000) | **-1.39** [-1.58, -1.20] (p=0.000) | +0.06 [-0.14, +0.27] (p=0.541) |
| C | OLS+CR | 378 | 95 | 0.00 | **+0.44** [+0.18, +0.71] (p=0.001) | **+1.78** [+1.44, +2.12] (p=0.000) | **-1.42** [-1.90, -0.94] (p=0.000) |

Bold = p < 0.05 (uncorrected). Multiple-comparison correction (Benjamini-
Hochberg) will be applied across the family of primary tests once all
LMMs (explanation quality, detection validity) are fit in subsequent phases.

### Sanity check vs paired t-test on judge-averaged BPS

Marginal target effect from the LMM (averaged across judges) should track
the paired-t mean difference closely, confirming model identification.

| Eval | Paired-t mean diff (GPT − Sonnet) | t | p | LMM marginal target β |
|------|-----------------------:|---:|---:|---------------------:|
| A | -0.36 | -1.71 | 0.090 | -0.46 |
| B | -0.38 | -4.70 | 0.000 | -0.38 |
| C | -0.25 | -1.34 | 0.182 | -0.27 |

## LMM 2 — Explanation quality (`score ~ target × judge`, meta_judgment)

N obs: **380**, N articles: **95**, ICC_article: **0.18**, method: `lmm_random_intercept`.

Lower score = explanation cites specific language; higher = generic boilerplate.
Positive `target_main` β means GPT-4.1 writes worse (more boilerplate) explanations.

| Effect | β [95% CI] (p) |
|--------|---------------|
| Target main (GPT-4.1 vs Sonnet, at Opus) | +0.47 [-0.25, +1.20] (p=0.200) |
| Judge main (GPT-5 vs Opus, at Sonnet) | -0.02 [-0.74, +0.70] (p=0.955) |
| Target × Judge interaction (favoritism) | +0.47 [-0.55, +1.50] (p=0.364) |

Sanity check: paired-t mean diff = +0.71, LMM marginal target β = +0.71 (p=0.041).

## LMM 3 — Detection validity (logistic, `verdict_valid ~ target × judge`)

N detection-judgments: **1326**, N articles: **87**, method: `gee_logit_exchangeable`.

Outcome: 1 if verdict ∈ {confirmed, plausible}, else 0. Odds ratio > 1 means
the GPT-4.1 detection is more likely to be valid than Sonnet's.

| Effect | OR [95% CI] (p) | log-odds β |
|--------|-----------------|------------|
| Target main (GPT-4.1 vs Sonnet, at Opus judge) | 0.89 [0.53, 1.51] (p=0.661) | -0.12 |
| Judge main (GPT-5 vs Opus, at Sonnet target) | **0.36** [0.23, 0.56] (p=0.000) | -1.03 |
| Target × Judge interaction | 1.50 [0.88, 2.54] (p=0.135) | +0.40 |

## Exploratory — Bias-Direction Asymmetry (NF-1)

**Question:** Are LLMs more critical of one political direction
than the other, holding article lean constant?

**Method:** For each detection, classify the flagged `biasedText`
against a paired political lexicon as left-coded, right-coded, both,
or neither. Article lean is Opus's article-level rating.

*Lexicon (Paired terminology pairs: 45 (45 LEFT + 45 RIGHT). Unpaired LEFT phrases: 45. Unpaired RIGHT phrases: 55. Total LEFT match patterns: 90; total RIGHT match patterns: 100.):* phrases sourced from `rate-article-system.txt` ideological
markers + standard political-science vocabulary. Lexicon is
paired by design — each LEFT/RIGHT terminological counterpart
is included as a matched pair. Slight imbalance in unpaired
counts (LEFT: 45, RIGHT: 55) reported transparently for reader auditing.

**Coverage:** Of 1326 total detections,
1292 have a known article lean. Direction
distribution: neither = 1201, left = 34, right = 56, both = 1.

**Coverage limitation:** ~93% of detections flag bias *mechanisms*
(spin verbs, framing, omission patterns) rather than ideologically-
coded vocabulary. The lexicon-based classifier therefore tags only
a minority of detections. Power for the asymmetry test is limited.
A future LLM-based classifier could substantially raise coverage
(see EVAL_CRITIQUE.md NF-1 follow-ups).

### Descriptive — left/right flag rates by target × article lean

| Target | Article lean | % left-coded | % right-coded |
|--------|-------------|------------:|------------:|
| sonnet | Left | 5.7% | 0.0% |
| sonnet | Lean Left | 4.6% | 3.1% |
| sonnet | Center | 0.0% | 0.0% |
| sonnet | Lean Right | 2.2% | 6.7% |
| sonnet | Right | 1.2% | 11.6% |
| gpt | Left | 6.1% | 0.0% |
| gpt | Lean Left | 0.8% | 2.5% |
| gpt | Center | 0.0% | 0.0% |
| gpt | Lean Right | 4.8% | 7.1% |
| gpt | Right | 0.0% | 11.4% |

### GEE-logit fits — `outcome ~ target × lean_ordinal`

Lean ordinal: Left=−2, Lean Left=−1, Center=0, Lean Right=+1, Right=+2.
Reference target = Sonnet. Cluster-robust SEs by article.

| Outcome | N | Target main OR [95% CI] (p) | Lean main OR [95% CI] (p) | Interaction OR [95% CI] (p) |
|---------|--:|-----------------------------|----------------------------|------------------------------|
| is_left_coded | 1292 | 1.08 [0.60, 1.94] (p=0.802) | 0.64 [0.37, 1.09] (p=0.101) | 1.10 [0.78, 1.53] (p=0.589) |
| is_right_coded | 1292 | 1.02 [0.29, 3.59] (p=0.974) | **2.31** [1.19, 4.49] (p=0.014) | 1.08 [0.54, 2.17] (p=0.822) |

**Interpretation guide.** A target_main OR > 1 on `is_left_coded`
means GPT-4.1 flags left-coded language at a higher rate than Sonnet
does (at the lean=0 / Center level). The lean_main OR captures the
expected baseline — Right articles produce more right-coded flags,
Left articles more left-coded flags. The target × lean interaction
tests whether one target is *differentially sensitive* to ideological
language by article-lean direction.

**Findings.**

1. **No detectable target asymmetry.** Target main effects are null
   on both directional outcomes (OR ≈ 1.0–1.1, p ≥ 0.80) — Sonnet
   and GPT-4.1 flag left- and right-coded language at indistinguishable
   rates after controlling for article lean.
2. **Lean main effect is significant only for `is_right_coded`** 
   (OR = 2.31, p = 0.014) — right-coded flag rate scales with article
   right-leaningness, as expected. The corresponding effect for
   `is_left_coded` is directionally consistent (OR = 0.64) but does not
   reach significance.
3. **No interaction.** Neither target shows differential sensitivity
   by article-lean direction (interaction p ≥ 0.59 on both outcomes).

**Bottom line.** Within the 1,292-detection sample with a known article
lean, both targets behave symmetrically across political directions,
with detection rates that scale with the article's actual ideological
direction in the expected way. *This is a substantive null result*,
but **power is limited**: only ~7% of detections contained
ideologically-coded vocabulary captured by the lexicon. A higher-
coverage classifier (LLM-based) is the recommended robustness check.

## Exploratory — Detection Precision / Recall / F1

**Not in the pre-registered FDR family.** Replaces the gestalt 1–10
`false_positive_rate` / `false_negative_rate` custom_qualities with
hard counts derived from the existing verification verdicts:

- TP = detections with verdict ∈ {confirmed, plausible}
- FP = detections with verdict ∈ {unsupported, hallucinated}
- FN = entries in `*_false_negatives` for that (target, judge)

### Cell means by (target, judge)

| Target | Judge | TP | FP | FN | Precision | Recall | F1 | N detections |
|--------|-------|---:|---:|---:|----------:|-------:|---:|-------------:|
| gpt | gpt5 | 3.19 | 0.31 | 1.00 | 0.895 | 0.698 | 0.883 | 3.49 |
| gpt | opus | 3.35 | 0.15 | 3.45 | 0.961 | 0.387 | 0.691 | 3.49 |
| sonnet | gpt5 | 2.98 | 0.51 | 0.96 | 0.834 | 0.767 | 0.862 | 3.48 |
| sonnet | opus | 3.29 | 0.19 | 3.28 | 0.933 | 0.481 | 0.700 | 3.48 |

N valid F1 cells: 273 of 380 (NaN when target made 0 detections AND judge proposed 0 false negatives — neither precision nor recall defined).

### Marginal target effects (across both judges)

- **gpt**: P = 0.928, R = 0.532, F1 = 0.786
- **sonnet**: P = 0.883, R = 0.618, F1 = 0.779

### LMM fits — `outcome ~ target × judge + (1|article)`

| Outcome | Method | N | ICC | Target main β [95% CI] (p) | Judge main β [95% CI] (p) | Interaction β [95% CI] (p) |
|---------|--------|--:|----:|-------|-------|-------|
| precision | LMM | 280 | 0.51 | -0.013 [-0.067, +0.042] (p=0.649) | **-0.099** [-0.147, -0.050] (p=0.000) | +0.033 [-0.040, +0.105] (p=0.378) |
| recall | OLS+CR | 346 | 0.00 | **-0.095** [-0.172, -0.017] (p=0.017) | **+0.285** [+0.212, +0.359] (p=0.000) | +0.026 [-0.019, +0.071] (p=0.263) |
| f1 | OLS+CR | 273 | 0.00 | -0.010 [-0.055, +0.035] (p=0.667) | **+0.162** [+0.104, +0.220] (p=0.000) | +0.030 [-0.037, +0.098] (p=0.376) |

**Caveat — recall is judge-bound.** A judge that proposes more
missed detections (`*_false_negatives`) drags recall down for both
targets. Look at the judge-main effect for recall: it captures
'how aggressively does this judge propose missed detections,'
not target ability. Precision is similarly affected through the
verdict mix. The target × judge interaction is the cleanest target-
comparison signal.

## LMM 4 — Lean classification accuracy (logistic)

N article-(target,judge) cells: **370**, N articles: **95**, method: `gee_logit_exchangeable`.

Outcome: 1 if target's predicted lean equals the judge's article-rating lean,
else 0. Each judge's article rating serves as that judge's ground truth.
Interaction tests favoritism: does GPT-5-as-truth disproportionately favor GPT-4.1?

| Effect | OR [95% CI] (p) | log-odds β |
|--------|-----------------|------------|
| Target main (GPT-4.1 vs Sonnet, at Opus truth) | 0.74 [0.44, 1.24] (p=0.248) | -0.31 |
| Judge-truth main (GPT-5 vs Opus, at Sonnet) | 0.71 [0.43, 1.19] (p=0.199) | -0.34 |
| Target × Judge-truth interaction (favoritism) | 1.42 [0.78, 2.62] (p=0.253) | +0.35 |

## Exploratory — Absorption vs Generation × Condition (NF-3 extended)

**Question:** When a model's summary contains bias, is it parroting
source bias (absorption) or introducing new bias (generation)? And
how does the neutrality instruction in the system prompt affect both?

**Method:** For each (article, target, judge, condition, bias_type),
code source_present (judge's verification view) and summary_present
(custom_score ≥ threshold). Fit GEE-logit `summary_present ~
condition × target + judge`, clustered on article_id.

Conditions:
- `baseline`: minimal — no JSON schema constraints, no framing rules
- `ablation`: JSON schema + length constraints, no framing rules
- `full`: schema + 'objective, neutral tone, do not adopt framing'

### Threshold ≥ 5  (summary score ≥ 5 = present)

**Per-cell absorption rates** (% source bias preserved):

| Target × Judge | baseline | ablation | full |
|---|---:|---:|---:|
| sonnet × opus | 27.8% | 25.1% | 11.2% |
| sonnet × gpt5 | 9.8% | 11.3% | 2.5% |
| gpt × opus | 25.3% | 24.4% | 6.5% |
| gpt × gpt5 | 11.7% | 9.2% | 1.1% |

**Per-cell generation rates** (% summary-bias not in source):

| Target × Judge | baseline | ablation | full |
|---|---:|---:|---:|
| sonnet × opus | 40.7% | 32.9% | 34.2% |
| sonnet × gpt5 | 58.1% | 48.1% | 65.4% |
| gpt × opus | 40.8% | 37.4% | 27.5% |
| gpt × gpt5 | 48.2% | 48.5% | 33.3% |

**Combined GEE-logit (condition × target + judge), threshold ≥ 5:**

| Outcome | Effect | OR [95% CI] (p) |
|---|---|---|
| Absorbed | source_present=1 | Removing framing rule (full → ablation) | **3.13** [2.06, 4.74] (p=0.000) |
| Absorbed | source_present=1 | Removing schema + framing (full → baseline) | **3.30** [2.12, 5.15] (p=0.000) |
| Absorbed | source_present=1 | GPT-4.1 vs Sonnet (at full) | **0.52** [0.29, 0.92] (p=0.025) |
| Absorbed | source_present=1 | GPT-5 vs Opus (judge calibration) | **0.31** [0.22, 0.43] (p=0.000) |
| Absorbed | source_present=1 | Ablation × GPT-4.1 (instruction sensitivity) | 1.75 [0.93, 3.31] (p=0.084) |
| Absorbed | source_present=1 | Baseline × GPT-4.1 | **1.86** [1.07, 3.23] (p=0.028) |
| Generated | source_present=0 | Removing framing rule (full → ablation) | **2.17** [1.60, 2.94] (p=0.000) |
| Generated | source_present=0 | Removing schema + framing (full → baseline) | **3.21** [2.33, 4.43] (p=0.000) |
| Generated | source_present=0 | GPT-4.1 vs Sonnet (at full) | **0.31** [0.18, 0.54] (p=0.000) |
| Generated | source_present=0 | GPT-5 vs Opus (judge calibration) | **0.47** [0.36, 0.63] (p=0.000) |
| Generated | source_present=0 | Ablation × GPT-4.1 (instruction sensitivity) | **3.31** [1.91, 5.73] (p=0.000) |
| Generated | source_present=0 | Baseline × GPT-4.1 | **2.75** [1.63, 4.64] (p=0.000) |

### Threshold ≥ 3  (summary score ≥ 3 = present)

**Per-cell absorption rates** (% source bias preserved):

| Target × Judge | baseline | ablation | full |
|---|---:|---:|---:|
| sonnet × opus | 73.3% | 75.6% | 61.4% |
| sonnet × gpt5 | 39.4% | 35.8% | 20.1% |
| gpt × opus | 71.5% | 80.5% | 49.1% |
| gpt × gpt5 | 35.1% | 37.2% | 12.0% |

**Per-cell generation rates** (% summary-bias not in source):

| Target × Judge | baseline | ablation | full |
|---|---:|---:|---:|
| sonnet × opus | 47.8% | 47.8% | 44.6% |
| sonnet × gpt5 | 55.2% | 55.9% | 57.3% |
| gpt × opus | 50.6% | 49.3% | 45.9% |
| gpt × gpt5 | 56.9% | 54.9% | 56.0% |

**Combined GEE-logit (condition × target + judge), threshold ≥ 3:**

| Outcome | Effect | OR [95% CI] (p) |
|---|---|---|
| Absorbed | source_present=1 | Removing framing rule (full → ablation) | **2.04** [1.56, 2.68] (p=0.000) |
| Absorbed | source_present=1 | Removing schema + framing (full → baseline) | **2.07** [1.58, 2.72] (p=0.000) |
| Absorbed | source_present=1 | GPT-4.1 vs Sonnet (at full) | **0.59** [0.44, 0.79] (p=0.000) |
| Absorbed | source_present=1 | GPT-5 vs Opus (judge calibration) | **0.18** [0.15, 0.23] (p=0.000) |
| Absorbed | source_present=1 | Ablation × GPT-4.1 (instruction sensitivity) | **1.98** [1.29, 3.02] (p=0.002) |
| Absorbed | source_present=1 | Baseline × GPT-4.1 | **1.47** [1.01, 2.12] (p=0.044) |
| Generated | source_present=0 | Removing framing rule (full → ablation) | **1.76** [1.47, 2.11] (p=0.000) |
| Generated | source_present=0 | Removing schema + framing (full → baseline) | **1.78** [1.48, 2.14] (p=0.000) |
| Generated | source_present=0 | GPT-4.1 vs Sonnet (at full) | **0.70** [0.56, 0.87] (p=0.002) |
| Generated | source_present=0 | GPT-5 vs Opus (judge calibration) | **0.30** [0.26, 0.36] (p=0.000) |
| Generated | source_present=0 | Ablation × GPT-4.1 (instruction sensitivity) | **1.63** [1.27, 2.10] (p=0.000) |
| Generated | source_present=0 | Baseline × GPT-4.1 | **1.52** [1.21, 1.91] (p=0.000) |

### Headline findings — the neutrality instruction *causes* the stripping

1. **Removing 'be neutral, do not adopt framing' triples absorption rate.**
   At threshold ≥ 5, absorption goes from ~6–11% (full) to ~25–28% (baseline)
   on the Opus judge. Combined LMM: removing framing rule OR ≈ 3.1 (p<0.001).

2. **The 'GPT-4.1 less biased than Sonnet' finding is largely instruction-
   driven.** Under `full` (with neutrality instruction): GPT-4.1 absorbs 6.5%
   vs Sonnet 11.2%. Under `baseline` (no instruction): GPT-4.1 absorbs 25.3%
   vs Sonnet 27.8%. The targets converge to within 2.5pp of each other.

3. **JSON schema/structure has near-zero effect.** baseline OR ≈ ablation OR
   (~3.1–3.3) — the active ingredient is the framing-rule sentence, not the
   structural constraints.

4. **Generation also tracks instruction.** Removing the neutrality rule
   roughly doubles generation odds. The instruction restrains *both* sources
   of bias — including the model's own. Pure-fidelity scoring (high absorption,
   low generation) is NOT achieved by either condition.

5. **Significant baseline_x_target interaction** for generation (OR ≈ 2.75)
   means GPT-4.1 is *more responsive* to instruction removal than Sonnet —
   ratifying the interpretation that the original target-effect was
   instruction-followability, not capability.

**Implication for the paper.** The Eval B pre-registered finding
(GPT-4.1 BPS < Sonnet BPS, p_FDR=0.0003) is real *under explicit neutrality
instructions* — but it doesn't generalize to natural deployment, where users
don't say 'be neutral.' The deeper finding is that *neutrality instructions
themselves cause the stripping behavior media-studies critics warn about*.

## Exploratory — Attribution-Rule Effect on Detection Direction (NF-1 extension)

**Question:** Does removing the attribution rule (Eval A baseline vs
ablation vs full) asymmetrically increase flagging of one political
direction over the other?

**Method:** Apply the political lexicon to detections from all 3
conditions. Fit GEE-logit `is_{left,right}_coded ~ condition × target
+ lean_ordinal`, clustered on article_id.

**Detection counts:** total = 2107

| Condition × target | N detections |
|--------------------|-------------:|
| ablation × gpt | 348 |
| ablation × sonnet | 317 |
| baseline × gpt | 337 |
| baseline × sonnet | 459 |
| full × gpt | 323 |
| full × sonnet | 323 |

**Pooled GEE-logit (both targets, condition × target):**

| Outcome | Effect | OR [95% CI] (p) |
|---------|--------|----------------|
| is_left_coded | ablation_main | 1.16 [0.85, 1.58] (p=0.340) |
| is_left_coded | baseline_main | 0.77 [0.34, 1.72] (p=0.521) |
| is_left_coded | target_main | 0.98 [0.51, 1.86] (p=0.944) |
| is_left_coded | lean_main | **0.65** [0.43, 0.99] (p=0.042) |
| is_left_coded | ablation_x_target | 0.72 [0.26, 2.02] (p=0.531) |
| is_left_coded | baseline_x_target | 0.74 [0.25, 2.19] (p=0.583) |
| is_right_coded | ablation_main | 0.96 [0.59, 1.56] (p=0.875) |
| is_right_coded | baseline_main | 0.80 [0.39, 1.65] (p=0.546) |
| is_right_coded | target_main | 1.22 [0.64, 2.33] (p=0.546) |
| is_right_coded | lean_main | **1.78** [1.11, 2.86] (p=0.016) |
| is_right_coded | ablation_x_target | 0.94 [0.47, 1.89] (p=0.864) |
| is_right_coded | baseline_x_target | 1.25 [0.50, 3.08] (p=0.635) |

**Findings:**

1. **No detected attribution-rule × direction asymmetry.** Neither
   condition main effects nor condition × target interactions are
   significant on either directional outcome. Removing the rule
   does not asymmetrically expand flagging by political direction.

2. **Lean main effect replicates NF-1.** Right-coded flag rate
   scales with article right-leaningness (OR ≈ 1.78, p = 0.016);
   left-coded flag rate scales inversely (OR ≈ 0.65, p = 0.042) —
   articles' actual lean drives directional flag distribution as
   expected.

3. **Power-limited null.** Total directional flags across all 3
   conditions = ~95 (left + right + both). Same lexicon-coverage
   limitation as NF-1; LLM-classifier follow-up (NF-1B) remains the
   recommended robustness check.

## Inter-judge reliability

### BPS Krippendorff's α (ordinal) and Pearson r — per eval

| Eval | N pairs | α [95% CI] | r [95% CI] (p) |
|------|--------:|-----------:|---------------:|
| A | 166 | 0.27 [0.13, 0.39] | 0.46 [0.33, 0.57] (p=4.97e-10) |
| B | 189 | -0.17 [-0.32, -0.04] | 0.57 [0.46, 0.66] (p=2.08e-17) |
| C | 188 | 0.50 [0.39, 0.58] | 0.62 [0.53, 0.70] (p=1.41e-21) |

### Detection-verdict agreement (paired across judges)

- N paired detections: **663**
- 4-class Cohen's κ: **0.07** [0.03, 0.11]
- Binary Cohen's κ: **0.36** [0.24, 0.47]
- Binary raw agreement: **90%**
