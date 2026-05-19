# Inter-Judge Agreement Report

## Cross-Family Dual-Judge Evaluation Design

To assess evaluation integrity, we employed a cross-family dual-judge design: **Claude Opus 4.6** (Anthropic) and **GPT-5** (OpenAI) independently scored both target models — Claude Sonnet 4.5 and GPT-4.1 — across all three evaluations. This design detects systematic bias that would be invisible with a single judge from either family.

![Inter-Judge Agreement Heatmap](figures/inter_judge_agreement.png)

---

## BPS Correlation

Inter-judge correlation on Behavior Presence Scores (BPS), with Fisher-z
95% confidence intervals:

| Eval | N pairs | Pearson r [95% CI] | Krippendorff's α (ordinal) [95% CI] |
|------|:-------:|:------------------:|:-----------------------------------:|
| **A** — Detection | 166 | 0.46 [0.33, 0.57] | 0.27 [0.13, 0.39] |
| **B** — Summarization | 189 | 0.57 [0.46, 0.66] | **−0.17** [−0.32, −0.04] |
| **C** — Classification | 188 | 0.62 [0.53, 0.70] | 0.50 [0.39, 0.58] |

Judges rank articles in broadly the same order (Pearson r), with agreement
strongest on lean classification.

**Important caveat for Eval B**: Krippendorff's α is *negative* (−0.17),
indicating judges disagree on the absolute BPS scale even though their
relative orderings correlate. Opus mean ≈ 3.1, GPT-5 mean ≈ 1.7. Pearson
r captures correlation; α captures agreement. Both should be reported.

---

## Harshness Direction

The harsher judge **flips between evaluations** — there is no stable calibration offset:

| Eval | Harsher Judge | BPS Gap |
|------|:-------------:|:-------:|
| **A** — Detection | GPT-5 | +1.53 |
| **B** — Summarization | Opus | +1.36 |
| **C** — Classification | GPT-5 | +1.06 |

This inconsistency rules out a simple "one judge is always stricter" explanation and supports averaging across both judges as the most defensible reporting strategy.

---

## Family Favoritism

We test family favoritism as the `target × judge` interaction in a regression
of BPS on target and judge, clustering on `article_id`. The interaction
quantifies how much the GPT-5 judge widens or narrows the GPT-4.1 − Sonnet
gap relative to the Opus judge — a negative coefficient means each judge
rates the same-family target more favorably.

| Eval | Interaction β | 95% CI | p (raw) | p (BH-FDR) | Method |
|------|:------------:|:------:|:-------:|:----------:|:------:|
| **A** — Detection | **−0.86** | [−1.60, −0.13] | 0.021 | 0.063 | LMM, ICC=0.19 |
| **B** — Summarization | +0.06 | [−0.14, +0.27] | 0.541 | 0.649 | OLS+CR, ICC≈0 |
| **C** — Classification | **−1.42** | [−1.90, −0.94] | <0.0001 | <0.0001 | OLS+CR, ICC≈0 |

**Eval C** shows the strongest signal: same-family pairings score 1.42 BPS
units lower (more favorable) than cross-family pairings, **confirmed under
pre-registered Benjamini-Hochberg FDR correction** across 12 primary tests
(`PRE_REGISTRATION.md`).

**Eval A** shows a directional effect that *does not survive* FDR correction
(BH-corrected p = 0.063). It should be reported as a suggestive trend, not
a confirmed finding.

**Eval B** shows no family effect — both judges agree on the target ranking.

Computed by `analysis/run_all_stats.py` (LMM 1, BPS ~ target × judge per eval,
clustered on article_id). Full results in `stats_report.md` and `stats_report.json`.

---

## Verification Verdict Agreement

Both judges reviewed 609 matched detection items (bias instances flagged by the target models). Each item received a verdict: confirmed, plausible, unsupported, or hallucinated.

| Metric | Value [95% CI] | Interpretation |
|--------|:--------------:|----------------|
| **4-class Cohen's κ** | 0.07 [0.03, 0.11] | Near-zero (misleading — see below) |
| **Binary Cohen's κ** | 0.36 [0.24, 0.47] | Fair agreement |
| **Binary raw agreement** | 90% | Strong |
| **Positive rate (Opus)** | 95% | — |
| **Positive rate (GPT-5)** | 88% | — |

