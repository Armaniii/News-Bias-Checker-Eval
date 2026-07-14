# Novel findings: reliability signals for AI bias-detection tools
(2026-07-13, cached data only — no new API calls)

A separate contribution from the political-bias findings: *which outputs of a
frontier-model bias detector can a tool trust, and how does it triage the rest?*
All computed on baseline eval-A/eval-C, 200 articles, both target models.

## Headline: cross-model agreement is a strong, cheap triage signal
- Two independent frontier models AGREE on the 5-class lean label → **74%** accurate.
  They DISAGREE → **22%** accurate. (n=199 shared articles; 61% agree.)
- **Route-on-disagreement**: route the 39% of articles where the models disagree
  → catch **65% of all errors**; the auto-cleared 61% run at 74% accuracy.
  Beats confidence at matched routing volume (65% vs 59%).
- **Combined rule** (route if models disagree OR either is <0.85 confident):
  route 57% of articles → catch **86% of all errors**; the auto-cleared 43%
  run at **85%** accuracy.
- APPLICATION: a concrete, model-agnostic triage rule for a bias-detection
  product — auto-clear the confident-agreement cases, send the rest to the
  human review that expert-rating platforms already run.

## Confidence is real but the models are badly overconfident
- Confidence → correctness AUC = **0.749** (real discriminative power).
- BUT mean confidence 0.88 vs actual accuracy 0.60 — a **28-point overconfidence
  gap**. Only the top bin is trustworthy: conf≥0.95 → 87% accurate; everything
  below 0.90 is near coin-flip (35–42%).
- APPLICATION: raw confidence must NOT be shown to users as a probability — it
  needs recalibration; but its *ordering* is usable for routing, and the
  conf≥0.95 bin can be auto-trusted.

## Detection count is a validated bias-intensity meter
- Flagged-span count vs expert |lean rating|: Spearman **0.64** (Sonnet) /
  **0.58** (GPT-4.1), both p<1e-18. Monotone dose-response.
- APPLICATION: a tool that simply COUNTS flagged spans is measuring real
  partisan intensity — validates the cheapest possible bias meter.

## Bias-TYPE reliability: only "loaded language" reproduces across models
- Of articles where either model flags a bias type, both agree on:
  Loaded Language **55%**, Framing ~14%, Selection ~16%, Omission ~0%,
  Labeling ~10%, Source ~6%.
- CAVEAT: free-text type strings don't fully normalize ("Framing Bias" vs
  "Framing bias" split the counts), so abstract-type agreement is a loose
  lower bound — but even generously, only concrete-lexical bias (loaded
  language) is reproducible; the interpretive categories are model-specific.
- APPLICATION: a highlighting tool should surface loaded-language flags as
  reliable and treat framing/omission/selection flags as one model's
  opinion, not a fact — show them only on cross-model agreement.

## Lexicon is NOT a per-item drift detector (honest negative)
- As a pre-filter for the judge's directional verdict: precision **0.25**,
  recall **0.30** (tp=106, fp=311, fn=244 over 1,987 items).
- The free lexicon corroborates the AGGREGATE asymmetry (paper Finding 3) but
  cannot stand in for the judge on any single output — aggregate signal is
  real, per-item detection is not.
- APPLICATION: don't ship the cheap lexicon as a live per-article drift flag;
  use it only as a corpus-level monitor / regression check.

## Why this is a real second paper / section
- Distinct from the "directional default" findings: this is reliability
  ENGINEERING for the tool, not a claim about model politics.
- Every result is a deployable rule with a number, model-agnostic, and
  computed with no AI judge in the loop except where noted.
- Directly answers the applications ask; pairs naturally with the six
  finding-anchored design rules already in the Discussion.
