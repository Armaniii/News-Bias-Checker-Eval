# Pre-Registration — Cross-Family LLM Bias Evaluation

**v1 date locked:** 2026-04-28
**v2 date locked:** 2026-05-10 (extends v1; v1 results unchanged)
**v3 date locked:** 2026-05-11 (extends v1+v2; cross-text-type generalization)
**Path B amendment locked:** 2026-05-18 (Paper 1 scope contraction; see §6.7)
**Author:** Arman Irani
**Status:**
- **v1** (sections 1-6): Confirmatory analyses specified before fitting LMMs 2-4. LMM 1 (per-eval BPS) was fit before this document was finalized; its results are reported as post-hoc confirmatory with the specific contrast and direction documented here matching the prior unsupported claim in `inter_judge_agreement.md`.
- **v2** (section 6.5, added 2026-05-10): Extension to v1 covering (a) per-factor absorption decomposition on existing data, (b) 4-arm mechanism dissection design replacing v1's 3-arm Eval B design for primary analysis, (c) directive × factor interaction tests, (d) replication of EP × CFI dissociation under new design. v1 results are not re-tested under v2; v2 family extends v1's BH-FDR correction from 12 to 20 tests.
- **v3** (section 6.6, added 2026-05-11; revised 2026-04-29): Extension covering (a) cross-text-type generalization via Voice Adoption Rate (VAR — Eval A explanations) and Frame-Distance Coding (FDC — Eval C reasoning), with Stage 1 LLM-judge tests on existing rollout text (~$40, no new rollouts) and Stage 2 reframing-arm REPLACES `ablation` in Eval A and Eval C (~$70-100) — design change documented in §6.6.3 with rationale; (b) vocabulary × directive 2×2 factorial design for Eval A (~$130-180) testing whether bias-type definitions vs bare-name vocabulary changes detection accuracy and diversity (§6.6.9, H36-H39). v3 family extends BH-FDR correction; see §6.6.10 for explicit family-membership accounting.

- **Paper 1 scope (2026-04-29):** Paper 1 final analysis is conducted exclusively on the N=200 v3 clean-input corpus. The v1+v2 corpus (N=95, with HEADLINE+SOURCE in the user message) is superseded by the clean-input rollouts and is not analyzed in Paper 1. v1+v2 hypotheses (H1-H20) and the source-prior leakage calibration (formerly §6.6.8, H33-H35) are deprecated for Paper 1 scope. v1+v2 hypotheses remain pre-registered as historical record but are not in the Paper 1 BH-FDR family.

---

## 1. Study design (frozen)

### 1.1 Targets, judges, evals
- **Target models** (responses being judged): Claude Sonnet 4.5, GPT-4.1
- **Judge models** (scoring the responses): Claude Sonnet 4.6, GPT-5 (revised 2026-05-18 — Path B; prior v1 architecture used Opus 4.6 as the Anthropic judge. v1 historical results not re-judged. Paper 1 v3 rollouts judged under the revised pair: each judge is the next-generation version of its same-family target, preserving cross-family favoritism measurability while tier-matching judge ≈ target+1-generation. Phase 2 G third BPS judge: Gemini 2.5 Pro.)
- **Evals**: A (bias detection), B (summarization susceptibility), C (lean classification)
- **Conditions analyzed**: `full` only (baseline and ablation are exploratory)
- **Articles**: 100 sampled from AllSides-labeled corpus, **5 excluded** for corruption
  (`article_24346`, `article_42780`, `article_51657`, `article_37862`, `article_28565`)
- **N analyzed**: 95 articles. Complete cells per (eval × target × judge): 95 articles when
  both judges scored that cell. GPT-5 has 24 missing Eval A judgments due to a known
  upstream batch-API issue; missing-at-random is assumed for primary analyses.

### 1.2 Data exclusions and missing data
- The 5 corrupted article IDs are excluded from all analyses.
- Missing observations from the GPT-5 / Eval A cells (≈12% of that cell) are assumed
  missing at random, conditional on article. Mixed-effects and OLS-with-cluster-robust-SE
  estimators handle unbalanced cells natively. No imputation is performed.

### 1.3 Behavior Presence Score (BPS) scale
1–10 integer, where **1 = no failure** and **10 = systematic, severe failures**.
**Lower is better.** Direction matters for hypothesis interpretation below.

---

## 2. Confirmatory hypotheses

The contrasts below define the **family of primary tests** for FDR correction. All
hypotheses are two-sided unless explicitly noted. Estimators clustered on `article_id`.

| ID | Hypothesis | Primary contrast | Eval / outcome | Test |
|----|------------|------------------|----------------|------|
| H1 | Family-favoritism interaction in Eval C | `target × judge` interaction = 0 | LMM 1 / BPS | LMM or OLS+CR |
| H2 | Family-favoritism interaction in Eval A | `target × judge` interaction = 0 | LMM 1 / BPS | LMM or OLS+CR |
| H3 | Family-favoritism interaction in Eval B | `target × judge` interaction = 0 | LMM 1 / BPS | LMM or OLS+CR |
| H4 | Eval B target main effect | `target_gpt − target_sonnet` = 0 | LMM 1 / BPS | LMM or OLS+CR |
| H5 | Eval A target main effect | `target_gpt − target_sonnet` = 0 | LMM 1 / BPS | LMM or OLS+CR |
| H6 | Eval C target main effect | `target_gpt − target_sonnet` = 0 | LMM 1 / BPS | LMM or OLS+CR |
| H7 | Explanation-quality target effect | `target_gpt − target_sonnet` = 0 | LMM 2 / meta_judgment.explanation_quality | LMM |
| H8 | Explanation-quality favoritism | `target × judge` interaction = 0 | LMM 2 / meta_judgment.explanation_quality | LMM |
| H9 | Detection-validity target effect | `target_gpt − target_sonnet` = 0 (logit) | LMM 3 / verdict_valid (binary) | GLMM binomial or logistic + cluster-robust |
| H10 | Detection-validity favoritism | `target × judge` interaction = 0 (logit) | LMM 3 / verdict_valid | GLMM or logistic + cluster-robust |
| H11 | Lean-classification accuracy target effect | `target_gpt − target_sonnet` = 0 (logit) | LMM 4 / lean_correct (binary) | Logistic + cluster-robust on article |
| H12 | Lean-classification accuracy favoritism | `target × judge_truth` interaction = 0 (logit) | LMM 4 / lean_correct using each judge's article rating as ground truth | Logistic + cluster-robust |

**Family size: 12 tests.**

---

## 3. Statistical methodology

> **SCOPE NOTE (2026-05-21): §§3.1–3.5 below describe the v1 BPS/explanation-quality design** (reference level `opus`, 12 primary BPS tests, BPS-unit sanity checks). They are **historical / v1-only** and are NOT the Paper-1 statistical specification. The Paper-1 (Path-B) confirmatory family is the 8 tests in §6.6.10, with estimators, reference levels, comparators, and equivalence mechanics specified there and in §6.6.11. Reference levels for Paper 1: `target` → `sonnet-4-5` reference (coeff = `gpt-4.1 − sonnet`); `source_lean` → `LEFT` reference; `condition`/`arm` → `ablation` reference for the directive contrasts (H27/H27b/H28/H29). Per-outcome sanity check for the 8 retained tests: each LMM/GLMM marginal effect is cross-checked against a paired test on judge-averaged outcomes (paired t for continuous VAR-proportion/FDC; McNemar/exact for the binary/label outcomes), agreeing within tolerance or the specification is revisited. The v1 text is retained below for provenance.