CIs from 2000-iteration bootstrap resampling of paired detections.

### Why the 4-class κ is misleading

The near-zero 4-class kappa reflects a **granularity disagreement**, not a validity disagreement:

- Opus classifies 67% of detections as "confirmed" and 27% as "plausible"
- GPT-5 classifies only 14% as "confirmed" and 74% as "plausible"

Both judges place the vast majority (88–95%) in the positive bucket (confirmed + plausible). They disagree on *how confidently* a detection is valid, not on *whether* it is valid. The binary kappa of 0.35 and 88% raw agreement more accurately reflect the actionable level of consensus.

---

## Meta-Judgment Agreement

The verification stage included per-article meta-judgment scores across five dimensions. Agreement varies dramatically by dimension:

| Dimension | Pearson r | Interpretation |
|-----------|:---------:|----------------|
| **Explanation quality** | 0.47 | Moderate — judges partially agree on which explanations are better |
| **Political direction bias** | -0.10 | **No agreement** — judges have fundamentally different thresholds for what constitutes directional bias |

The near-zero correlation on political direction bias is a critical finding. Opus rates political direction bias substantially higher than GPT-5 (mean 3.54 vs 2.04), particularly for GPT-4.1 targets (Opus 3.78 vs GPT-5 1.92). This dimension should be treated as **low-confidence** in any reporting.

---

## Confidence Tiers for Reported Findings

Tiers below are determined by formal pre-registered tests (`PRE_REGISTRATION.md`)
with Benjamini-Hochberg FDR correction at q=0.05 across 12 primary contrasts.
Full results: `stats_report.md`, raw values in `stats_report.json`.

### Confirmed (BH-corrected p < 0.05)
- **GPT-4.1 produces less biased summaries (Eval B target effect)** — β=−0.41 BPS [CI −0.61, −0.21], p_FDR=0.0003. Direction agrees across both judges (no interaction).
- **Family favoritism in Eval C lean classification** — interaction β=−1.42 BPS [CI −1.90, −0.94], p_FDR<0.0001.
- **Eval C target main effect at Opus judge** — GPT-4.1 has higher BPS (worse) than Sonnet by 0.44 [CI +0.18, +0.71] when judged by Opus, p_FDR=0.0045. (NB: this flips when judged by GPT-5; the favoritism interaction is the dominant effect.)

### Suggestive but not confirmed (p_raw < 0.05, p_FDR > 0.05)
- **Eval A family favoritism** (interaction β=−0.86, p_raw=0.021, p_FDR=0.063) — directional but does not survive correction across the family of 12 tests.

### Not detected (p_FDR > 0.10)
- **Detection validity differences between targets** (OR=0.89, p_FDR=0.72) — no evidence GPT-4.1 detections are more or less valid than Sonnet's.
- **Explanation quality differences** (β=+0.71, paired-t p=0.04, but LMM p_raw=0.20, p_FDR=0.38) — direction-consistent across judges but underpowered at N=95 articles.
- **Lean classification accuracy differences** (target OR=0.74, p_FDR=0.38) — the question of "which model is better at lean classification" is *not answered* by these data.
- **Lean classification favoritism in target predictions** (OR=1.42, p_FDR=0.38) — separate from the BPS-judgment favoritism in Eval C.

### Descriptive observations (no formal test)
- Both models detect bias at similar rates (~3.5 detections/article).
- 88–95% of detections fall in the valid bucket (confirmed + plausible).
- Sonnet distributes detections more evenly across bias types (Shannon 0.82 vs 0.71).

---

## Methodological Recommendation

All reported scores in this study are **averaged across both judges** to mitigate systematic biases. Findings where judges diverge in direction are flagged as low-confidence. The cross-family design revealed that:

1. **No single judge is reliably neutral** — harshness flips between evaluations
2. **Family favoritism is real but task-dependent** — strongest in classification, absent in summarization
3. **Granularity thresholds differ** — Opus confirms readily, GPT-5 hedges with "plausible"
4. **Political direction bias is not a reliable metric** with current judge models (r ≈ 0)

These findings underscore the importance of multi-judge, cross-family evaluation designs for AI bias benchmarks. A single-judge study would have produced confident but systematically skewed conclusions.
