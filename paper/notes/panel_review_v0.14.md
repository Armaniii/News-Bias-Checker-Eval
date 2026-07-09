# Editorial Decision — FRAME Paper 1 v0.14 (5-reviewer panel, 2026-07-08)

Panel: EIC (eval/benchmarking SAC) · R1 Methodology (psychometrics; re-derived all
headline stats + re-ran the verifier) · R2 Domain (political-bias-NLP literature) ·
R3 Perspective (audit/policy) · DA Devil's Advocate (ran adversarial probes on the
released verifier). Every item below traces to a specific reviewer report
(tags: EIC-Wn, R1-Mn/mn, R2-Wn, R3-Wn, DA-Cn/Mn/mn).

## DECISION: MAJOR REVISION
(EIC: Major Revision; R1: Major Revision; R2: 6/10 conditional; R3: weak accept;
DA: 2 CRITICALs → Accept blocked by iron rule.)
Unanimous qualifier: **no reviewer found any threat to the direction of any
reported effect; no required revision needs new data collection** (R1 explicitly;
EIC "driven almost entirely by completeness, not by the science").

## VERDICT ON THE SPECIAL CHARGES

**Framing/narrative (charge 2): HOLDS.** EIC: Finding 1 "lands as a designed
measurement result, not a failure confession." DA verdict table: the
"failed-experiment-rebranded" attack **FAILS (mostly)** — the pre-registered
outcome map (§6.8.4) named the methods-paper branch before the failures existed.
Two seams only: the §4.1 title quantifier ("Most") and the Conclusion's
resurrection of the demoted claim.

**Finding 1 novelty (charge 3): SURVIVES AFTER SCOPING.** R2 steelmanned
Registered Reports / FDA instrument qualification / crowdsourcing gates / Jung
et al. and concluded: "the concept is imported; the demonstration is new. The
paper must say exactly that." Scope the not-aware-of-prior-work sentence to
"in LLM-judge evaluation"; the 0/25 survey then evidences the scoped claim.

**Prevalence survey integration: convincing but non-compliant with the paper's
own standard.** All five tallies verified against the coding log (EIC), but ALL
FIVE reviewers demand dual-coding + fixes (see P1-8).

**46.7% artifact: core stands, number inflated.** DA and R1 independently ran
the verifier. Two real defects found:
- Apostrophe-regex bug: straight `'` treated as quote delimiter → possessives in
  judge prose mint phantom "quoted terms". 54/549 numerator items are pure
  artifacts (DA-M3, R1-M1b).
- Registered-exclusion violation: the 6 identity-contaminated pilot articles
  (PRE_REG §6.8.9) are not excluded; on those, absent quotes are corpus error,
  not judge error (R1-M1a).
- Jointly corrected: **44.1% (466/1,057)** (R1). Also: denominator phrasing
  (1,175 = extractable-quote subset of 1,225 inheriting verdicts); matching runs
  on post-hygiene text_clean, not the as-judged 4,000-char source (R1-M1c,d).
- DA honesty note: encoding/normalization attack FAILED (0/549 rescued); gate
  re-run collapse (53.4%→13.3%/0%) independently corroborates the artifact.

## CONSENSUS MATRIX (items raised independently by ≥2 reviewers)

| Item | Raised by |
|---|---|
| Survey: dual-code, fix "unverifiable" wording, convenience-sample honesty | ALL FIVE |
| Human calibration pending yet load-bearing; "confirmed" needs grading or a pre-committed arbitration rule | EIC-W2, R1-M3/m11, R3-W7, DA-C2 |
| $150 = happy-path compute cost; cost figures don't reconcile with pre-reg budget | EIC-W10, R1-m10, R3-W2, DA-M6 |
| Demoted H27 claim resurrected in Discussion/Conclusion ("rationales responsive") | R3-W4, DA-C1 |
| §4.1 title "Most" overclaims from n=3 correlated instruments | EIC-W3, DA-M1 |
| 46.7% needs correction + hand-audit + judge-vs-corpus split | EIC-W7, R1-M1, DA-M3 |
| H29 BH multiplicity deviates from registered in-family treatment, unlogged | EIC-W6, R1-M4 |
| Bibliography = commented stubs; paper does not compile | EIC-W1, R2-W1 |
| "~10% corrected rate" smooths 13.3%-vs-0% per-judge gap | EIC-W4 (R1-M1 adjacent) |
| Asymmetric restriction in "not misperception" check (19.7% restricted vs 7.3% unrestricted mirror) | R1-m2, DA-m3 |
| Krippendorff/content-analysis canon absent; κ≥0.40 must be framed as screening gate | R3-W3, R2-W2 adjacent |
| Register-normalization (house-style) alternative unexcluded; turnabout test named in pre-reg, not run | DA-M5, R2-W10 adjacent |