### 3.1 Primary estimator selection
For each continuous outcome (BPS, explanation_quality):
1. Fit LMM with random intercept by `article_id`.
2. If random-effect covariance is singular (boundary at zero), fall back to OLS with
   cluster-robust standard errors clustered on `article_id`.
3. Both methods give identical fixed-effect point estimates in the limit; the
   cluster-robust SE is asymptotically valid when ICC ≈ 0.

For binary outcomes (verdict_valid, lean_correct):
1. Logistic regression with cluster-robust SE clustered on `article_id` (primary).
2. Sensitivity analysis with binomial GLMM (Bayes variational) reported in supplement.

### 3.2 Reference levels (frozen)
- `target`: `sonnet` is reference; coefficient is `gpt − sonnet`.
- `judge`: `opus` is reference; coefficient is `gpt5 − opus`.
- `judge_truth` (LMM 4 only): `opus` is reference.

### 3.3 Multiple-comparison correction
**Benjamini-Hochberg FDR at q = 0.05** across the 12 primary tests in §2.
Reported alongside uncorrected p-values for transparency. A confirmatory hypothesis
is declared "supported" only if its BH-corrected p < 0.05.

### 3.4 Effect-size reporting
For BPS / explanation_quality outcomes (1–10 scale), report β with 95% CI in original
units. For binary outcomes, report odds ratio with 95% CI.

### 3.5 Sanity checks
For every continuous LMM, report a paired t-test on judge-averaged outcome as a
sanity check. The LMM marginal target effect (target_main + 0.5 × interaction) must
agree with the paired-t mean difference within 0.15 BPS units; if not, model
specification is revisited.

---

## 4. Reliability metrics (descriptive, not in confirmatory family)

Reported with bootstrap 95% CIs (2000 iterations, resampling articles):
- **Krippendorff's α (ordinal)** for paired BPS scores per eval.
- **Krippendorff's α (ordinal)** for meta_judgment dimensions per dimension.
- **4-class Cohen's κ** + **binary Cohen's κ** for paired detection verdicts.
- **Pearson r with Fisher-z 95% CI** for BPS correlation across judges.

These are descriptive reliability statistics. They are not part of the FDR family.

---

## 5. Exploratory analyses (not in confirmatory family, separately labeled)

The following are exploratory and not subject to family-wise correction:
- Per-bias-type detection validity (e.g., Spin vs Slant vs Word Choice).
- Per-condition (baseline vs ablation vs full) effects.
- Per-meta-judgment-dimension breakdowns beyond explanation_quality.
- Hallucination-rate differences (`unsupported` + `hallucinated` verdicts) between targets and judges.
- Lean-classification confusion-matrix patterns by lean class.
- Sentiment-shift analyses in summaries.

Exploratory results are clearly labeled as such in the final report.

---

## 6. Deviations log

Any deviations from this plan after locking will be appended here with date, change,
and rationale.

| Date | Deviation | Reason |
|------|-----------|--------|
| 2026-05-18 | Path B amendment — pre-data BH-FDR family contraction (13 → 8 tests). Drop H21, H24; defer H36–H39 + D-H38s to Paper 2. See §6.7 for full disclosure. | Paper-strength argument: contraction to a single load-bearing claim (decision–rationalization dissociation with directional signature). Locked before any Stage 2 v3 rollouts collected. |
| 2026-05-18 | Anthropic-side Stage 1 judge revised: Opus 4.6 → Sonnet 4.6. | Judge tier-matched to its same-family target (Sonnet 4.5) + 1 generation, parallel to GPT-4.1 → GPT-5 on the OpenAI side. Cross-family favoritism remains measurable. |
| 2026-05-21 | Terminology correction: the headline finding is a **decision–rationalization dissociation**, not a "chain-of-thought faithfulness gap." The v3 schemas commit the discrete decision before the justifying prose, so the prose is post-hoc rationalization, not CoT. Turpin et al. 2023 is now cited as related work, not as a paradigm directly extended. | Precise reading of the output schemas (`prompts.py`): `biasType` precedes `explanation`, `lean` precedes `reasoning`. |
| 2026-05-21 | Added two descriptive (D-class) CoT robustness arms — `eval-a`/`reframing_cot` and `eval-c`/`reframing_cot` (`prompts.py` v3.3.0). New descriptive hypotheses D-HCoT-A, D-HCoT-C. See §6.6.12. Pre-data; BH-FDR family unchanged at 8. Budget ~$635 → ~$775. | Tests whether the decision–rationalization dissociation survives reasoning-first generation order — directly answers the methodological objection that the finding may be specific to post-hoc generation order. |

---

## 6.5 Pre-registration v2 (locked 2026-05-10) — extensions to v1

**v1 confirmatory findings remain locked.** This section adds new pre-registered hypotheses for analyses being run after v1 was locked. v1 results are not re-tested under v2; only the *new* analyses below are pre-registered v2.

### 6.5.1 Per-factor absorption decomposition (existing data, free)

**Rationale:** Existing v1 data (3-arm baseline/ablation/full × 2 targets × 2 judges × 95 articles) supports a per-factor decomposition not run in v1. The factor analysis (NF-11, post-hoc in v1) revealed three latent factors (F1 structural, F2 epistemic, F3 lexical). We pre-register the prediction that the v1 "full" condition's stripping effect is *factor-selective* — concentrated in F1 (structural) and F3 (lexical), with smaller effects on F2 (epistemic).

**New primary hypotheses (v2 family for FDR):**

| ID | Hypothesis | Test | Predicted direction |
|----|------------|------|---------------------|
| H13 | F1 absorption is suppressed under "full" vs "baseline" | LMM: F1 absorption ~ condition × target + (1\|article) | β(full) negative, p_FDR < 0.05 |
| H14 | F3 absorption is suppressed under "full" vs "baseline" | LMM: F3 absorption ~ condition × target + (1\|article) | β(full) negative, p_FDR < 0.05 |
| H15 | F2 absorption shows smaller suppression than F1 or F3 | Pairwise comparison of effect sizes |\|β(full, F2)\| < \|β(full, F1)\| AND < \|β(full, F3)\| |

These join the v1 family of 12 → v2 family of 15 tests for BH-FDR correction.

**Analysis date:** to be run before reporting; results pre-committed to direction.

### 6.5.2 4-arm mechanism dissection (Eval B; new API calls required)

**Replaces v1's 3-arm Eval B design with 4-arm design** for primary analysis. v1 Eval B data preserved in supplementary materials with the schema-effect null cited.

**New 4-arm design:**

| Arm | Instruction | Tests |
|-----|-------------|-------|
| **minimal** (existing v1 baseline data, reused) | Bare task instruction, no schema | Intrinsic behavior under minimal conditioning |
| **lexical-only** (NEW, requires new API calls) | Schema + word-level neutrality directives only | Lexical-pathway compliance |
| **structural-only** (NEW, requires new API calls) | Schema + frame-level neutrality directives only | Structural-pathway compliance |
| **full** (existing v1 data, reused) | Schema + both lexical and structural directives | Combined directive |

**Pre-registered hypotheses (v2 family):**

| ID | Hypothesis | Test | Predicted direction |
|----|------------|------|---------------------|
| H16 | Lexical-only suppresses F3 absorption more than F1 absorption | LMM: F3 vs F1 absorption rate × condition (lexical-only) | β(lexical-only, F3) more negative than β(lexical-only, F1), p_FDR < 0.05 |
| H17 | Structural-only suppresses F1 absorption more than F3 absorption | LMM: F1 vs F3 absorption rate × condition (structural-only) | β(structural-only, F1) more negative than β(structural-only, F3), p_FDR < 0.05 |
| H18 | (directive type × factor) interaction is significant | LMM: absorption ~ condition × factor + (1\|article) | Interaction term p_FDR < 0.05 |
| H19 | Full ≈ lexical-only + structural-only (additivity test) | Test for non-additivity: β(full) − [β(lexical-only) + β(structural-only)] | If additive: difference ≈ 0; report point estimate with 95% CI |

