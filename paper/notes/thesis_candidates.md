# FRAME workshop-thesis candidates (mined from existing data only)
Session: 2026-07-07. Sources: paper/frame_iclr_draft.tex (v0.13+),
data/hypotheses_stage2.json, PRE_REGISTRATION.md deviations log,
paper/notes/panel_review_v0.14.md, data/directional_rd.parquet (Stage-2 scope,
3,896 classifiable verdicts, 200 articles), analysis/paper1_*.py.

## COMPUTED THIS SESSION — batch 1 (directional_rd.parquet, read-only)
- Per-arm H26 asymmetry (pooled judges+targets, 80R/80L articles):
  baseline +4.38pp (p=.032) | ablation +4.06pp (p=.066) | full +3.02pp (p=.147)
  | reframing +8.23pp (p=.0013) | reframing_cot +6.77pp (p=.0015)
  (reframing elevation already known to die/reverse under length control — dev log 2026-07-07).
- NEW EQUIVALENCE NUMBER: directive effect on overall drift rate (share of
  classifiable RD verdicts that are directional), paired reframing−ablation per
  article×target (n=390 pairs): **+0.26pp, 90% CI [−2.09, +2.61]pp; TOST ±5pp
  p=.0005 (±10pp p=1.8e-11)**. Sonnet-only: +1.77pp, 90% CI [−1.83, +5.37].
- Judge-disagreement structure: one-judge-flags 17.8% on Right-lean vs 10.9%
  Left-lean (chi2 p=1.3e-4). Per-judge directional flag rates: anthropic 9.7% (R)
  vs 4.6% (L); openai 18.2% (R) vs 9.8% (L) — both judges ~2.0–2.1x on Right.
- Mechanism (pooled): Right-lean L-sub amplify:strip = 119:39; Left-lean R-sub
  strip:amplify = 53:36. Center articles: R-sub 49 vs L-sub 27 (both centerward-consistent).
- Concentration verified: Sonnet L-sub on Right-lean = 139 verdicts / 51 articles;
  top-20 articles = 69.8% (all-targets 68.2%).

