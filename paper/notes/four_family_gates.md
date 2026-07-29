# Four-family gate reliability (Qwen + DeepSeek-V3.2 added) — 2026-07-27

Ran RD/VAR/FDC judge instruments with the two open models. RD complete;
VAR partial (12,355/27,710 — conclusive); FDC crashed on a code bug
(KeyError 'fdc_schema' in assemble; produced 0 ext rows — needs fix+rerun).

## RD (directional substitution) — the SURVIVING instrument does NOT generalize
Raw 4-label kappa is base-rate-suppressed; the real story is base rates +
sign agreement.

Directional base rate per family (how often each flags ANY direction):
  anthropic 9.5% | openai 20.7% | qwen 45.5% | deepseek 10.6%   (n≈2000-2600)
  -> Qwen flags directional substitution ~5x more often than Anthropic. The
     instrument's threshold is wildly judge-dependent.

SIGN agreement on both-directional items (the actual H26 criterion):
  anthropic x openai   82%  (n=142)   <- the original pair (paper: 93.5%)
  anthropic x qwen     71%  (n=108)
  openai    x qwen     66%  (n=151)
  openai    x deepseek 53%  (n=49)
  anthropic x deepseek 50%  (n=30)
  qwen      x deepseek 44%  (n=150)   <- chance

4-label kappa (base-rate dominated, for the record):
  anthropic x openai 0.32; every open-model pair 0.05-0.09.

INTERPRETATION (cuts two ways):
- STRENGTHENS Paper 1 (gates): the instrument that PASSED its gate for the
  Anthropic x OpenAI pair produces near-chance agreement with judges from
  other labs (sign agreement down to 44%; kappa 0.05). This is the strongest
  possible demonstration of the paper's thesis: gate every instrument on the
  exact judge population you will deploy — reliability does NOT transfer
  across vendors.
- CAVEATS H26 (the directional default): H26 rests on the RD instrument judged
  by Anthropic x OpenAI (which agrees best, 82%) + judge-free lexicon
  corroboration. It is NOT refuted, but the four-family data shows the RD
  construct is judge-specific — the directional claim is conditioned on that
  pair and the lexicon, and should say so.
- DeepSeek-V3.2 is a POOR RD judge (near-chance sign agreement 44-53%); Qwen
  is over-sensitive (45% directional). The construct is genuinely hard to
  measure, consistent with the paper's core thesis.

## VAR (framing inheritance) — FAILS across ALL four families (conclusive)
All family-pair kappa ≈ 0 (partial data, but unambiguous):
  a x deepseek 0.027 | a x openai -0.003 | a x qwen 0.037
  deepseek x openai -0.012 | deepseek x qwen 0.057 | openai x qwen -0.012
-> No pair of frontier judges from four labs can agree whether an explanation
   "inherits" source framing. The demotion of framing-inheritance is now a
   FIELD-LEVEL measurement result, not a two-judge quirk. Strong for Paper 1.

## FDC (frame distance, 1-7) — did not run
Code bug: assemble() references column 'fdc_schema' (should be 'schema'?);
KeyError crashed it before any ext verdicts were written. Low priority
(demoted instrument); fix + rerun if the four-family FDC failure is wanted.

## Bottom line
- Paper 1 gates thesis: powerfully strengthened (RD doesn't transfer; VAR
  fails everywhere across 4 labs).
- Paper 2 committee: unaffected (that uses lean labels, clean 4-vendor result).
- H26 directional default: add an honest caveat that RD reliability is
  vendor-pair-specific; the finding stands on the commercial pair + judge-free
  lexicon, not on cross-vendor RD agreement.


## UPDATE 2026-07-28 — VAR complete, FDC partial (all 3 instruments now scored)
- VAR COMPLETE (27,710 verdicts). Full-n family-pair kappa still all ~0:
  a×deepseek 0.031 (n=13851), a×openai -0.003 (n=999), a×qwen 0.051 (n=13847),
  deepseek×openai -0.013, deepseek×qwen 0.066 (n=13851), openai×qwen -0.012.
  Max = 0.066 -> paper should say kappa <= 0.07 (was 0.06). Degenerate confirmed.
- FDC COMPLETE (3974). All family-pair kappa near zero, max 0.134:
  a×deepseek 0.000 (n=1455), a×openai -0.032 (n=2578), a×qwen -0.034 (n=1979),
  deepseek×openai 0.061 (n=1455), deepseek×qwen 0.134 (n=1450), openai×qwen
  0.078 (n=1979). Anchor-divergence failure replicates across all four labs
  (every pair kappa <= 0.13).
- BOTTOM LINE (all 3 instruments, 4 families): the two-family pass/fail pattern
  does NOT survive four families. RD ("pass") does not transfer (0.32 commercial
  pair -> 0.05-0.09 open pairs). VAR + FDC ("fail") replicate as failures across
  all four labs. Gate lesson maximally reinforced.
- ALL THREE INSTRUMENTS COMPLETE across four families (RD 3974, VAR 27710, FDC 3974). Written into p1_disclosure.tex Finding 1.