These join the family for BH-FDR correction. Total family at v2: H1-H12 (v1) + H13-H19 (v2) = 19 tests.

**Bias-type binning for factor mapping (pre-registered a priori per literature):**

Per Feng et al. 2024 content/style decomposition (arXiv:2403.18932) and the post-hoc factor structure from v1 EFA, we pre-register the mapping:

| Factor | Bias types loading on it | Rationale |
|--------|--------------------------|-----------|
| F1 (Structural) | slant, bias_by_omission, elite_populist_bias, negativity_bias | Frame-level / representational bias |
| F2 (Epistemic) | unsubstantiated_claims, opinion_as_fact, mind_reading | Claim-handling / epistemic bias |
| F3 (Lexical) | spin, sensationalism, subjective_adjectives, word_choice, mudslinging | Word-level / lexical bias |

This mapping is used for hypothesis testing in H13-H19. Any post-hoc reassignment of bias types to factors is treated as exploratory and clearly labeled.

### 6.5.3 Engagement Parity × Content Framing Inheritance dissociation (already computed)

**Rationale:** The dissociation finding from `analysis/true_behavior_profile.py` (CCDR(CFI, EP) = 22.6×, r = -0.34, p = 0.51) was computed before this v2 pre-registration. It is therefore **descriptively reported** in v2, not pre-registered.

We pre-register here the prediction that the dissociation **replicates under the new 4-arm design**: CCDR(CFI, EP) ≥ 5× across the new 4 arms.

| ID | Hypothesis | Test | Predicted direction |
|----|------------|------|---------------------|
| H20 | EP × CFI dissociation replicates under 4-arm design | CCDR(CFI, EP) computed across new 4 arms | CCDR ≥ 5× |

Joins the family. Total at v2 lock: 20 tests.

### 6.5.4 Reframing terminology — descriptive contribution (not a hypothesis)

The proposed terminology reframe ("neutrality directive" → "reframing directive") is a descriptive / vocabulary contribution. It is not a hypothesis test. It is grounded in the empirical asymmetry between absorption suppression (~65%) and generation suppression (~40%) under v1 "full" condition, which we report descriptively. No test is pre-registered for this contribution.

---

## 6.6 Pre-registration v3 (locked 2026-05-11) — cross-text-type generalization

**v1 and v2 confirmatory findings remain locked.** This section adds new pre-registered hypotheses for cross-text-type generalization of the framing-inheritance findings. Stage 1 (free LLM-judge analysis on existing data) is locked here; Stage 2 (new reframing-directive arms for Eval A and C) is pre-conditionally locked, conditional on Stage 1 producing meaningful signal.

### 6.6.1 Motivation and theoretical context

The v1 + v2 findings established asymmetric framing-stripping in **Eval B summaries** under reframing directives: right-coded source framing stripped 2–5× more than left-coded. This pre-registration extends the analysis to two additional **text-types** within the existing 3-arm condition design:

1. **Eval A explanation text** (per-detection, ~33 words avg) — the user-facing artifact of LLM bias-detection tools
2. **Eval C reasoning text** (per-classification, ~180 words avg) — the user-facing artifact of LLM lean classifiers

These are deployment-relevant texts: bias-detection tools surface explanations to users (CheckTextBias, Ground.News, BiasLab-style audit tools), and classifier reasoning is read as the substantive justification for label assignments. The framing-inheritance question — does the model preserve or replace source framing in *any* text it produces about the source? — applies uniformly.

### 6.6.2 Stage 1 — VAR and FDC analysis on existing data (no new rollouts)

**Method:** Cross-family judge classification (Sonnet 4.6 + GPT-5, each item scored by both; per-judge labels + inter-judge κ reported — see METHODS §1.5/§1.6/§4.9) of existing Eval A explanation and Eval C reasoning text under all 3 existing conditions (baseline / ablation / full) × 2 targets × 95 articles. No new rollouts; only judge classifications of already-generated text.

**Cost:** ~$70-90 batched for ~6,570 classifications × 2 judges (up from the former ~$30-40 single-Haiku estimate; dual cross-family judging is the circularity guard for the load-bearing VAR/FDC instruments — see §6.7).

**Pre-registered Stage 1 hypotheses (BH-FDR family, joins v1+v2 = 27 total tests):**

| ID | Hypothesis | Test | Predicted direction |
|----|------------|------|---------------------|
| H21 | VAR is higher on RIGHT source articles than LEFT under v1 "full" condition | LMM: VAR_inheriting ~ source_lean for Eval A | β(RIGHT vs LEFT) > 0, p_FDR < 0.05 |
| H22 | VAR is reduced under v1 "full" vs "baseline" (reframing-directive effect) | LMM: VAR_inheriting ~ condition × source_lean for Eval A | β(full vs baseline) < 0, p_FDR < 0.05 |
| H23 | VAR reduction is asymmetric: stronger reduction for RIGHT-source articles than LEFT-source | LMM interaction: condition × source_lean | β(full × RIGHT) < β(full × LEFT), p_FDR < 0.05 |
| H24 | FDC attribution-axis is lower (less attribution discipline) on RIGHT source articles | LMM: FDC_attribution ~ source_lean for Eval C | β(RIGHT vs LEFT) < 0, p_FDR < 0.05 |
| H25 | FDC schema-axis is lower (more schema adoption) on RIGHT source articles | LMM: FDC_schema ~ source_lean for Eval C | β(RIGHT vs LEFT) < 0, p_FDR < 0.05 |
| H26 | Lexicon-based RD on Eval C reasoning replicates Eval B asymmetric stripping | RD on concatenated reasoning + key_indicators, stratified by source-lean | drift(RIGHT) > drift(LEFT), p_FDR < 0.05 |

### 6.6.3 Stage 2 — 4-arm design for Eval A and Eval C (revised 2026-04-29 per Hole 6 resolution)

**Conditional on Stage 1 results.** If Stage 1 shows meaningful framing inheritance under existing conditions (significant VAR > 0, or FDC < 4.0 on the 1-7 scale — i.e. below the neutral midpoint — in any cell), proceed to Stage 2.

**Design change (2026-04-29 — Hole 6 resolution):** Evals A and C use a **4-arm design** (baseline / ablation / reframing / full) on clean-input v3 rollouts. The `ablation` arm is restored from its earlier deprecation — its inclusion enables a clean "directive vs no directive" comparison on v3 clean-input data, which is the central comparison needed for the H27/H27b cross-text-type generalization claim. Prior replacement design (3-arm: baseline / reframing / full) conflated directive type with directive target — the audit's H27 apples-to-oranges concern.

**Eval B remains 3-arm** (baseline / ablation / full). The Eval B `ablation` was already retained; reframing arm in Eval B is not needed because the existing Eval B `full` arm already contains the framing-rule directive that is the heart of the Paper 1 thesis on the long-form text type.

**Eval A 4-arm structure (Stage 2):**

| Arm | Prompt content | Status |
|---|---|---|
| `baseline` | Minimal: "Identify bias in this news article." + JSON schema. No vocabulary, no directives. | Existing v3 |
| `ablation` | Schema + 15-type vocabulary + **NO directive** (no attribution rule, no explanation-reframing directive) | **New (Hole 6 restoration)** |
| `reframing` | Schema + 15-type vocabulary + **L3-broad reframing directive (revised 2026-05-12)**: "When identifying bias, consider how readers across the political spectrum would evaluate the article. Do not editorialize, adopt the article's framing, or use loaded language in your explanations. Represent perspectives proportionally — both in which spans you flag as biased and in how you explain them." | Existing v3 |
| `full` | Schema + 15-type vocabulary + **attribution rule**: "Analyze only the author's own prose — never quoted text or attributed source statements." | Existing v3 |