## REVISION ROADMAP

### P0 — Blocking (submission invalid without)
1. **Bibliography + style files.** Build references.bib with verified entries
   (kennedy2026left and vallejo2025neutral author lists currently guessed);
   vendor ICLR style; compile. Mandatory adds (R2-W1): Feng 2023, Santurkar,
   Röttger 2024, Motoki, Gentzkow–Shapiro 2010, Baly 2020, Spinde BABE/Hamborg,
   Flake & Fried, Chambers & Tzavella (RR), van Miltenburg (NLP prereg),
   Lakens TOST, Benjamini–Hochberg, judge-bias survey, Panickssery
   (self-preference — currently cross-family rationale is uncited), AlpacaEval,
   Krippendorff (R3-W3), Entman/Chong & Druckman, Raji internal-audit +
   named-system audit norm (R3-W1).
2. **Verifier corrections + paper numbers.** Fix verify_var_artifact.py
   (boundary-aware regex; registered contaminated-article exclusion; state
   denominators; match as-judged text where feasible); update 46.7% → corrected
   rate everywhere with judge-vs-corpus split + sensitivity note; hand-audit ~50
   surviving items (feeds the existing human sheet); soften "rests on no model's
   judgment" → detection deterministic, interpretation pending arbitration
   (DA-M3); cite the 27% quoted-complement error mode (EIC-W7).
3. **Kill the resurrection.** Rewrite Discussion opener + Conclusion to
   Contribution-1 wording: two findings (directive-equivalent decisions;
   directive-INDEPENDENT rationale default), not "rationales responsive"
   (DA-C1, R3-W4). Re-derive the practitioner claim from confirmed components
   only (R3-W4 text provided).
4. **Human-calibration grading.** Pre-commit the arbitration decision rule
   (n, coders, stratification, what sustains/retracts H26) in §3 replacing
   \pending{}; align §3 scope with Limitation 7 (all judged claims, not only
   demoted); add "pending human arbitration" clause to Conclusion (DA-C2,
   EIC-W2, R3-W7, R1-M3). Execute the minimal slice before actual submission.

### P1 — Major (analysis/text, no new data)
5. Retitle §4.1: "Plausible judge instruments can fail calibration
   systematically—and gates catch what inspection does not"; hedge the intro
   prevalence sentence (EIC-W3, DA-M1).
6. Corrected-rate range "0–13% depending on judge, pending arbitration" in
   abstract/intro/§4.1 (EIC-W4).
7. H29 BH: report registered in-family treatment (bootstrap p) alongside;
   log deviation in PRE_REGISTRATION.md (EIC-W6, R1-M4).
8. Survey compliance: user dual-codes the 25 (or stratified subsample) as human
   second coder; report agreement in caption; fix exclusion wording
   (out-of-scope, not unverifiable); "structured audit of a convenience sample";
   label consumer/constructor split post hoc; add rule-of-three CI (~14% upper)
   to the 0/25 claim (ALL FIVE).
9. Novelty scoping + import acknowledgment (Registered Reports, crowdsourcing
   gates, selection-vs-gating distinction w/ AlpacaEval+Tulu3 cites)
   (R2-W2, R2-W9).
10. Delta sentence → explicit joint claim + 3-work × 4-element mini-table
    (R2-W3); Finding 5 ↔ Kennedy engagement paragraph (R2-W4); fix/bound the
    "directionally consistent with their ranking" clause (R2-W5).
11. Magnitude bracketing for H26 (both-agreed +2.8pp floor ↔ pooled +5.2pp;
    judge-dependent absolute rates; distribution-shift hypothesis for κ
    attenuation) (R1-M3, DA-M4).
