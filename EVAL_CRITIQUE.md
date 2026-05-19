# Eval Construct-Validity Critique & Improvement Roadmap

> **Living document.** Update on any of: rubric change, new analysis added,
> finding promoted from "proposed" → "implemented." Append to changelog at
> bottom with date + one-line summary. Status table at top is the dashboard.
>
> **Scope.** Construct-validity audit of prompts and rubrics in `eval-{a,b,c}/`,
> verification stage in `verify-*.txt`, and article-rating stage in
> `rate-article-*.txt`. Companion to `PRE_REGISTRATION.md` (which freezes
> confirmatory hypotheses) and `stats_report.md` (which holds current results).

**Last updated:** 2026-05-07 (NF-1, NF-2, NF-3 implemented; corpus enrichment done)
**Maintainer:** Arman Irani

---

## Status dashboard

### Construct-validity issues

| ID | Issue | Severity | Status |
|----|-------|:--------:|:------:|
| CV-A1 | Eval A BPS conflates detection ability with attribution-rule compliance | High | open |
| CV-A2 | "Be cautious — fewer, confident examples" prompt biases precision-recall | Medium | open |
| CV-A3 | No actual P/R/F1 computed despite verdicts existing | High | **implemented (NF-2)** |
| CV-A4 | No sentinel/floor articles to anchor BPS | Medium | open |
| CV-B1 | Absorption/Generation framework specified in seed.yaml but never computed | High | **implemented (NF-3)** |
| CV-B2 | 14 Eval-B custom dimensions overlap; no factor analysis | Medium | open |
| CV-B3 | Source-bias level not used as covariate in BPS analyses | Medium | partial (figure only) |
| CV-B4 | Behavior name `framing-inheritance` ignores 4 other behaviors in `behaviors.json` | Low | open |
| CV-C1 | Three concurrent ground truths, no triangulation | High | open |
| CV-C2 | 5-class accuracy ignores ordinal distance | Medium | open |
| CV-C3 | `confidence_calibration` judged by LLM despite raw confidence values existing | High | open |
| CV-C4 | Centrist compression untested formally | Medium | open |
| CV-C5 | AllSides ideological markers embed a particular ideological framing | Low | acknowledged |
| CR-1 | Verifier-judge circularity (Opus = judge + ground-truth + verifier) | High | acknowledged |
| CR-2 | `num_reps: 3` in seed.yaml but only 1 rollout per cell — no within-target variance | Medium | open |
| CR-3 | baseline/ablation/full conditions confound multiple variables simultaneously | Medium | mitigated (full only) |
| CR-4 | No human-annotated calibration set | High | open |

### Novel findings — achievable on existing data (no new API calls)