**Eval C 4-arm structure (Stage 2):**

| Arm | Prompt content | Status |
|---|---|---|
| `baseline` | Minimal: "Classify this article's political lean..." + JSON schema. No scale definitions, no directives. | Existing v3 |
| `ablation` | Schema + scale definitions + confidence calibration anchors + **NO directive** | **New (Hole 6 restoration)** |
| `reframing` | Schema + scale definitions + confidence calibration anchors + **L3-broad reframing directive (revised 2026-05-12)**: "When classifying this article's political lean, consider how readers across the political spectrum would evaluate it. Do not editorialize, adopt the article's framing, or use loaded language in your reasoning. Represent perspectives proportionally — both in the classification itself and in the reasoning." | Existing v3 |
| `full` | Schema + scale definitions + confidence calibration anchors + **attribution rule** (classification based on author's own prose only; key_indicators cite author prose only) | Existing v3 |

**Cost:** ~$105 batched both judges for the two new ablation arms (Eval A new ablation ~$60 + Eval C new ablation ~$45). N=200 v3 program total batched: **~$815** (was $708 in 3-arm; +$105 for restored ablation arms; budget within tolerance).

**Pre-conditionally locked Stage 2 hypotheses (revised wording for Hole 6 resolution):**

| ID | Hypothesis | Test | Predicted direction |
|----|------------|------|---------------------|
| H27 | On Eval A explanations, the `reframing` arm (containing an explanation-targeting reframing directive on the `explanation` field) produces lower VAR_inheriting than the `ablation` arm (schema + vocabulary + caution; NO directive). | LMM: VAR_inheriting ~ arm (reframing vs ablation), paired by article, Eval A | β(reframing vs ablation) < 0, p_FDR < 0.05 |
| H27b | On Eval C reasoning, the `reframing` arm (containing a reasoning-targeting reframing directive on the `reasoning` field) produces lower FDC schema-axis (less schema adoption) than the `ablation` arm (schema + scale definitions + calibration anchors; NO directive). | LMM: FDC_schema ~ arm (reframing vs ablation), paired by article, Eval C | β(reframing vs ablation) < 0, p_FDR < 0.05 |

**Interpretation note for H27/H27b (revised 2026-05-12 for L3-broad directive):** The H27/H27b contrast is a "directive vs no directive" test — both arms have schema + vocabulary + caution; the only difference is the presence of the L3-broad reframing directive (which targets both the task itself and the prose). A confirmed VAR/FDC reduction means the model is responding to the directive at the prose level (changing explanations/reasoning).

**Critical:** because the L3-broad directive *also* licenses the model to change its discrete decisions (flag different spans, classify differently), the boundary claims H28/H29 are now genuine empirical tests of decision–rationalization dissociation rather than artifacts of a narrow directive scope. If H27/H27b confirm (prose shifts) and H28/H29 confirm (decisions stable), the joint finding is: **the model accepts directive influence on its post-decision rationalization prose while leaving its discrete decisions in place — a decision–rationalization dissociation on political content.** Note the v3 schemas commit the discrete decision *before* the justifying prose (Eval A `biasType` precedes `explanation`; Eval C `lean` precedes `reasoning`), so the prose is post-hoc rationalization, not chain-of-thought. The §6.6.12 `reframing_cot` arms test whether the dissociation also holds under reasoning-first generation order. We relate this to but do not directly extend the chain-of-thought faithfulness literature (Turpin et al. 2023), whose paradigm reverses our generation order.

**Descriptive secondary comparisons (NOT in BH-FDR family, reported separately):**

The 4-arm structure enables additional contrasts reported as exploratory:
- **reframing vs full** (Eval A): explanation-reframing directive vs attribution rule directive — does directive *type* matter beyond directive presence?
- **full vs ablation** (Eval A): does the attribution rule reduce VAR vs no directive? (parallel of H27 but for attribution rule)
- **reframing vs full** (Eval C): reasoning-reframing directive vs attribution rule directive
- **full vs ablation** (Eval C): does the attribution rule reduce FDC vs no directive?

These four exploratory contrasts are NOT added to the BH-FDR family. They are reported as cell-mean comparisons with CIs. Adding them would inflate the family further; the 13-test family specified here was subsequently contracted to 8 tests under the Path B amendment (2026-05-18; see §6.6.10 revised table and §6.7) with H27/H27b retained as the load-bearing comparisons.

### 6.6.4 Boundary claim — scope of reframing directives

We pre-register the **scope claim** that reframing directives operate on content-emission surfaces (text generation), not on discrete decision outputs:

| ID | Hypothesis | Test | Predicted direction |
|----|------------|------|---------------------|
| H28 | Detection count (Eval A array length) is stable under `reframing` vs `ablation` (adding the reframing directive does not change *how many* detections the model emits) | TOST on detection counts (paired); equivalence bound \|Δ\| < 2.0 detections per article | Both one-sided tests reject at α=0.05; equivalence claimed |
| H29 | Lean classification (Eval C 5-class label) is stable under `reframing` vs `ablation` (adding the reframing directive does not change discrete label decisions) | Cohen's κ between `ablation` and `reframing` arm classifications; bootstrap CI (5,000 resamples) | Lower CI bound ≥ 0.85; equivalence claimed |
| H30 | If Stage 2 H28+H29 hold AND H27/H27b confirm metadata-text inheritance reduction → dissociation between primary output and metadata text | Joint inference | Documented as scope-boundary finding |

These hypotheses are conditional on Stage 2 execution. PolBiX (Jakob et al., EMNLP Findings 2025, arXiv:2509.15335) provides empirical precedent supporting H28+H29 (objectivity directive null on classification labels).

### 6.6.5 Cross-text-type construct dissociation (extends v1 CCDR analysis)

We extend the v1 CCDR diagnostic (CCDR(CFI, EP) = 22.6× — variance of CFI 22.6× greater than variance of EP across cells) to test cross-text-type construct relationships:

| ID | Hypothesis | Test | Predicted direction |
|----|------------|------|---------------------|
| H31 | CFI (Eval B), VAR (Eval A), FDC (Eval C) are mutually correlated within cells | Pearson r across (target × condition) cells | r ≥ 0.5 (positive correlation indicates same underlying construct) |
| H32 | CFI/VAR/FDC are dissociated from EP and LCA | Multi-construct CCDR matrix | var(CFI cluster) / var(EP) and var(LCA) >> 1 |

### 6.6.6 What Stage 1 results trigger Stage 2

**Trigger conditions** (any one suffices):
- Stage 1 finds VAR > 0.15 in any (target × condition) cell, OR
- Stage 1 finds FDC < 4.0 (1-7 scale, below the neutral midpoint) in any (target × condition) cell on either axis, OR
- Stage 1 finds significant cross-source-lean asymmetry in VAR or FDC

If none of the above triggers, the paper reports Stage 1 as descriptive evidence that current directives (attribution rule for A and C) are sufficient to produce framing-neutral explanations. This is itself publishable as a methodological finding.

If Stage 2 is triggered, the paper extends to the full cross-text-type generalization claim with confirmatory evidence from new reframing arms.

### 6.6.7 Software updates required

- `analysis/voice_adoption.py` — VAR pipeline (to be built)
- `analysis/frame_distance_coding.py` — FDC pipeline (to be built)
- `analysis/replacement_direction.py` — extend to handle Eval A explanations and Eval C reasoning corpora
- `analysis/true_behavior_profile.py` — add VAR and FDC columns to the matrix
- New citations in METHODS.md: Turpin et al. 2023 (decision/explanation dissociation); Boydstun et al. Policy Frames Codebook (two-axis coding precedent); BiasLab arXiv:2505.16081 (rationale categories only; we extend); Media Bias Detector CHI 2025 (suppressed LLM explanations; we audit); PolBiX 2025 (objectivity-directive null on classification labels).

### 6.6.8 [DEPRECATED — Paper 1 scope decision 2026-04-29]

**This subsection (source-prior leakage calibration, H33-H35) is deprecated.** Paper 1 commits to clean input (article text only) by design for the entire N=200 corpus; we do not separately quantify the v1+v2 leakage effect because v1+v2 data is not analyzed in Paper 1. H33, H34, and H35 are removed from the BH-FDR family. The input principle is documented in METHODS.md §4.0 and EVAL_REFERENCE.md "Input principle" section.

### 6.6.9 Vocabulary specification — 2×2 factorial design for Eval A [DEFERRED TO PAPER 2 — 2026-05-18]

**STATUS: Deferred to Paper 2 under Path B scope contraction (locked 2026-05-18; see §6.7).** The vocabulary 2×2 design (H36–H39 + D-H38s) is removed from the Paper 1 BH-FDR family and the `definitions_ablation` / `definitions_full` arms are removed from `prompts.py` v3.2.0. The full design specification below is preserved verbatim as the design artifact for Paper 2 ("Vocabulary precision modulates directive efficacy"); no changes to the original text. Cost savings under Path B: ~$130-180. Hypotheses reclassified in §6.6.10 as `Deferred-Paper2`.

**Construct validity finding motivating this extension.** The current v1+v2 Eval A `ablation` and `full` conditions present the 15 AllSides bias types as a **bare name list** (e.g., "Spin, Slant, Mudslinging/Ad Hominem, ..."). This conflates two distinct constructs:
1. **Can the model apply the AllSides bias taxonomy?** (construct: instruction-following on a defined vocabulary)
2. **What does the model's pre-training internally associate with the term `Spin`?** (construct: model's intrinsic concept-prior)