## T1 — Placebo directive, governance hook  [RECOMMENDED — see final ranking]
(a) THESIS: The system-prompt neutrality directive that 2025 U.S. procurement
guidance accepts as compliance evidence is a behavioral placebo: it leaves the
model's decisions statistically equivalent, leaves the political drift itself
equivalent to zero within ±5pp, and its only reliable measured product is
longer explanations.
(b) EVIDENCE: H28 TOST +0.69 detections/article, 90% CI [0.48,0.90], equivalent
at ±1.0 (p=.007), judge-free; H29 lean-label κ=.900 [.864,.932] ≥ .85 floor,
judge-free; drift present at baseline (+9.4pp Sonnet p=.007; pooled +4.4pp
p=.032) and significant under every arm; directive's nominal elevation of the
asymmetry is a length artifact (dev log: sign flips under length control);
rationales lengthen +18 to +65 words under the directive; OMB M-26-04 accepts
system-prompt disclosure as neutrality evidence (paper §Discussion).
(c) NEW ANALYSIS (RUN): the drift-rate equivalence TOST above — the directive's
effect on the politically directional behavior itself is +0.26pp
[−2.09,+2.61], TOST ±5pp p=.0005. This closes the loop: the directive is
equivalence-bounded on BOTH decisions (judge-free) and drift (judged).
(d) STRONGEST OBJECTION: "placebo" overclaims — the directive is not literally
null (+0.69 detections ≈ +10%; label κ .915 vs re-run ceiling .960; and the
drift-TOST rides the κ=.255 instrument). SURVIVES with wording discipline:
claim "equivalence-bounded at the registered SESOI," not "no effect"; the
decision-side tests are judge-free so judge-κ and human-arbitration attacks
don't reach them; RD threshold noise is condition-blind, so it attenuates
rather than manufactures a directive effect. Model-specificity: inertness
replicated on both targets (H28/H29 pooled, stable per target). Register-
normalization rival is irrelevant to inertness (it explains the default, not
the directive's failure to move it).

## T2 — Bias lives in the paraphrase, not the verdict (dissociation)
(a) THESIS: In a frontier model, measurable political bias resides in the
paraphrase, not the verdict: the same outputs whose decisions are politically
symmetric re-voice right-leaning sources in left-coded vocabulary at ~2x the
mirror rate.
(b) EVIDENCE: decisions symmetric — detection volume balanced (L 5.96 vs R 6.38,
p=.40), content check −2.5pp CI [−14.0,+9.3], labels stable κ=.90; rationales
asymmetric — 11.0% vs 5.8% (p=.0014, permutation p≤1e-4), each judge family
independently significant (+4.0pp p=.006; +6.4pp p=.004), judge-free lexicon
corroboration (+7.5pp p=.04 Sonnet; +5.8pp p=.03 pooled), both-judge-agreed
floor +2.8pp (p=.005), not-misperception 19.7% vs 7.5% (p=.0012), 8/8 themes
positive (Sonnet).
(c) NEW ANALYSIS (queued, batch 2): item-level co-occurrence — among rationales
judged left-substituting on right-lean sources, what fraction sit in the SAME
output as a correct right-of-center lean verdict (the dissociation inside a
single JSON object).
(d) STRONGEST OBJECTION: κ=.255 + pending human arbitration. PARTLY SURVIVES:
per-judge independent significance, 93.5% sign agreement, judge-free lexicon,
and the +2.8pp both-agreed floor bound the attack, but the panel (DA-C2) makes
human arbitration load-bearing — thesis must carry "pending arbitration" and
"confined to one of two targets" (Sonnet +10.1pp vs GPT-4.1 +0.1pp, interaction
CI [+4.7,+15.4]) or it overclaims "frontier models."

## T3 — Political bias as style-guide vocabulary (institutional renaming)
(a) THESIS: The measured leftward drift is anatomically a style guide, not an
ideology: additive institutional renaming of contested referents
("undocumented," "reproductive rights," "gender-affirming care"), concentrated
in 20 articles that carry ~70% of it.
(b) EVIDENCE: top-added terms are institutional renamings (paper Finding 6);
amplify:strip 119:39 on right-lean (3:1 additive) vs strip-dominant mirror
53:36; top-20 = 69.8% (verified); persistence: 16 articles drift in ≥3/5
conditions; triggers skew to high-intensity full-Right combative outlets.
(c) NEW ANALYSIS: none cheap that discriminates — the registered discriminating
test (mirrored-vocabulary turnabout) was deferred and NOT run.
(d) STRONGEST OBJECTION: fatal as a thesis — this IS the register-normalization
rival (DA-M5), explicitly unadjudicated in the paper; the mechanism subfield is
ungated (79% raw agreement, R1-M6 demoted it from the abstract); asserting
"it's just house style" is exactly as unsupported as asserting "it's politics."
DOES NOT SURVIVE as a standalone thesis; survives only as the anatomy section
of T2 with both readings stated.

## T4 — Compliance theater index
(a) THESIS: Compliance theater is measurable: the neutrality directive buys
+18–65 words of explanation per output and zero equivalence-bounded behavioral
change — a words-per-behavior-change index any auditor can compute.
(b) EVIDENCE: rationale lengthening (deterministic word counts); H28/H29;
batch-1 drift TOST (+0.26pp [−2.09,+2.61]).
(c) NEW ANALYSIS (queued, batch 2): exact Δwords reframing−ablation per target
from eval-c rollouts, to state the index numerically.
(d) STRONGEST OBJECTION: "theater"/"performs compliance" resurrects the demoted
H27 claim (panel DA-C1/R3-W4: the instruments that would establish PERFORMED
neutrality failed their gates; the single-judge VAR trend carries no
evidential weight). PARTLY SURVIVES only if stripped to its deterministic core
("the directive's one reliable effect is more words"), at which point it is
T1's sharpest sub-claim rather than its own paper. Fold into T1.

## T5 — Confidence already knows (routing rule) / the observability split
(a) THESIS: The model's own confidence already flags its one decision-level
political failure (Lean-Right→Center is its lowest-confidence error cell) yet
is provably silent on its rationale drift — so self-monitoring can route half
the problem and is structurally blind to the other half.
(b) EVIDENCE: LR→Center errors .82 vs .85 other errors, p<1e-6 (Sonnet .77);
within-article drifted vs non-drifted confidence Δ=+0.002, p=.77; all four
models compress Lean Right by 0.6–1.1 classes (Table 5); 33/198 articles defeat
all four models (7.8x independence).
(c) NEW ANALYSIS (queued, batch 2): routing operating point — AUC of confidence
for LR→Center errors + capture rate at a concrete threshold.
(d) STRONGEST OBJECTION: Finding-5 is exploratory, non-registered, and inherits
AllSides outlet labels as ground truth (though uniform label noise cannot
produce one-sided compression). SURVIVES as a deployable-note thesis but reads
product-y for ICLR; the observability-split framing (self-report blindness) is
the defensible scientific core and is already T1/T2 territory.

## T6 — The auditors share the defect (ecosystem circularity)
(a) THESIS: Every frontier model in the audit loop — two targets and two
cross-family judges alike — compresses Lean-Right toward Center, so LLM-judged
"neutrality" audits are structurally circular and require judge-free anchors
plus human arbitration to mean anything.
(b) EVIDENCE: signed error on Lean Right: targets −0.75/−0.64, judges
−0.65/−1.05 (Table 5, two families); judge threshold disagreement is itself
lean-dependent (one-judge-flags 17.8% R vs 10.9% L, chi2 p=1.3e-4 — verified
batch 1); both judges flag right-lean items ~2x more (anthropic 9.7 vs 4.6;
openai 18.2 vs 9.8); concurrent kennedy2026 scores with a single fixed LLM
evaluator — the exact instrument class shown here to fail gates 2/3 of the time.
(c) NEW ANALYSIS: none needed beyond batch 1 (flag-rate asymmetry per judge).
(d) STRONGEST OBJECTION: higher judge flag rates on right-lean items are
CONSISTENT with real target drift (judges detecting a real signal), so only
the judges' own classification compression (Table 5) is independent evidence,
and it is exploratory + label-inheriting. PARTLY SURVIVES: strong as the
motivation for gates/judge-free anchors (synergizes with Finding 1 and the
0/25 survey), too underpowered to headline alone.
