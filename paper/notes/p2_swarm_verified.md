# Paper 2 strengthening swarm — adversarially verified (2026-07-14)
6 finders computed on cached data; each independently re-run by a skeptic.
Every number below reproduced by a second agent's from-scratch code.

## CONFIRMED (add to paper)

### F1 — Disagreement is a free, label-free triage router (CROWN JEWEL)
N=299 (2 targets, eval-C baseline, expert 5-class). 117 disagreements (39.1%).
- acc | AGREE = 71.4% (n=182) vs acc | DISAGREE = 31.6% (n=117); gap 39.8pts,
  bootstrap 95% CI [29.0, 50.4]. Robust to tie-break (23.9/31.6/50.4%).
- Operating table (% of 132 committee errors captured, route worst first):
  vol 10/20/30/40/50%: disagree 15.5/31.1/46.6/61.3/67.7; conf 15.2/25.0/38.6/56.1/65.2.
- Disagree beats confidence at matched volume: +6.1pt (p=.042) @20%, +8.0pt
  (p=.030) @30%; washes out above the disagreement rate (n.s. @39%).
- AUC for predicting an error: disagree 0.692 [.639,.744] vs min-conf 0.697
  [.636,.754]; paired diff -0.004, p=0.895 — statistically indistinguishable
  as global rankers, but disagree is FREE and more error-dense in-budget.
- HONEST CAVEATS (state): part of the gap is structural (on disagreement only
  one of two labels can match one GT label → capped at 0.5); mid-regime p's
  are directional, do NOT survive Holm cleanly → frame as a regime claim;
  baseline condition + one model pair only.

### F2 — Per-model calibration; overconfidence is a boundary artifact
- Both severely overconfident on EXACT 5-class: conf ~.85-.89 vs acc .53-.63.
- GPT-4.1 better calibrated: ECE 0.260 [.209,.313] vs Claude 0.324 [.269,.381]
  (exact-target gap p=.053 — call "suggestive"); Brier 0.286 vs 0.336 (clean).
- Overconfidence is almost entirely exact-boundary: on DIRECTION (within-1)
  GPT-4.1 ECE 0.024 (≈calibrated), Claude 0.085.
- Actionable: stated 0.9 ≈ 71% (Claude) / 77% (GPT) exact accuracy → rescale
  before thresholding; trust confidence only for direction.
- Confound: confidence-correctness AUC essentially tied (.686 vs .681).

### F3 — The reliability map is prompt-invariant (durability)
- Agreement→accuracy gap holds in 5/5 prompt conditions (gap .277-.361,
  bootstrap P(gap>0)=1.0 in every condition).
- Lean-Right strict hardest class in 5/5 (pooled acc .211-.289).
- Honest caveat: the Lean-Right effect is Claude-driven (Claude LR .075-.175,
  argmin 5/5; GPT .263-.462, argmin 3/5).

### F4 — Ensemble NULL + a unanimity gate
- 4-model majority vote does NOT beat best single: 0.6465 vs gpt-4.1 0.6616;
  McNemar p=0.678; bootstrap gain CI [-.061,+.030], P(gain>0)=0.233.
- You cannot pre-pick the best model: bootstrap P(is-best) gpt-4.1 .63,
  claude-4-6 .35, gpt-5 .02, claude-4-5 .00.
- Redirect: unanimity is a high-precision GATE — 4/4 agree on 43.9% of
  articles at 87.4% accuracy. Ensemble buys insurance, not accuracy.

### F5 — Label-granularity robustness (add only label-independent parts)
- Models rank-track the CONTINUOUS expert rating ≥ as strongly as the discrete
  label (Spearman .77-.86; deltas vs label ≤0.01, all 4 models).
- They resolve graded intensity the label discards: within-Lean-Left
  Spearman(pred,rating) +0.40 to +0.50, p≤.01, all 4.
- DO NOT claim this "escapes" AllSides labels: continuous bands recreate the
  label partition EXACTLY (verified symdiff=0), so the 33%/2% asymmetry is the
  label re-expressed, not an independent instrument.

## CUT / WEAKENED
- Difficulty pre-screen ("centrist hardest, CV-AUC 0.68"): WEAKENED. Monotone
  tercile is a sort tie-break artifact (53 articles pinned at |rating|=1.5);
  under within-1 tolerance AUC collapses .676→.563, n.s.; |lean_rating| is
  label-circular. Text-only proxy .55-.59 = open problem, not a result. CUT.

## MAIN-TRACK FRAMING SHIFT
Stop shipping a reliability *map*; ship a validated, label-free *triage
protocol* with an operating curve: (1) route model DISAGREEMENT first (free,
beats confidence in-budget); (2) trust UNANIMITY at committee scale (87%
gate); (3) never read raw confidence as P(correct) — rescale, use for
direction only. Method + reusable benchmark + prompt-invariance = the durable
contribution; the Claude-vs-GPT numbers are perishable payload.

## STILL MISSING for a clear accept (honest)
(a) Second ground-truth source (Ad Fontes/MBFC or human subsample) — NEEDS new
    data, cheap. Biggest gap: everything rides on AllSides source-level labels.
(b) Realizable risk-coverage/AURC curve + Holm correction + router on the other
    4 conditions & a 2-of-4 committee — REANALYSIS, no new data.
(c) A single-model label-free signal (self-consistency across temperature
    samples) benchmarked vs the disagreement AUC 0.69 — NEEDS modest new data.