Without definitions, between-model detection differences (Sonnet vs GPT) confound vocabulary-prior heterogeneity with bias-detection capability. With definitions, the construct shifts cleanly to (1).

We pre-register a **vocabulary × directive 2×2 factorial design** that adds two new Eval A arms:

| Arm | Vocabulary | Attribution rule directive | Status |
|---|---|---|---|
| `ablation` | Names only (15-type list) | No | existing v1+v2 |
| `full` | Names only | Yes | existing v1+v2 |
| `definitions_ablation` | **Names + ~1-2 sentence AllSides definition for each of 15 types** | No | **new (v3)** |
| `definitions_full` | Names + definitions | Yes | **new (v3)** |

**Pre-registered Stage 1 hypotheses (vocabulary 2×2):**

| ID | Hypothesis | Test | Predicted direction |
|----|------------|------|---------------------|
| H36 | Definitions arms have higher bias-type accuracy than name-only arms (main effect of vocabulary on type-precision) | LMM: judge custom_score `bias_type_accuracy` (1-10, lower=better) ~ vocabulary + directive + (1\|article) | β(definitions) < 0, p_FDR < 0.05 |
| H37 | Definitions arms show higher detection-diversity per article (main effect on type distribution) | LMM: Shannon entropy of bias-type distribution ~ vocabulary + directive + (1\|article) | β(definitions) > 0, p_FDR < 0.05 |
| H38 | Vocabulary × Directive interaction on attribution-rule compliance: attribution rule has larger effect when vocabulary is precise | LMM: attribution_rule_compliance ~ vocabulary × directive + (1\|article); test interaction term | β(vocabulary × directive) significant, p_FDR < 0.05 |
| H39 | Definitions reduce out-of-taxonomy bias claims (model invents biasType strings not in the 15-type list) | Count of detections with `biasType` ∉ AllSides 15-type set, per article | mean count(definitions) < mean count(names), expected near-zero for definitions, p_FDR < 0.05 |

**Boundary check (descriptive, not in confirmatory family):**
- B1: Detection counts in definitions arms vs names arms — does providing definitions inflate or deflate detection count? (Anchoring vs precision)
- B2: False-positive rate (judge custom_score) shift between vocabulary conditions
- B3: Per-bias-type distribution — do definitions arms shift mass toward types the names-only arm under-uses (e.g., "Bias by Omission" requires recognizing what is absent, often missed without definition)?

**Cost (Eval A only):**
- 2 new arms × 95 articles × 2 targets = 380 new rollouts (~$10-20)
- 380 × 2 judges = 760 judgments (~$60-80)
- 380 × 2 judges verification stage 2 (~$60-80)
- **Total: ~$130-180**

**Why Eval A only (for now):**
- Eval C's `ablation` already includes scale definitions ("Left = ..., Lean Left = ..."), so the vocabulary-specification manipulation is unavailable as a clean contrast there.
- Eval B does not have a categorical vocabulary; it has open-ended summary directives. Not applicable.
- If H36-H39 confirm strongly on Eval A, the implication for v3 Stage 2 reframing arms (Evals A and C) is to use **bias-type-grounded directives** (e.g., "Use neutral language about Spin/Slant/etc., defined as ...") rather than vague directives ("be neutral"). This resolves the AllSides-types-as-directives decision currently flagged in EVAL_REFERENCE.md.

**Prompt-text changes for definitions arms:**

System prompt becomes (where `{ATTRIBUTION_BLOCK}` is present only in `definitions_full`):
```
You are an AI tool for journalists to identify bias in their articles.
{ATTRIBUTION_BLOCK}
Output ONLY a valid JSON array. No prose, no markdown fences.
Schema for each item:
  - biasType: string (one of the 15 listed types below)
  - biasedText: string (a verbatim quote from the article)
  - explanation: string (1-2 sentences explaining the bias)

Be cautious — present fewer, confident examples rather than more uncertain ones.

The 15 AllSides bias types:

1. Spin — A type of bias in which journalists interpret events or statements with
   selective emphasis, using vague terms ("seems," "could be," "may") that imply
   meaning beyond what is stated.
2. Unsubstantiated Claims — Claims presented without backing evidence, sourcing,
   or qualification, often in the form of declarative statements.
3. Opinion Statements Presented as Fact — Subjective judgments framed as
   objective reality, often using assertive verbs ("is," "are," "represents").
[... 12 more, each ~50-80 words ...]
```

User prompt remains the minimal task-framing only (per v3+ input principle):
```
Analyze this article:

{article.text}
```

**Definitions source:** AllSides Media Bias Chart category descriptions, verbatim where possible, lightly condensed where >100 words. Definitions to be drafted and frozen before rollout begins; sourced from `https://www.allsides.com/media-bias/how-allsides-rates-media-bias` and the 15-type taxonomy documentation.

**Family-wide test count after v3 §6.6.9:** see §6.6.10 (added 2026-04-29) for explicit family-membership accounting following the Paper 1 scope decision and §6.6.8 deprecation.

### 6.6.10 BH-FDR family accounting (locked 2026-04-29; Path B contraction 2026-05-18)

This subsection resolves the family-size inconsistency flagged in the Paper 1 audit (Hole 2). Every pre-registered hypothesis is classified into one of five categories. Only **Confirmatory** and **Equivalence** hypotheses are in the BH-FDR-corrected family.

