# Gate Protocol for LLM-Judge Instruments (v1.1)

A pre-committed reliability gate any study using LLM judges can copy into
its workflow. v1.1 incorporates the amendment derived from this study's
own results (step 2–3: bind on the interval, not the point estimate).
Companion paper: "A Directional Default, Not a Directive Effect."

## The protocol

1. **Pair** two judges from *different model families* on identical
   inputs. Same-family pairing leaves self-preference circularity intact.

2. **Score a held-out pilot slice**, excluded from all confirmatory
   analysis, sized so the agreement interval's *lower bound* can clear
   your threshold. n≈40 is decisive only for structural failures
   (zero-variance raters, ceiling anchors); passes at that n are
   provisional.

3. **Pre-commit, in a public registration, before the gate data exist:**
   - the acceptance criterion: agreement interval lower bound ≥ threshold
     (κ ≥ 0.40 is a *screening* floor, not a confirmatory standard —
     content-analysis practice requires α ≥ 0.80 for conclusions);
   - non-degeneracy conditions: no zero-variance rater; no near-ceiling
     single-label marginal (κ is uninterpretable under extreme base
     rates — check AC1 or raw agreement alongside);
   - any direction-quality companion criteria (e.g., sign agreement on
     double-flagged items), with their own minimum n.

4. **One shot.** No iterative re-anchoring of the rubric against gate
   data. A failed gate is an outcome, not a debugging signal.

5. **Register the fallback.** Failing instruments are demoted to
   exploratory per-judge reporting and routed to human arbitration — not
   deleted, not retried until they pass.

6. **Report** the gate estimate *with its interval* wherever the
   instrument's output is used, and grade every downstream claim by the
   instrument's at-scale reliability, not its gate-slice reliability.

## What it costs and what it catches

In the companion study: two judge passes over 40–60 pilot items per
instrument. It failed 2 of 3 plausible, professionally drafted
instruments — including one that had already minted a publishable false
headline (55–64% framing absorption; 0–13% under the corrected rubric;
44.1% of its verdicts failed deterministic evidence-traceability).
In a structured audit of 25 recent LLM-judge-using papers, 0 pre-commit
any acceptance threshold and 1 specifies any fallback.

## Minimum valid use

Results produced with this pipeline but **without freshly passed gates**
(and, for judged constructs, without the human-arbitration layer) are
not findings of this instrument. The analysis code prints an
`UNGATED — NOT A FINDING` banner when gate artifacts are absent.