| ID | Finding | Effort (hrs) | Status |
|----|---------|:------:|:------:|
| NF-1 | Bias-direction asymmetry within targets (LEFT/RIGHT marker tagging) | 4 | **implemented** ([results](stats_report.md#exploratory--bias-direction-asymmetry-nf-1)) — lexicon-classifier follow-up open |
| NF-2 | Per-article precision/recall/F1 from verification verdicts | 2 | **implemented** ([results](stats_report.md#exploratory--detection-precision--recall--f1)) |
| NF-3 | Absorption vs Generation decomposition (Eval B × Eval A) | 3 | **implemented** ([results](stats_report.md#exploratory--absorption-vs-generation-decomposition-nf-3)) |
| NF-4 | Confidence calibration (Brier, ECE, reliability diagram) for Eval C | 2 | proposed |
| NF-5 | Centrist compression coefficient test | 1 | proposed |
| NF-6 | Quote-trap success rate (programmatic attribution-rule check) | 3 | proposed |
| NF-7 | Key-indicator groundedness check (substring match in source) | 2 | proposed |
| NF-8 | Article-length confounds: FPR ~ token-count | 1 | proposed |
| NF-9 | Per-source-type performance (news/opinion/investigative) | 2 | proposed |
| NF-10 | Bias-type co-occurrence matrices per target | 1 | proposed |

### Tier 2 — modest re-analysis

| ID | Finding | Effort | Status |
|----|---------|:------:|:------:|
| NF-11 | Factor analysis on 14 Eval-B custom_scores | 3h | proposed |
| NF-12 | Ordinal MAE on Eval C lean prediction | 0.5h | proposed |
| NF-13 | Triangulation across three Eval-C ground truths | 2h | proposed |
| NF-14 | Within-model variance from `num_reps: 3` (partial re-run) | 4h + ~$10 | proposed |

### Tier 3 — new experiments

| ID | Finding | Cost | Status |
|----|---------|:------:|:------:|
| NF-15 | Sentinel articles (10 clean + 10 biased + 10 adversarial) | 4h + ~$20 | proposed |
| NF-16 | Human-rater calibration set (3 raters × 50 articles) | recruitment + ~$500 | proposed |
| NF-17 | Counterfactual paraphrase robustness | 6h + ~$30 | proposed |
| NF-18 | Add Gemini and/or Llama as judge AND target | full re-run | proposed |

---

## Issue details

### Eval A — Bias Spotting

#### CV-A1 — Construct drift between behavior and rubric *(High)*
`behaviors.json` defines bias-spotting-quality as detection accuracy. The four
`custom_qualities` in `seed.yaml` weight attribution-rule compliance,
false-positives, false-negatives, and bias-type accuracy roughly equally. Two
distinct constructs (detection ability + format compliance) are compressed
into one BPS. A model that perfectly detects bias but violates the attribution
rule once is dragged the same as a model that misses real bias.

**Fix:** Compute attribution-rule violation as a *separate* binary outcome.
Report it adjacent to BPS, not folded in.

#### CV-A2 — Built-in conservativeness bias *(Medium)*
The "full" prompt instructs *"Be cautious — present fewer, confident examples
rather than more uncertain ones."* This biases the precision-recall trade-off
toward precision *in the system prompt itself*, while `false_positive_rate`
rewards exactly that behavior and `false_negative_rate` punishes the cost.
Net effect: the rubric punishes both sides while the prompt tilts you toward
one.

**Fix:** Either remove the conservativeness instruction, or add a recall-only
condition for fair comparison.

#### CV-A3 — No P/R/F1 anywhere *(High)*
Detection-level verdicts (`confirmed`, `plausible`, `unsupported`,
`hallucinated`) and `*_false_negatives` already exist in
`results/verification/stage2/`. Yet nothing computes per-article
`precision = TP/(TP+FP)`, `recall = TP/(TP+FN)`, `F1`. Judges' 1–10 gestalt
scores are noisier than the verdicts they themselves produced. **See NF-2.**

#### CV-A4 — No sentinel/floor articles *(Medium)*
Without articles known to have *zero* author-level bias and articles known
to have *severe* bias, BPS = 4 could mean "model is bad" or "article is
hard." **See NF-15.**

### Eval B — Susceptibility

#### CV-B1 — Absorption/Generation framework not implemented *(High)*
`eval-b-susceptibility/seed.yaml:12–19` explicitly distinguishes:
- **ABSORPTION** = bias present in source AND in summary
- **GENERATION** = bias present in summary, NOT in source

This is the single most interesting analytic frame available — it cleanly
separates "does the model parrot the article's bias" from "does the model add
its own bias." It is never computed. The 12 per-bias-type scores in
`seed.yaml` measure presence in the *summary* without conditioning on the
source. **Major missed opportunity. See NF-3.**

#### CV-B2 — 14 dimensions, no factor analysis *(Medium)*
`slant`, `bias_by_omission`, `perspective_completeness`, `framing_neutrality`,
`spin`, `subjective_adjectives`, `word_choice` etc. measure overlapping
constructs. With N=95 × 2 × 2 = 380 cells × 14 = 5,320 individual scores you
have a lot of redundant data and zero validity check. **See NF-11.**

#### CV-B3 — No fidelity normalization *(Medium)*
A model summarizing the New York Post should be expected to produce a more
biased summary than one summarizing Reuters. Current BPS doesn't condition on
source bias level. `fidelity.py` figure does this informally; not in any LMM.

**Fix:** Add `source_bias_level` (from Eval A detection count) as a covariate
to LMM 1 for Eval B.

#### CV-B4 — Naming inconsistency *(Low)*
`behaviors.json` lists 5 distinct behaviors but only `framing-inheritance` is
implemented. The other 4 (`slant-inheritance`, `omission-bias-inheritance`,
`sensationalism-amplification`, `key-facts-political-selection`) are described
but not separately operationalized.

### Eval C — Lean Classification

#### CV-C1 — Three concurrent ground truths, never compared *(High)*
- AllSides outlet lean (coarse, publisher-level)
- Opus 4.6 article-level rating
- GPT-5 article-level rating
- `labeled_lean` in CSV (article-level, provenance unclear)

LMM 4 uses judge ratings as truth — circular when one judge shares family
with one target. **See NF-13.**

#### CV-C2 — Binary correctness ignores ordinal distance *(Medium)*
"Lean Right" predicted on a "Right" article (1 step off) is treated identically
to "Left" predicted on a "Right" article (4 steps off). **See NF-12.**

#### CV-C3 — Confidence calibration judged by LLM despite raw values existing *(High)*
Each Eval C target output has `parsed_output.confidence ∈ [0, 1]`. We can
compute Brier scores, expected calibration error, reliability diagrams
*directly*. The current `confidence_calibration` rubric has a judge guess
whether confidence "feels" calibrated. **See NF-4.**

#### CV-C4 — Centrist compression untested *(Medium)*
Models likely pull predictions toward Center. The `centrist_compression.py`
figure exists but no inferential test on the compression coefficient. **See
NF-5.**

#### CV-C5 — AllSides ideological markers embed an ideological framing *(Low)*
`rate-article-system.txt:19–46` lists ideological markers (e.g., "concerns
about hate speech" → Left, "fiscal conservatism" → Right). These markers
themselves embed a particular framing of what counts as "left" vs "right."
Models trained on this taxonomy reproduce its boundaries. Acknowledged
limitation; should be cited explicitly in the paper's threats-to-validity
section.

### Cross-cutting

#### CR-1 — Verifier-judge circularity *(High, acknowledged)*
Opus 4.6 is (a) BPS judge in all 3 evals, (b) verification verdict author in
the stage-2 verifier, (c) article-rating ground-truth source for Eval C, (d)
meta-judgment author. Opus's idiosyncrasies propagate everywhere. Mitigation:
GPT-5 plays parallel roles, and inter-judge agreement is reported.

#### CR-2 — No within-target variance *(Medium)*
`seed.yaml` says `num_reps: 3` but only 1 rollout per (article, target,
condition) exists. No data on within-model temperature variance. We cannot
distinguish "Sonnet vs GPT-4.1 differ by 0.4 BPS" from "Sonnet today vs Sonnet
tomorrow differ by 0.4 BPS." **See NF-14.**

#### CR-3 — Conditions confound multiple variables *(Medium, mitigated)*
baseline → ablation → full changes schema strictness + vocabulary +
attribution rule simultaneously. Currently mitigated by analyzing only `full`.

#### CR-4 — No human-annotated calibration set *(High)*
Every comparison currently rests on "LLMs agree with LLMs." **See NF-16.**

---

## Novel findings — detail

### NF-1: Bias-direction asymmetry within targets ✓ implemented (lexicon v1)
**Question:** Are LLMs more critical of one political direction than the
other, holding article lean constant?

**Implemented in:** `analysis/political_lexicon.py` (paired LEFT/RIGHT lexicon),
`analysis/build_long_format.py` (tagging in `df_verdict`),
`analysis/lmm_fits.py:fit_direction_asymmetry()` (GEE-logit models).

**Lexicon (v1):** 45 paired terminology pairs + 45 unpaired LEFT phrases + 55
unpaired RIGHT phrases. Sourced from `rate-article-system.txt` ideological
markers + standard political-science vocabulary. Pairs are matched by concept
(e.g., "undocumented immigrant" / "illegal alien" for the immigration concept).

**Coverage limitation:** Only ~7% of detections (91 of 1326) contain
ideologically-coded vocabulary captured by the v1 lexicon. ~93% flag bias
*mechanisms* (spin verbs, framing, omission patterns) rather than ideology
terminology. Power for the asymmetry test is limited.

**Findings (lexicon v1):**
- **No detectable target asymmetry.** Target-main OR ≈ 1.0–1.1 on both
  `is_left_coded` and `is_right_coded` outcomes (p ≥ 0.80 each).
- **Lean main effect** is significant on `is_right_coded` (OR = 2.31, p = 0.014)
  and directionally correct on `is_left_coded` (OR = 0.64, p = 0.10).
- **No target × article-lean interaction** (p ≥ 0.59 both outcomes).

**Substantive interpretation:** Within the 1,292-detection sample with known
article lean, both targets flag left- and right-coded language at indistinguishable
rates after controlling for article lean. The flagging rate scales with article
lean in the expected direction (right articles → more right-flagging). This
is a *symmetric, well-behaved* picture — but with low power.

**Recommended follow-ups (NF-1B / NF-1C):**
- **NF-1B — LLM-based classifier.** Replace the 7%-coverage lexicon with a
  one-shot LLM classifier (~600 detections × 2 judges × $0.001/call ≈ $5 total).
  Each detection gets classified as left-coded / right-coded / neutral by a
  third-party model (e.g., Gemini, to avoid Anthropic/OpenAI circularity).
  Will likely raise coverage to ~30–50%, sharply increasing power.
- **NF-1C — Bias-mechanism asymmetry.** Even if directional vocabulary is rare,
  *mechanisms* (e.g., calling a left policy "controversial" vs a right policy
  "controversial") could be politically asymmetric. Requires source-article
  context-windowing — significantly more involved.

### NF-2: Per-article P/R/F1 from existing verdicts ✓ implemented
**How to compute:** For each (article, target, judge):
- TP = count(`confirmed`) + count(`plausible`)
- FP = count(`unsupported`) + count(`hallucinated`)
- FN = len(`{sonnet,gpt}_false_negatives`)
- precision = TP/(TP+FP), recall = TP/(TP+FN), F1 = 2PR/(P+R)

**Implemented in:** `analysis/build_long_format.py:build_pr_long()`,
fitted in `analysis/run_all_stats.py` as exploratory (not in pre-reg FDR family).

**Results** (averaged across both judges):
- **Sonnet**: P = 0.883, R = 0.618, F1 = 0.779
- **GPT-4.1**: P = 0.928, R = 0.532, F1 = 0.786

**Key finding:** Targets are identical on F1 (~0.78) but achieve it differently:
- Sonnet: higher recall (β = +0.095, p = 0.017) — catches more bias instances
- GPT-4.1: higher precision (numerically; not significant, β = -0.013, p = 0.65)
- Article-level ICC for precision = **0.51** — half the variance in precision
  is between-article (some articles are just hard); BPS hid this entirely.

**Methodological implication:** F1 is the cleanest cross-target comparison
metric here. Precision and recall in isolation are *judge-bound* — Opus
proposes 3.4 false-negatives per article on average, GPT-5 only 1.0, so a
target's recall depends on which judge scored it. The judge main effect
for recall (β = +0.285, p < 0.001) is much larger than the target effect.

### NF-3: Absorption vs Generation decomposition ✓ implemented (3-arm extension done 2026-05-07)
**Method:** For each (article, target, judge, condition, bias_type):
- `source_present` from judge's verification (confirmed/plausible + false_negatives)
- `summary_present` from Eval B custom_scores ≥ threshold (≥5 primary, ≥3 sensitivity)
- `absorbed` = source ∧ summary; `generated` = ¬source ∧ summary; `resisted` = source ∧ ¬summary
- 3 conditions analyzed: baseline (minimal) / ablation (schema, no framing rules) / full (schema + 'be neutral, do not adopt framing')

**Implemented in:** `analysis/absorption_generation.py`. GEE-logit clustered on article_id.

**Absorption rates (% source bias preserved), threshold ≥ 5:**

| Target × Judge | baseline | ablation | full |
|----------------|---------:|---------:|-----:|
| Sonnet × Opus  | 27.8% | 25.1% | 11.2% |
| GPT-4.1 × Opus | 25.3% | 24.4% |  6.5% |
| Sonnet × GPT-5 |  9.8% | 11.3% |  2.5% |
| GPT-4.1 × GPT-5| 11.7% |  9.2% |  1.1% |

**Combined LMM (threshold ≥ 5):**
- `absorbed | source_present=1`: removing framing rule (full → ablation/baseline) OR = 3.13 (p<0.001), target main OR = 0.52 (p=0.025)
- `generated | source_present=0`: removing framing rule OR = 2.17 (p<0.001), target main OR = 0.31 (p<0.001), baseline × target OR = 2.75 (p<0.001)

**Headline findings — the neutrality instruction *causes* the stripping:**
1. **The "be neutral, do not adopt framing" instruction triples absorption suppression.** Removing it more than doubles fidelity from ~7–11% to ~25–28% (Opus judge).
2. **The "GPT-4.1 less biased than Sonnet" finding is largely instruction-driven.** Under `full` (with neutrality instruction) the targets differ; under `baseline` they converge to within 2.5pp.
3. **JSON schema/structure has near-zero effect.** baseline ≈ ablation, only the framing-rule sentence matters.
4. **Generation also tracks instruction.** Removing the rule roughly doubles generation odds — the instruction restrains both source-derived AND model-introduced bias.
5. **Significant baseline × target interaction.** GPT-4.1 is more responsive to instruction removal than Sonnet — confirming the original target-effect was instruction-followability, not capability.

**Implication for the paper.** The pre-registered Eval B finding (GPT-4.1 BPS < Sonnet BPS, p_FDR=0.0003) is real *under explicit neutrality instructions* but doesn't generalize to deployment, where users don't say "be neutral." The deeper finding: *neutrality instructions themselves cause the stripping behavior the media-studies critique (Lakoff 1996, Entman 2007, Boykoff 2004) warns about*.

### NF-4: Confidence calibration
**How to compute:** Per target on Eval C:
- Brier = mean((confidence − lean_correct)²)
- ECE: bin confidence into 10 buckets; ECE = Σ |bin_acc − bin_mean_conf| × bin_weight
- Reliability diagram

**Likely surprise:** One target probably overclaims confidence on
misclassifications.

### NF-5: Centrist compression
**How to compute:** Encode lean as ordinal (Left=−2, Lean Left=−1, Center=0,
Lean Right=+1, Right=+2). Per target: regress `predicted_ordinal ~
truth_ordinal`. Slope of 1.0 = perfect calibration; <1.0 = compression toward
center. Compare slopes between Sonnet and GPT-4.1 with cluster bootstrap.

### NF-6: Quote-trap success rate
**How to compute:** For each detection, check whether `biasedText` is a
substring of any quoted span in the source article (regex `"[^"]+"` or
attributed-source patterns). Per target: % of detections that violate the
attribution rule. Per condition (baseline/ablation/full).

### NF-7: Key-indicator groundedness
**How to compute:** For each Eval C output, target produces `key_indicators:
[...]`. Per indicator: substring match in source article text. Per target:
fraction of indicators actually grounded in source.

### NF-8: Article-length confounds
**How to compute:** Token-count each article; regress detection count on
length per target. Test FPR ~ length.

### NF-9: Per-source-type performance
**How to compute:** Group by article source-type (news/opinion/investigative —
derivable from `article_meta.source` + AllSides metadata). Test target ×
source_type interaction in BPS.

### NF-10: Bias-type co-occurrence
**How to compute:** Per target, build 12×12 matrix of bias types co-occurring
within the same article. Compare matrices (Frobenius distance, or cell-wise
log-odds).

### NF-11: Factor analysis on Eval-B custom_scores
**How to compute:** Stack 380 × 14 score matrix. Run PCA / EFA. If 14
dimensions collapse to 3–4 factors, drop redundant rubric items.

### NF-12: Ordinal MAE
**How to compute:** Replace binary `lean_correct` with `|predicted_ordinal −
truth_ordinal|`. Re-fit LMM 4 with this richer outcome.

### NF-13: Triangulation across ground truths
**How to compute:** Fit three parallel LMM 4's — AllSides label, Opus rating,
GPT-5 rating as truth. Compare estimates of target effect.

### NF-14: Within-model variance from `num_reps`
**How to compute:** Re-run one eval × one condition × ~30 articles × 3 reps.
Estimate within-model SD; compare to between-target SD.

### NF-15: Sentinel articles
**Materials:**
- 10 clean sentinels: AP wire / Reuters / sports / weather
- 10 biased sentinels: clearly partisan op-eds (Breitbart, Mother Jones)
- 10 adversarial sentinels: news articles with extensive quotes from
  extreme partisan figures (testing attribution-rule)

**Run:** Same pipeline. Anchors interpretation.

### NF-16: Human-rater calibration set
**Design:** 50 articles, 3 raters (journalism / political-science backgrounds).
Annotate per article: bias presence (binary), bias instances (free-form),
lean class (5-class), explanation quality (1–5). Compute Krippendorff's α
among humans. Anchor LLM judges to human consensus.

### NF-17: Counterfactual paraphrase robustness
**Design:** Take 30 Eval-C articles. Paraphrase via separate model
(GPT-4.1 or Gemini) preserving content. Re-run pipeline. Does lean class
flip? Compute flip rate per target.

### NF-18: Adding judges and targets
**Design:** Gemini 2.5 Pro / Llama 3.3 405B as both judge and target. Lets you
separate "model" effects from "family" effects with degrees of freedom.

---

## Recommended modification priority

| Priority | Change | Cost | Payoff |
|---|---|:---:|:---:|
| P1 | NF-3 — Absorption/Generation decomposition | 3h | Major novel finding |
| P2 | NF-2 — P/R/F1 from existing verdicts | 2h | Replaces gestalt with hard numbers |
| P3 | NF-1 — Bias-direction asymmetry | 4h | Likely flagship paper finding |
| P4 | NF-4 — Confidence calibration (Brier/ECE) | 2h | Standard ML calibration; cheap, novel-here |
| P5 | NF-5 — Centrist compression | 1h | Single significant number |
| P6 | NF-15 — Sentinel articles | 4h + ~$20 | Cheapest ground truth available |
| P7 | NF-12 — Ordinal MAE on Eval C | 0.5h | Free power gain |
| P8 | NF-6 — Quote-trap success rate | 3h | Tests prompt's most distinctive instruction |

Items P1–P5 and P7–P8 cost zero new API calls.

---

## What this paper *could* be claiming after improvements

Currently: "Sonnet vs GPT-4.1, BPS comparisons, judge agreement."

After P1–P8:
1. **"LLMs as bias detectors exhibit detectable political asymmetry"** (NF-1)
2. **"Bias absorption ≠ bias generation"** as separable behavioral dimensions (NF-3)
3. **"Lean-classification confidence is uncalibrated, with consistent direction across families"** (NF-4)
4. **"Cross-family family favoritism is task-specific and largest where ambiguity is highest"** (already supported)
5. **"Models systematically compress lean predictions toward Center"** (NF-5)
6. **"Attribution-rule compliance varies between families and conditions"** (NF-6)

That's a real paper.

---

## Changelog

| Date | Change | By |
|------|--------|----|
| 2026-04-28 | Initial document. Construct-validity audit, 18 novel findings catalogued, priority ranking established. | Claude |
| 2026-04-28 | **NF-2 implemented**: per-article P/R/F1 from verification verdicts. New `df_pr` Parquet, three exploratory LMMs (precision/recall/F1) added to `stats_report.md`. Key finding: Sonnet & GPT-4.1 have identical F1 (~0.78) but differ on the precision-recall axis — Sonnet has higher recall (p=0.017), GPT-4.1 numerically higher precision. CV-A3 closed. | Claude |
| 2026-04-28 | **NF-1 implemented (lexicon v1)**: paired LEFT/RIGHT political lexicon, GEE-logit asymmetry models. Substantive null: no target asymmetry (target OR ≈ 1.0, p ≥ 0.80 on both directions). Both targets flag ideological vocabulary at rates that scale with article lean in the expected direction. **Limitation**: lexicon captures only 7% of detections — bias-mechanism vocabulary (spin verbs, framing) dominates. Follow-up NF-1B (LLM-based classifier, ~$5 of API) opened. | Claude |
| 2026-05-07 | **10K corpus enrichment** complete. Curated 10,000 articles from PROD.db (articles + backup7), stratified by lean × density-tier × source-table with outlet-diversity caps. Lean labels parsed from existing GPT-4o (validated κ=0.59 vs Opus). Topic labels via sentence-transformer cosine similarity to 18 topic prototypes. Output: `data/articles_enriched.parquet` (50 MB). 72.6% political articles, well-distributed across lean × topic. | Claude |
| 2026-05-07 | **NF-3 implemented**: Absorption/Generation decomposition for Eval B. GEE-logit models show GPT-4.1 less susceptible on both dimensions (absorption OR=0.53, p=0.037; generation OR=0.42, p=0.004 at threshold ≥ 5). Generation > absorption when summary bias is clearly present (5–10× ratio). ~90% resistance overall. CV-B1 closed. | Claude |
| 2026-05-07 | **NF-1 extended to 3-condition analysis** (baseline/ablation/full). Substantive null: removing the attribution rule does NOT asymmetrically increase flagging by political direction (all condition main and condition × target effects p > 0.30). Lean main effect replicates (right-coded flag rate scales with article right-leaningness). Power-limited as in v1 (~95 directional flags total). | Claude |
| 2026-05-07 | **NF-3 extended to 3-arm condition analysis** (baseline/ablation/full Eval B). MAJOR FINDING: the "be neutral, do not adopt framing" instruction triples absorption suppression and doubles generation suppression. The pre-registered Eval B target-effect (GPT-4.1 BPS < Sonnet BPS) is largely *instruction-following* — under baseline (no framing rule), the targets converge to within 2.5pp on absorption rate. Reframes the paper: neutrality instructions cause the stripping behavior media-studies critics (Lakoff/Entman/Boykoff) warn about. | Claude |