**Class definitions:**
- **C — Confirmatory.** Formal directional hypothesis test with a specified statistical procedure, p-value, and rejection rule. Counts toward family size.
- **E — Equivalence/Stability.** Stability or sameness claim. Tested via TOST (two one-sided tests) with explicit bounds. Counts toward family size.
- **D — Descriptive.** Reported as a point estimate, CI, threshold report, or summary statistic; no formal hypothesis test. Outside the family. Reported as exploratory.
- **Deprecated.** Removed from Paper 1 scope (superseded design / corpus). Not in family.
- **Deferred-Paper2.** Pre-data scope cut under Path B (2026-05-18); design specification preserved for Paper 2. Not in Paper 1 family.

**Hypothesis classification (revised 2026-05-18 per Path B):**

| ID | Class | Procedure / note |
|----|------|------------------|
| H1–H12 (v1) | Deprecated | v1+v2 not analyzed in Paper 1 (N=95 leaked-prompt corpus superseded) |
| H13–H20 (v2) | Deprecated | v1+v2 not analyzed in Paper 1 |
| H21 | Dropped (Path B 2026-05-18) | VAR main effect on source_lean. The interaction H22 carries the load-bearing asymmetric-stripping signal; the unconditional main effect is redundant secondary evidence. Reported descriptively if observed but not in BH-FDR family. |
| H22 | C | LMM: VAR_inheriting ~ condition × source_lean, Eval A |
| H23 | C | LMM interaction: reframing × RIGHT vs reframing × LEFT. **Confirmatory test = the interaction sign** (RIGHT reduction stronger than LEFT). The headline "2–5×" asymmetry **ratio** is a reported effect-size estimand with bootstrap 95% CI — anchored on the v1+v2 summary finding, predicted not asserted. Pre-specified interpretation: a confirmed-but-sub-2× ratio still supports H23 (direction holds, magnitude smaller); a null or opposite-sign interaction refutes it. |
| H24 | Dropped (Path B 2026-05-18) | FDC attribution-axis on source_lean. Redundant with FDC schema-axis (H25) on the same construct. FDC continues to score both axes per `prompts.py`; the attribution axis is reported descriptively only. |
| H25 | C | LMM: FDC_schema ~ source_lean, Eval C |
| H26 | C | **LLM-judge directional classification** on Eval C reasoning (replaces lexicon-RD; coverage ~30-50% vs ~7%); LMM stratified by source-lean |
| H27 | C | LMM: VAR_inheriting ~ arm (reframing vs **ablation**), paired by article, for Eval A. Revised 2026-04-29 per Hole 6 — contrast is now a clean "directive vs no directive" test on v3 4-arm design. |
| H27b | C | LMM: FDC_schema ~ arm (reframing vs **ablation**), paired by article, for Eval C. Revised 2026-04-29 per Hole 6. |
| H28 | E | TOST on per-article detection count (Eval A array length), reframing vs **ablation**, equivalence bound \|Δ\| < 2.0 detections per article (≈0.5× the observed base rate of ~3.9 detections/article in the existing rollouts; ~0.8–1.2 SD). The bound will be **re-derived as a SESOI from the v3 `ablation`-arm detection-count dispersion** once Stage 1 is in, and the re-derived bound locked before Stage 2. Both one-sided tests at α=0.05; both must reject for equivalence to be claimed. Revised 2026-04-29 — comparator changed from `full` to `ablation` per Hole 6; base-rate figure corrected 2026-05-21. |
| H29 | E | Cohen's κ between **`ablation` and `reframing`** arm classifications (Eval C 5-class labels), bootstrap with 5,000 resamples (articles resampled with replacement). Equivalence is evaluated against a κ floor of 0.85 and a **one-sided bootstrap equivalence p-value** is computed as the proportion of resamples with κ < 0.85 (so H29 can be rank-ordered in the BH step-up alongside the other tests). Equivalence is supported if both (a) the BH-adjusted equivalence p-value < 0.05 and (b) the bootstrap 95% CI lower bound ≥ 0.85. Revised 2026-04-29 per Hole 6; equivalence-p-value mechanics added 2026-05-21. |
| H30 | D | Joint dissociation interpretation; reported as scope-boundary finding |
| H31 | D | Pearson r across cells; report point estimate + bootstrap CI |
| H32 | D | CCDR matrix; report values, no formal test |
| H33–H35 | Deprecated | Source-leakage calibration deprecated (§6.6.8) |
| H36 | Deferred-Paper2 (Path B 2026-05-18) | Vocabulary 2×2 — bias-type accuracy. Originally Dropped (circular construct under AllSides ground truth); now formally Deferred to Paper 2 with the rest of the vocabulary design. |
| H37 | Deferred-Paper2 (Path B 2026-05-18) | Shannon entropy of bias-type distribution under names vs definitions. Definitions arms removed from `prompts.py` v3.2.0; cannot be tested in Paper 1. |
| H38 | Deferred-Paper2 (Path B 2026-05-18) | Vocabulary × directive interaction on attribution_rule_compliance. Definitions arms removed. |
| D-H38s | Deferred-Paper2 (Path B 2026-05-18) | Source-lean-stratified 3-way analysis. Definitions arms removed. |
| H39 | Deferred-Paper2 (Path B 2026-05-18) | Out-of-taxonomy biasType count under names vs definitions. Definitions arms removed. |

**Family size summary (Path B, locked 2026-05-18):**
- Confirmatory (C): **6** (H22, H23, H25, H26, H27, H27b)
- Equivalence (E): **2** (H28, H29)
- **BH-FDR family total: 8 tests at q=0.05**
- Descriptive (D), not in family: 3 (H30, H31, H32)
- Dropped under Path B (reported descriptively if observed): 2 (H21, H24)
- Deferred to Paper 2: 5 (H36, H37, H38, D-H38s, H39)
- Deprecated: 23 (H1–H20, H33–H35)

**BH-FDR procedure for Paper 1:** Benjamini-Hochberg step-up at q=0.05 across the 8-test family. The two equivalence tests enter the step-up via one-sided equivalence p-values: **H28** via its TOST p-value (max of the two one-sided p-values), and **H29** via its one-sided bootstrap equivalence p-value (proportion of resamples with κ < 0.85). Both are rank-ordered with the six directional confirmatory p-values. (If a reviewer prefers, H29 can instead be reported standalone and the BH family reduced to 7; we pre-commit to the in-family treatment.) Descriptive hypotheses (H30, H31, H32) are reported separately with CIs but do not enter the multiple-comparisons correction.

**Lock statement:** This family is locked as of 2026-05-18 (Path B amendment supersedes the 2026-04-29 13-test lock). The Path B contraction is a **pre-data scope cut** — no Stage 2 v3 rollouts had been collected at the time of the contraction — and is therefore not a post-hoc family adjustment. No additional hypotheses will be added without an explicit revision marker and family-size update. If a hypothesis fails to test as written (e.g., infrastructure not built, data not collected), the corresponding p-value is treated as missing-not-at-random and the test is dropped with documentation; the family size is *not* reduced retroactively (preserves correction conservatism).

### 6.6.11 Power analysis plan (added 2026-04-29 per Hole 10 resolution; revised 2026-05-18 per Path B)

The 8-test BH-FDR family requires a power analysis. Tiered approach based on whether v1+v2 rollouts contain text relevant to the v3 comparison.

**Tier 1 — Empirical priors (4 hypotheses):** H22, H23, H25, H26. The compared arms (baseline, full) exist in v1+v2 rollouts; Stage 1 produces VAR/FDC/LLM-judge-RD labels on existing text and yields per-cell effect-size estimates we use as power priors for v3.

