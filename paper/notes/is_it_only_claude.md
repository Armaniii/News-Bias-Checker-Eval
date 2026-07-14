# Is the directional default truly only Claude? (2026-07-13, cached-data only)

Motivating concern (panel DA alt-explanation #3): GPT-4.1's judged "null"
(+0.1pp) may be a MEASUREMENT FLOOR, not a true absence — if GPT-4.1 writes
shorter, blander rationales, the AI judge has less to detect.

## Test: break the tie with the JUDGE-FREE lexicon (independent of judge sensitivity)

Per target, eval-C rationales (all conditions, n≈1000 each):

| | mean words | coded-vocab used | JUDGE flag rate | **judge-FREE asymmetry** |
|---|---|---|---|---|
| Claude Sonnet 4.5 | 175 | 50.9% | 18.8% | **+7.5pp** (0.217 vs 0.142), p=.003 |
| GPT-4.1 | **94** | **35.2%** | **11.3%** | **+4.1pp** (0.094 vs 0.053), p≈.01–.06 |

(judge-free asymmetry = P(adds left-coded term | right-lean source) −
P(adds right-coded term | left-lean source); "added" = term in rationale,
absent from source. Point estimate +4.1pp reproduces an earlier independent
run (+4.0pp); its p is significant-to-marginal depending on test spec.)

## Conclusion: NOT only Claude — but ~2x larger in Claude

- GPT-4.1 writes **46% fewer words** (94 vs 175) with **a third less coded
  vocabulary** (35% vs 51%), so the AI judge sees far less to flag
  (11.3% vs 18.8% flag rate). Its judged "+0.1pp null" is **substantially a
  text-length floor**, not a clean absence.
- The judge-free lexicon — which does NOT depend on judge sensitivity —
  finds GPT-4.1 **does carry the same-direction center-ward asymmetry**,
  about **half** the size of Claude's (+4.1pp vs +7.5pp).
- So the honest claim is: **a same-direction directional default is present
  in BOTH frontier models, ~2x larger in one**, not "confined to one model."

## Paper impact
- CURRENT text overclaims: "confined to one model", "GPT-4.1 not detected",
  "in a frontier model, not frontier models per se". SOFTEN to: present in
  both, larger in Claude; GPT-4.1's judged null is partly a length floor,
  and its judge-free asymmetry is same-signed at ~half the magnitude.
- This STRENGTHENS the non-gotcha framing: the phenomenon is field-level
  (both vendors), consistent with Finding 5 (all 4 models compress
  Lean-Right). It is NOT "Claude is biased"; it is "frontier models
  normalize toward center, and one does it more."
- It WEAKENS the clean "GPT shows none → trainable away" existence proof;
  the trainability point survives in magnitude form (2x spread across
  vendors) but not as a clean zero.
- GPT-4.1's terseness is itself a finding: **saying less drifts less-
  detectably** — relevant to both measurement (judges floor on terse text)
  and product design (verbose explanation = more exposure).
