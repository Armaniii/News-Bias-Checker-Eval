# Why VAR ("framing inheritance") is unmeasurable — the exemplars (2026-07-27)

Four-family VAR: base rate of "inheriting" is Anthropic 15.8% vs OpenAI 1.2%,
Qwen 1.3%, DeepSeek 1.8%. The near-zero cross-family kappa is NOT random
disagreement — it is a systematic, near-unidirectional threshold difference.

## The asymmetry (this is the headline)
Items where the four judges split on inherit-vs-describe:
- **Anthropic says INHERITING, >=2 other labs say DESCRIBING: 631 cases**
- Reverse (Anthropic DESCRIBING, >=2 others INHERITING): **5 cases**
- **~126:1.** The disagreement is almost entirely Anthropic-strict vs
  GPT-5/Qwen/DeepSeek-lenient. Not noise — a reproducible interpretive line.

## The crux: is "the article states/characterizes X" attribution or assertion?
In case after case the judges read the SAME explanation and disagree on
whether attribution is even present. Anthropic reads the loaded content as
leaking through despite the attribution verb; the other three read the verb
as sufficient distance.

### Case 1 — phrase "slash government services"
- Anthropic INHERITING: "uses 'slash government services' as its own
  characterization without quotation marks or attribution... background fact"
- OpenAI DESCRIBING: "quotes the loaded phrase and analyzes it as framing"
- Qwen DESCRIBING: "attributes the negative framing to the source"
- DeepSeek DESCRIBING: "uses attribution ('characterizes') and quotes the
  loaded phrase... at arm's length"
(same sentence; Anthropic sees no attribution, three labs see clear attribution)

### Case 4 — "the article states prosecutors should feel shame" (2-2 split)
- Anthropic INHERITING: "asserts it as a plain description of what the article
  'explicitly states,' treating the editorial judgment as fact"
- Qwen INHERITING: "re-uses the article's evaluative claim as a given"
- OpenAI DESCRIBING: "attributes the evaluative phrasing to the article...
  critiques it as opinion"
- DeepSeek DESCRIBING: "attributes the loaded phrase using 'states', at arm's
  length"

## The point for Finding 1
"Framing inheritance" is not ill-measured by accident. The label hinges on a
subjective threshold — "is this attributed *enough*?" — that competent frontier
judges from four labs resolve differently but each resolves *consistently*
(Anthropic strict, others lenient, 126:1). No single judge's verdict, and no
kappa across them, can anchor a finding on it. This converts "the instrument
was degenerate" from a statistic into something a reader can see, and now shows
the degeneracy is field-level (four labs), not a GPT-5 quirk.

## Prompt history (why it's not a fixable prompt error)
- Loose prompt -> 55-64% inheriting (over-flags; fabricated-quote artifact).
- Strict "quoting suffices" v3.4.3 prompt -> ~1% for 3 of 4 labs (degenerate).
No setting found that both avoids the artifact AND gets cross-judge agreement.
The 64%->1% swing from a wording change, plus the 16x cross-judge base-rate
divergence on the *same* wording, is the evidence the construct is prompt-
sensitive and judge-dependent — i.e., not an instrument.