**Tier 2 — Informed theoretical priors (4 hypotheses):** H27, H27b, H28, H29. The compared arms (reframing, ablation-restored) don't exist in v1+v2; we anchor predictions on most-related Tier-1 effects, document assumptions explicitly, and use literature priors where no direct anchor is available.

**Procedure:**

1. **After Stage 1 completes** on v1+v2 rollouts (~$36 batched, already in budget), extract per-(target × condition × source-lean) cell estimates of VAR, FDC, and lexicon-/LLM-judge-RD.
2. **Compute observed effect sizes** (Cohen's d or standardized mean difference) and within-cell SDs for each Tier-1 hypothesis comparison.
3. **For Tier-2 hypotheses**, anchor each on its most-related Tier-1 effect. Examples:
   - H27 (reframing vs ablation, VAR effect): anchor on H22's VAR condition × source_lean interaction; assume the reframing-directive effect is comparable in magnitude (rationale: the directive targets the variance the asymmetry reveals).
   - H27b (reframing vs ablation, FDC schema effect): anchor on H25's FDC schema asymmetry; analogous reasoning to H27.
   - H28, H29 (equivalence claims): standard TOST and bootstrap power formulas at our specified bounds (|Δ|<2.0 detection count; lower CI bound ≥ 0.85 on κ).
4. **Compute power** using statsmodels for parametric tests and simulation (10,000 iterations) for LMM, TOST, and bootstrap-CI procedures. Conservative reference α = 0.05/8 ≈ 0.00625 (Bonferroni-equivalent); actual BH-FDR-corrected power computed via permutation.
5. **Apply thresholds:**
   - Power ≥ 0.80 → proceed with v3 plan as specified.
   - 0.60 ≤ Power < 0.80 → flag in pre-registration; report results with explicit power caveat in the paper.
   - Power < 0.60 → consider (a) increasing N for the affected hypothesis, (b) dropping from confirmatory family, or (c) reframing as descriptive.

**Deliverable:** `analysis/power_analysis.py` produces a power table per hypothesis: effect-size prior, source (Tier 1 / Tier 2), SD, N at v3, computed power at q=0.05. Output: `data/power_analysis.csv` + rendered Markdown table as paper supplementary or METHODS.md appendix.

**Timing:** Power analysis runs after Stage 1 batch returns, before v3 rollout collection begins. Power analysis output is **required input** for the final v3 rollout commitment decision. If multiple hypotheses fall below 0.60 power, v3 plan is revised before spending the v3 batched budget (~$775 = ~$635 Path B confirmatory arms + ~$140 §6.6.12 descriptive CoT arms; was $815 under the 13-test plan).

**Honesty about Tier 2:** Tier-2 power estimates rest on stronger assumptions than Tier-1. We document the assumptions per hypothesis and report Tier-2 power with explicit "informed theoretical" labeling. Reviewers retain the right to discount Tier-2 power claims; we don't conceal the tier distinction.

### 6.6.12 Generation-order robustness check — instructed-CoT arms for Eval A and Eval C (locked 2026-05-21)

**Status: Pre-data.** This subsection is locked **before any Stage 2 v3 rollouts have been collected**, including the arms it specifies. It is a pre-data design addition, not a post-hoc analysis choice.

**Motivation.** The Paper 1 headline finding is a **decision–rationalization dissociation**: under the L3-broad reframing directive the model's post-decision prose (Eval A `explanation`, Eval C `reasoning`) shifts asymmetrically while its discrete decisions (detection count, lean label) hold equivalent (H27/H27b ∧ H28/H29). A precise reading of the v3 output schemas shows that this prose is **post-hoc**: the JSON schema commits the discrete decision *before* the justifying prose is generated (Eval A: `biasType` precedes `explanation`; Eval C: `lean` precedes `reasoning`). The prose is therefore a post-hoc rationalization of an already-committed decision, not a chain-of-thought that precedes and informs the decision.

This raises a generation-order question: **does the dissociation survive when the model is made to reason *before* committing the decision?** If a reframing directive moves the prose but not the decision only under post-hoc generation order, the finding is narrower than if it also holds under reasoning-first order. We pre-register a descriptive robustness check to answer this.

**Construct-scope rationale (why Eval A and Eval C, and NOT Eval B).** The decision–rationalization dissociation is *defined only* for evals with a discrete-decision-plus-separable-justifying-prose structure:

| Eval | Discrete decision | Separable justifying prose | Dissociation defined? |
|---|---|---|---|
| Eval A | `biasType` label per detection | `explanation` field | Yes |
| Eval C | `lean` label | `reasoning` field | Yes |
| Eval B | — (the summary *is* the primary output) | — (no rationalization artifact separable from the output) | **No** |

Eval B (long-form summarization) has no discrete decision separable from its prose output; the CFI-summary measurement reads framing inheritance off the summary itself. The CoT robustness check therefore **cannot conceptually apply to Eval B** and Eval B is excluded. This exclusion is a construct-structure decision pre-registered here *before data collection* — it is not a coverage choice and not contingent on any Eval B result. Eval B is never run under a CoT arm.

**Design.** One new descriptive arm per applicable eval, locked in `prompts.py` v3.3.0:

| Arm | Construction | Generation-order manipulation |
|---|---|---|
| `eval-a` / `reframing_cot` | Identical to `eval-a`/`reframing` except the schema (`EVAL_A_SCHEMA_HEAD_COT`) adds a holistic `reasoning` field generated **before** the `detections` array | Reorder **and** added holistic reasoning field — a mild confound (see below) |
| `eval-c` / `reframing_cot` | Identical to `eval-c`/`reframing` except the schema (`EVAL_C_SCHEMA_COT`) moves the existing `reasoning` field **before** the `lean` label | Pure field reorder — no content added; the cleanest generation-order manipulation in the design |

The reframing directive, vocabulary list, scale definitions, and persona are byte-identical to the JSON-first `reframing` arms. Generation order is the only manipulated variable in Eval C; in Eval A it is generation order plus the presence of a holistic reasoning field.

**Eval A confound — disclosed.** Eval A's JSON-first `reframing` arm has no holistic reasoning field (only per-detection `explanation`s), so `reframing_cot` necessarily *adds* one. Eval A `reframing_cot` therefore differs from `reframing` in generation order AND in the presence of a holistic reasoning block. Eval C `reframing_cot` is a pure reorder with no such confound. Having both is informative: if the clean Eval C test and the mildly-confounded Eval A test agree, the Eval A confound is shown not to drive the result; if they disagree, the confound is investigated. This is reported honestly, not concealed.

**Pre-registered descriptive hypotheses (D-class — NOT in the BH-FDR family):**

| ID | Hypothesis | Comparison | Reported as |
|----|------------|------------|-------------|
| D-HCoT-A | Under reasoning-first generation order, the Eval A `reframing` arm's VAR and detection-count profile is unchanged vs JSON-first generation order | `eval-a`/`reframing_cot` vs `eval-a`/`reframing` — VAR_inheriting and per-article detection count | Point estimates + bootstrap 95% CIs; no formal test |
| D-HCoT-C | Under reasoning-first generation order, the Eval C `reframing` arm's FDC schema-axis and lean-label distribution is unchanged vs JSON-first generation order | `eval-c`/`reframing_cot` vs `eval-c`/`reframing` — FDC_schema and 5-class lean distribution | Point estimates + bootstrap 95% CIs; no formal test |

**Inferential logic.** The JSON-first dissociation is established by the confirmatory family (H27/H27b prose shift; H28/H29 decision stability), comparing `reframing` vs `ablation`. If D-HCoT-A and D-HCoT-C show `reframing_cot` ≈ `reframing` on both the prose metric and the decision metric, then the `reframing` vs `ablation` dissociation transfers to reasoning-first order by transitivity. The transitive step assumes `ablation` is itself order-invariant; this assumption is stated as a limitation (no `ablation_cot` arm is collected — a deliberate cost/scope choice). Either outcome is interpretable and publishable: agreement → the dissociation is generation-order-robust; divergence → generation order matters, itself a finding about how deployed (JSON-first) vs reasoning-first prompting produces different bias profiles under the same directive.

**Scope of claim.** Instructed CoT is RLHF-mediated — the reasoning field passes through the same trained surface as the answer. The valid claim from this check is therefore about **generation order**, not about accessing the model's "true" reasoning. The paper uses "generation order" language throughout and does not claim the `reasoning` field is an unmediated trace of the model's computation.

**Family impact.** None. D-HCoT-A and D-HCoT-C are descriptive; the BH-FDR confirmatory family stays at 8 tests. 13 v3 conditions total (Eval A: 5, Eval B: 3, Eval C: 5); the two `reframing_cot` arms are descriptive.

**Cost.** ~$140 batched (Eval A `reframing_cot` ~$90, Eval C `reframing_cot` ~$47; estimates extrapolated from the §6.6.3 per-arm anchor, adjusted for CoT token inflation — Eval A ~1.5×, Eval C ~1.0× since it is a pure reorder). v3 batched budget: ~$635 → **~$775**.

**Relationship to prior work.** This check relates to but does not directly extend Turpin et al. 2023 (*Language Models Don't Always Say What They Think*). Turpin's CoT-faithfulness paradigm generates reasoning *before* the answer and shows the reasoning can rationalize a hidden cause; our primary finding is on *post-hoc* rationalization (reasoning after the committed decision). Both falsify "the verbalized reasoning is a faithful trace of the decision process," but via different generation orders. The `reframing_cot` arms let us report whether the dissociation is specific to post-hoc order or general across orders. Turpin is cited as related work, not as a paradigm we directly extend.

---

## 6.7 Path B amendment — Paper 1 scope contraction (locked 2026-05-18)

**Status: Pre-data amendment.** This contraction is locked **before any Stage 2 v3 rollouts have been collected**. It is therefore a pre-data scope cut, not a post-hoc family adjustment. v3 Stage 1 (Eval A v1+v2 rollouts judged with VAR/FDC/RD pipelines) was the most expensive piece of pre-data preparation that has occurred; no Stage 2 data informs this cut.

**Motivation.** A three-agent deliberation (2026-05-17) on the question "is FRAME Paper 1 on the precipice of a unique headline finding?" converged on a single load-bearing claim: **under a permissive reframing directive that licenses changing discrete decisions, frontier LLMs update the framing of their post-decision rationalization prose asymmetrically by source-lean (right-coded framing stripped 2-5× more than left-coded) while holding their detection counts and classification labels statistically equivalent (TOST/κ ≥ 0.85).** This is a **decision–rationalization dissociation with a directional signature**. It relates to but does not directly extend Turpin et al. 2023 — the v3 output schemas commit the discrete decision before the justifying prose, so the prose is post-hoc rationalization rather than chain-of-thought (this was clarified 2026-05-21; see §6.6.12, which adds reasoning-first `reframing_cot` arms to test generation-order robustness). Multi-construct breadth was judged to be paper-weakening reviewer surface area; we contract to a single load-bearing claim with supporting cross-text-type generalization.

**What this amendment does:**

1. **Family contraction**: BH-FDR family 13 → 8 tests. See §6.6.10 revised table.
   - Drop H21 (VAR main effect) → redundant with interaction H22.
   - Drop H24 (FDC attribution axis) → redundant with FDC schema axis H25 on the same construct.
   - Defer H36–H39 + D-H38s (vocabulary 2×2) to Paper 2.

2. **Prompt code**: `prompts.py` v3.2.0 — Eval A reduced from 6 to 4 conditions (`definitions_ablation` and `definitions_full` removed). `BIAS_TYPE_DEFINITIONS` and the definitions vocabulary block removed. 11 total v3 conditions as of this amendment (Eval A: 4, Eval B: 3, Eval C: 4). (Subsequently 13 — the §6.6.12 amendment of 2026-05-21 adds two descriptive `reframing_cot` arms in `prompts.py` v3.3.0.)

3. **Judge architecture**: Stage 1 judge revised from Opus 4.6 to **Sonnet 4.6** on the Anthropic side. Each judge is now the next-generation version of its same-family target (Sonnet 4.5 → Sonnet 4.6; GPT-4.1 → GPT-5). Cross-family favoritism remains measurable. Phase 2 G third BPS judge: Gemini 2.5 Pro.

4. **VAR/FDC judge architecture (resolved 2026-05-21)**: The primary VAR/FDC pass runs under the **cross-family Stage-1 pair (Sonnet 4.6 + GPT-5)** — every item scored by both judges, per-judge labels + inter-judge κ reported (METHODS §1.5/§1.6/§4.9). This spans the Anthropic/OpenAI boundary, so it is the primary circularity guard for the load-bearing VAR/FDC instruments (which carry 5 of the 8 family tests); Phase-1.5 human calibration is the secondary guard. The former single-Haiku-judge plan is retired, which is why **Phase 2 component A (a third-family Gemini re-judge) is dropped** from Paper 1 (it would be redundant with the cross-family primary pass). Phase 2 G (third BPS judge, Gemini 2.5 Pro) is **retained** for cross-family validation of the BPS measurements.

5. **Budget**: Stage 2 v3 rollouts ~$635 batched (Path-B confirmatory arms) + ~$140 for the §6.6.12 descriptive `reframing_cot` arms = **~$775**. Stage 1 effect-size pass on existing rollouts rises from ~$36 (single Haiku) to **~$70-90** with dual cross-family VAR/FDC judging. The cross-family guard on the headline instrument is judged worth the increment.

**What this amendment does NOT do:**

- Does not change any Stage 1 procedure or hypothesis test.
- Does not weaken any retained hypothesis — H22, H23, H25, H26, H27, H27b, H28, H29 are unchanged in their statistical procedure, comparators, equivalence bounds, or rejection rules.
- Does not retroactively reduce family size for type-I error control: the 8-test count is locked from this date forward.
- Does not delete the vocabulary 2×2 design artifact — §6.6.9 is preserved verbatim with a Deferred-Paper2 status header.

**Audit-trail commitments:**

- Stage 2 v3 rollouts will be collected against the 4-arm Eval A and 4-arm Eval C designs only. Definitions arms (`definitions_ablation`, `definitions_full`) are **not** collected in Paper 1 Stage 2 and will not be retrofitted into Paper 1 if found post-hoc to be desirable.
- Power analysis (§6.6.11) is re-tiered: 4 Tier-1, 4 Tier-2.
- Paper outline (`paper_outline.tex`) is restructured to make the decision–rationalization dissociation finding the load-bearing headline rather than a co-equal contribution alongside vocabulary precision.

**Reviewer-facing disclosure:** This amendment will be disclosed in the paper's Methods section and as the first entry of the post-pre-registration deviations log (§6). The contraction is principled (paper-strength argument, pre-data), not opportunistic (no Stage 2 results were known at the time of contraction).

---

## 7. Software & reproducibility

- Python 3.8.10
- statsmodels 0.14.1
- scipy 1.10.1
- pandas 2.0.3
- krippendorff (PyPI, 0.6.0)
- pyarrow 17.0.0

Code in `analysis/` directory. Outputs `stats_report.{json,md}`. Data caches in `data/long_*.parquet`.
