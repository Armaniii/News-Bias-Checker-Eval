# Framing review — tracking document

**Question (2026-07-08):** the draft currently carries a first-person
self-correction narrative ("our best number was an artifact; we killed it;
we corrected our own pass verdict"). That narrative is strong *interview*
material but may be the wrong register for an academic/industry
publication. What is the best framing, based on how high-impact papers
actually handle instrument failure, self-correction, and sensitive
findings?

## Current framing inventory (draft v0.7)

Confessional/author-centric passages:
1. Abstract: "the pilot's most striking number ... proved to be judge
   artifact" — leads with our error before our result.
2. Intro: "We report this trajectory in full not as a confession but as a
   finding" — literally names the confession frame while disclaiming it.
3. Finding 1, obs. 4: "a correction we report against our own pass
   verdict" — author-as-subject.
4. Finding 3 validity paragraph: qualifications framed as our disclosures
   rather than as measured properties of the instrument.
5. Title comment trail, deviations-log citations throughout.

Hypothesis A (phenomenon-first): recast every self-correction as a
measured property of LLM-judge instruments in general, with our study as
the measurement apparatus. "Ungated instruments mint publishable
artifacts" (world-fact) vs "our number was wrong" (author-fact).

Hypothesis B (two-study structure): present Study 1 = instrument
validation experiment (N=3 instruments, pre-committed gates, failure
taxonomy) and Study 2 = the behavioral findings on the surviving
instrument. Failures become Study 1's *results*, not Study 2's
disclaimers.

Hypothesis C (status quo): transparency-as-identity is the
differentiator; first-person costly signals are what make the paper
distinctive. Risk: reads as cover letter / blog register at a venue.

## Agent findings

(to be filled by review agents)

### A. How landmark methods/measurement papers frame instrument failure (COMPLETE)

Surveyed: Schaeffer (Mirage), D'Amour (Underspecification), Gender
Shades, Röttger (Spinning Arrow), Anthropic's honest-negatives trio
(alignment faking / CoT faithfulness / sabotage evals), Perez
model-written evals, Sijtsma (Cronbach's alpha), Flake & Fried,
OSC 2015 reproducibility, Rohrer Loss-of-Confidence Project.

The dominant template (universal across subfields):
1. **Noun the failure** — the failure mode gets a NAME (underspecification,
   mirage, alignment faking, QMPs) and that noun is the subject of title
   + first sentence. Authors enter at sentence 2-3.
2. **Authors are the apparatus, never the culprit** — first person bound
   exclusively to discovery verbs (identify, find, show, measure). No
   successful paper says "we erred" or "not as a confession."
3. Prior wrong beliefs — even the community's own — attributed to
   **generic mechanisms** ("the researcher's choice of metric", "the
   prevailing paradigm").
4. **Failures become results when gated by design** (confirmed
   predictions, pre-committed evals) — implicitly the two-study move.
5. Confessional content has **fixed subordinate slots**: one
   matter-of-fact sentence + dedicated section (Anthropic sabotage
   evals: "We also survey related evaluations we tried and abandoned"),
   abstract-final limitations, appendix deviation logs, errata, or
   retrospective venues (ML Retrospectives = explicitly a blog genre).
Empirical: public first-person self-correction is vanishingly rare
(Rohrer et al. 2021); ML institutionalized it into workshops, not main
tracks. Verdict: Hypothesis A register, with B's "failures as designed
results" achieved implicitly; C's confession register reserved for
talks/blog/interviews.

### B. How high-impact sensitive-finding papers structure title/abstract (COMPLETE)

Surveyed: Feng (ACL best paper), Santurkar OpinionQA, Gentzkow-Shapiro,
Bang 2024, Hartmann (counter-example), Gender Shades + Raji actionable
auditing + Obermeyer, OpenAI + Anthropic self-audits.

Dominant pattern:
- **Title = question / phenomenon / measurement act; never model+direction.**
  Hartmann (the one direction-in-title paper) got virality, lost
  narrative control, aged badly with model updates.
- **Abstract states results plainly but picks the symmetric/comparative
  formulation** for headline billing; directional entity-specific claims
  live in the body with full precision. Hedging is methodological
  (pre-registration, robustness), never rhetorical.
- **Named-entity results: late, comparative, mechanism-class attributed.**
  Santurkar's "some human feedback-tuned LMs" + AI21 null contrast = our
  GPT-4.1 null: leading with the null model converts indictment into
  contingent-training-outcome.
- **Structural anti-weaponization**: symmetric instrument (both-poles
  anchored, like Gentzkow-Shapiro), refuse a single aggregate lean score
  (Bang), anchor to vendor-endorsed norms (both labs published
  even-handedness ideals), pre-publication vendor disclosure (Raji:
  naming-with-disclosure drives remediation), constructive counterfactual
  close (Obermeyer).

## Decision

**ADOPTED (2026-07-08): Option A register via Agent C's 11 local
rewrites + c-class deletions; reject the two-study rebilling (C's
registration-mismatch argument) — Finding 1 already functions as the
validation study's results section. Plus from B: abstract rebuilt on
C's Option A skeleton (divergence-on-symmetric-instrument billing),
mechanism-class attribution kept, single-score refusal kept,
pre-publication vendor-disclosure commitment added to Ethics. The
confessional chronology lives in the deviations log (public
registration) + one matter-of-fact pointer, Anthropic-sabotage-evals
style. The interview/cover-letter register is a SEPARATE artifact and
stays out of the paper.**

### C. Draft-specific inventory + rewrite options (COMPLETE)

Key discovery: **the draft is already ~70% phenomenon-first.** Its best
sentences ("The gates did real work"; "Ungated, this artifact was
publishable"; "Spot-checking cannot catch this; gates did") are already
the target register. The confessional register is concentrated in ~8
passages + 3 adverbs of self-praise ("transparently", "prominently",
"as prominently as its result"). The fix is surgical, not structural.

Inventory: 8 class-(a) passages = necessary first person (design
choices, claim-issuing verdicts, ethics statement — the sanctioned home
for the audit-trail register). 11 class-(b) passages = convertible,
with rewrites drafted (transformation rule: subject = the instrument /
the estimate / the gate, never the authors; every number preserved).
5 class-(c) items = deletable with zero transparency loss, including
the single worst sentence: "not as a confession but as a finding" —
"a paper that must announce it is not confessing is confessing."

Signature rewrites:
- b4 (load-bearing): "We report this trajectory in full not as a
  confession but as a finding:" -> "This trajectory is itself the
  paper's first result:"
- b1: "our most striking number proved to be judge artifact" ->
  "ungated judging had already produced a publishable artifact: an
  apparent 55-64% rate ... which fell to ~10% under an
  evidence-anchored rubric"
- b5: "a rule we enforced against our own study twice" -> "a rule that
  cost this study two of its three instruments"
- b6: "a correction we report against our own pass verdict" -> "the
  pass verdict itself did not survive scale unqualified"
- b9: "by our own standard" -> "under the registered standard"

Structural options assessed:
- OPTION A (phenomenon-first single arc, 11 local rewrites): minimum
  diff; artifact becomes evidence FOR the protocol. Risk: two
  contributions share one arc.
- OPTION B (two-study restructure): failures become Study 1's results —
  but N=3 instruments is thin for "study" billing, and the registration
  was not framed as two studies (creates a narrative-registration
  mismatch the current draft doesn't have).

VERDICT (Agent C): **Option A via the 11 rewrites; reject Option B.**
Decisive argument: the paper's credibility mechanism is structural, not
narrative — gates, registered fallbacks, timestamped history survive
every rewrite untouched. "A reviewer who trusts the registration
doesn't need the confession, and one who doesn't won't be persuaded by
it." The only thing removed is the authors standing between the reader
and the phenomenon.

## Decision

- pending
