# Editorial Decision — Paper 2 ICLR 2027 draft (5-reviewer panel, 2026-08-03)

Panel: EIC (Major Revision) · R1 Methodology (reject-in-form; re-ran everything)
· R2 Domain (weak reject, clear path) · R3 Practitioner (borderline accept)
· DA (recomputed from cache). DECISION: **MAJOR REVISION** — unanimous that the
descriptive core is real and verified, and unanimous that the current
submission is indefensible as-is. Every required fix is reanalysis/writing;
zero new API data required.

## THE GATING FINDING (DA-C1 + R1-W1, independently recomputed by both)
§5/Table 1/Table 2 (router, AUC/AURC, calibration, bias-type kappa) were
computed on a MIXED 299-article set: 200 v3 + ~100 LEGACY articles whose
prompts contained HEADLINE and SOURCE (outlet name) — pre-de-leak April
rollouts. This (a) contradicts Setup's "article text only", (b) explains the
impossible n=299/256 vs N=200, (c) leaks the AllSides label to one-third of
the flagship sample. R1 verified the paper's numbers reproduce EXACTLY and
ONLY on the mixed set.

**v3-only recomputation (R1, independent of DA):** qualitative map SURVIVES
(agree 73.8% vs disagree 33.8%; capture 31.9 vs 26.6 @20%; AURC combined
0.201 < confidence 0.217 < disagreement 0.296) BUT:
- mid-budget significance DIES: @20% +5.3pt p=.054 CI[-1.1,+12.2];
  @30% +5.7pt p=.153 CI[-4.5,+14.5] (article-level clustered bootstrap)
- AUC "tie" becomes point estimate FAVORING confidence: 0.695 vs 0.740,
  diff -0.045, p=.26 — "indistinguishable at this n", not "same information"
- calibration: GPT ECE gap STRENGTHENS on clean data (0.327 vs 0.237)
R1's power-restoring fix (principled): pool the 5 prompt conditions with
article-level clustering (ordering already replicates 5/5).

## CONSENSUS ROADMAP (by priority; reviewer tags)

### P0 — blocking
1. Recompute §5 + Tables 1-2 + AURC v3-only; segregate/quarantine legacy
   rollouts in release; add §3 data-accounting paragraph defining every n
   (DA-C1, R1-W1, EIC-W8). Pool conditions w/ clustering for power (R1-W2).
2. Commit the missing analysis scripts (triage router, AURC, calibration) —
   Reproducibility Statement currently false (DA-C3, R1-W5). Define tie-break
   convention + error unit; report tie-break range 23.9-50.4% (R1-W4).
3. Restore the two verification-mandated caveats: structural 0.5 cap on
   disagreement accuracy + Holm-fragility ("directional, in-budget")
   (EIC-W1, DA-C2, R1-W4). Remove "significantly...p<.05" from abstract.
4. Fix abstract overclaims: "Every result holds across five conditions" →
   "the two headline results" (EIC-W2, DA-C4); "all statistics carry
   bootstrap CIs" → "headline statistics" or add CIs (R1-W6);
   "expert-rated" → "AllSides-rated / outlet-anchored" (R2-W4, DA-m5).
5. Fix the backwards label-artifact logic IN BOTH PAPERS: cross-vendor
   replication rules out single-vendor quirks only; it CANNOT discriminate
   label error from shared training bias (R2-W3, DA-M4). Claim becomes
   "robust across vendors, unresolved against label error". P1 has the same
   sentence — fix there too.
6. "cost-free/free" → "label-free (at the cost of a second model call)" +
   the cents-vs-dollars economics sentence (ALL FIVE reviewers).

### P1 — major
7. Figures: risk-coverage curves (disagree/conf/combined/random/oracle,
   20-30% shaded) + per-class heatmap or decision flowchart w/ operating
   points + costs (EIC-W3, R3-W3, R3 special charge).
8. Prior art: QBC (Seung'92), deep ensembles (Lakshminarayanan'17),
   Jiang'22 disagreement-predicts-error, SelfCheckGPT (= the "future work"
   that already exists), Verga panels; verbalized-confidence (Tian'23,
   Xiong'23/24); BASIL/MFC for the map's organizing split; FIFO for framing
   rows; CiteGuard-line to bound the unsupported-claims recommendation
   (EIC-W4/W5, R2-W1/W2/W5/W6/W7, DA-M6). Reposition contributions: map =
   "quantification for frontier models of the known lexical/informational
   split"; router = "first careful head-to-head of committee disagreement
   vs calibrated confidence on this task, with operating curves".
9. Fix the circular routing trigger — replace with observable committee-split
   trigger (R3-W1, DA-M3); ADD the unanimous-error class-composition table
   (does the gate auto-clear Lean-Right misreads?) (DA-M3).
10. "All six models hardest on Lean-Right" → "shared in direction,
    heterogeneous in magnitude, strongest in Claude"; per-class Wilson CIs
    in Table 3 (EIC-W9, R2-W9, DA-M7, R1-W6). Label 4-model committee
    "two-vendor"; foreground the 6-model/4-lab gate (DA-M8).
11. Ethics Statement: escalation-not-reweighting, contested ground truth,
    dual use (R3-W4, EIC-W11). Companion protocol as anonymized supplementary
    + self-contained appendix (EIC-W7, R3-W8).
12. Free analyses: boundary-exclusion check on Lean-Right cell (R1);
    router on other conditions + 2-of-4 committee (EIC-W10); model-version
    sensitivity note (Sonnet 4.5→4.6 shift = re-derive per update) (R3-W6);
    residual review-load numbers (R3-W7).

### P2 — minor
p=.053 not ".05" (R1-W7); "0.9 means ~75%" bin definition (R1-W8); "validated"
→ "benchmarked" (EIC special charge); Kennedy delta detail + shared-label
caveat at point of claim (R2-W8); cut/one-line the orphan lexicon paragraph
(DA-m3); serving-stack note for HF judges + n=198 attrition (DA-m4); abstract
number-count halved, §5 split at AURC pivot (EIC-W12); uncited bib carryover
cleanup (R2-W10).

## What the panel PRAISED (keep)
Four-family replication reproduces to the decimal (R1); ensemble null
"exemplary practice"; prompt-invariance clean; continuous-rating honesty
(F5 trap avoided); text-only design (S5, R2); matter-of-fact exploratory
register; the map's descriptive value ("honest, useful engineering
measurements" — DA's only FAILED attack).

## Cheapest upgrades toward clear accept (unchanged from swarm)
(1) human re-rating of just the 40 Lean-Right articles (the only cell the
flagship directional claim needs) or a second provider; (2) single-model
self-consistency baseline (SelfCheckGPT-style) — now mandatory context anyway.