12. Demote "additive in mechanism" from abstract (mechanism subfield has no
    reported reliability; pilot flagged anchoring on exactly this field)
    (R1-M6).
13. Finding 3 figure + compact results table; break the mega-paragraphs
    (EIC-W5).
14. Boxed protocol card in amended interval-binding form + template file in
    repo; move 0/25 + 11/11 rows next to Finding 1 (R3-W6).
15. Table 1 additions: gate bootstrap CI [0.28,0.85]; n=1 sign-criterion note;
    restate the lesson (interval bounds OR structural-degeneracy diagnostics);
    state the reflexive consequence (bind-on-lower-CI demotes RD too) (R1-M2).
16. $150 → "API costs on the path where gates re-pass; gate failure triggers
    redesign + human arbitration, which dominated actual cost"; reconcile ~$200
    vs pre-reg ~$775 (batch discounts) in Reproducibility (R3-W2, DA-M6,
    R1-m10, EIC-W10).
17. Register-normalization alternative named honestly in Finding 6/Limitations;
    turnabout test flagged as the registered discriminating experiment, future
    work (DA-M5).
18. Audit-regime grounding paragraph (EU AI Act GPAI evals; 2025 US procurement
    neutrality criterion; Raji et al. cites) (R3-W1). Krippendorff + assay
    validation; κ≥0.40 explicitly a screening gate (R3-W3).
19. Minimum-valid-use clause in Ethics/Repro + "UNGATED — NOT A FINDING" banner
    in analysis output when gate artifacts absent (R3-W5). Append
    unvalidated≠false to the burden-inversion sentence (R3-W11).
20. Post-hoc power table for the 3 tests incl. TOST power (label post hoc);
    or disclose deliverable not produced (R1-M5). Report registered D-JA
    intensity-normalized companion or log deviation (R1-m8).

### P2 — Minor batch
21. Symmetric restriction in "not misperception" (restrict mirror to
    correctly-classified left-lean) (R1-m2, DA-m3); verify duplicate p=.0014
    (R1-m3).
22. Exploratory labels at point of use (per-target decomposition, interaction,
    permutation) (R1-m4); label abstract lexicon +7.5pp as Sonnet or use pooled
    (EIC-W12).
23. Denominators: n=399/394 exclusion accounting; 198-vs-200; "0.6–1.0" →
    "0.6–1.1" (EIC-W9, R1-m7).
24. "Replicate exactly" → "within the gate estimate's interval"; 17–50×
    consistency (R1-m9). Pre-reg date typo reconciliation (R1-m6). External
    timestamping: push commit hashes to OSF before review (DA-m5).
25. Register polish: drop §4.1's defensive parenthetical; abstract signaling
    sentence + ~30% trim (EIC-W11). Title plural decision — "a Frontier
    Language Model" or keep w/ body scoping (DA-m1: USER DECISION). Delete
    "trainable away" → "not task- or corpus-forced" (DA-m2).
26. Ethics: copyright basis named + archival plan (R3-W9); AI-disclosure adds
    (AI-proposed vs human-directed analyses; human review of load-bearing
    scripts) (R3-W10); IRB naming when known (R3-W14); AllSides
    parameterization note (R3-W12); SESOI anchoring sentence (R3-W13, DA-m4).

## SCORES
| | EIC | R1 | R2 | R3 |
|---|---|---|---|---|
| | O8 S7 C4 Cl6 | D8 V7 R7 T8 | L4 P6 C8 N7 | P7 E7 X5 M7 |

## STRENGTHS THE PANEL AGREED ON (keep; do not dilute in revision)
- Figure 1 paired exemplars: "best pedagogy in the paper" (R3), "does real
  argumentative work" (EIC), "unusually persuasive" (DA).
- Numerical integrity: every headline stat re-derived exactly (R1).
- Against-interest disclosure discipline: κ attenuation, stratum-differential
  disagreement, n=1 criterion, length-confound self-correction (R1, EIC, DA).
- Anthropic-eval complement positioning + VPEI adoption (R2: "better than
  nearly anything in this literature").
- Prior-panel revisions verified held: retitle, pooled/Sonnet qualifiers,
  article-paired bootstrap (EIC, charge 4; not re-litigated).
