# What benchmark can we actually release? (data inventory, 2026-07-30)

Inventory of every asset vs the requirements of a benchmark (items, scoring
rule, ground truth or deterministic metric, releasability, novelty, headroom).

## Assets found
| Asset | Size | Ground truth? | Releasable? |
|---|---|---|---|
| Judge verdicts, 3 instruments x 4 families on shared items | **62,581** (RD 9,139; VAR 44,851; FDC 8,591) | no (that's the finding) | yes — model outputs |
| 6-model lean committee (targets + 4 judges) | 800 judge + ~2,000 target labels on 200 articles | AllSides 5-class + continuous | labels yes; article text via recipe |
| Pre-located hard strata | RD 1,084 split items (>=3 families); VAR 631 threshold cases | no | yes |
| Test-retest slice | 400 re-runs | n/a (stability) | yes |
| Model outputs (all evals/conds) | 7,000 rollouts | — | yes (short article spans OK; full text via URL+curation script) |
| Deterministic tools | traceability scorer; paired lexicon | rule-based | yes |

## Verdict: ONE strong release — a judge-reliability corpus + challenge
The standout asset is the **62.5k-verdict, four-family judge corpus on shared
items over three subjective framing constructs** with a documented
impossibility result (cross-family kappa ~0 for 2 of 3 instruments; the third
vendor-pair-specific). Nothing like it exists: RewardBench/JudgeBench-style
meta-eval sets target objective-ish response comparison, not subjective
political-framing constructs, and none ship four-family verdicts with the
disagreement anatomy pre-located.

### Proposed structure (3 tracks; honest about what each can score)
1. **Deterministic track (releasable NOW):** source-traceability of judge-cited
   evidence (bench_source_traceability.py). No GT needed. Reference results:
   4 families, 3x spread. Framed as a *check* (cites CiteGuard et al. lineage),
   not a novel idea.
2. **Diagnostic-resource track (releasable NOW):** the 62.5k verdicts + the
   1,084 RD split items + 631 VAR threshold cases + test-retest slice, for
   judge-behavior research. Challenge framing: "our four families agree at
   kappa<=0.07-0.13 on VAR/FDC; report your judge's cross-family kappa and
   stability on the same items." Scores reliability, not correctness — stated.
3. **Gold track (releasable AFTER the planned human calibration):** the
   pre-committed n=300 stratified human-coded items become a held-out gold
   test set; judges scored on agreement with human GT. This is the track that
   scores VALIDITY — and it falls out of work already committed and budgeted
   ($150-400). The framing-inheritance benchmark (paper-3 idea) is this track
   scaled up (the 631 cases -> ~1k items, ~$1.5-3k).

### Copyright handling (the one release constraint)
Article full text cannot ship (public repo, news copyright). Release:
verdicts + model explanations (model outputs, fine) + short quoted spans +
article URLs + the deterministic curation script + text hashes. Full-text
reconstruction by regeneration — same policy the papers already state.

## What is NOT a strong standalone benchmark
- Lean-classification set (200 articles): too small; AllSides-derived sets
  exist (Baly 2020). Include as part of the suite, don't headline.
- Triage/router set (n=299): a result, not a benchmark; include as baselines.
- A scored "framing-inheritance leaderboard" without human GT: contradicts our
  own finding; do not release.

## Effort
Tracks 1-2: packaging only (no new API calls, no annotation) — a repo README,
loaders, and the release policy. Track 3: rides on the calibration hire.
Natural name: keep modest, e.g. "FrameJudge" corpus + challenge.
