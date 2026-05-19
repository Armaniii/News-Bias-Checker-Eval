# Paper Framing & Positioning

> Living strategy document. Synthesizes literature review (Opus agent, 2026-05-07),
> existing analyses, and venue-fit recommendations. Updated as findings shift.

**Last updated:** 2026-05-07
**Maintainer:** Arman Irani

---

## TL;DR — the proposed framing

**Lead pitch (alignment-relevant, field-defining):**

> *"AI political neutrality, as currently measured (including in Anthropic's own
> paired-prompts evaluation), is a thin instruction-following layer rather than
> a deeply trained property. We show that removing a single sentence from a
> summarization system prompt triples bias absorption, and that the magnitude
> of this effect is family-asymmetric. We further show that current single-judge
> evaluations of LLM media-bias behavior systematically advantage the judge's
> own family, contaminating the leaderboards used to claim 'less biased' models."*

This positions us:
- **Against** the most-cited corporate alignment artifact of late 2025 (Anthropic's `political-neutrality-eval`, Nov 2025)
- **In dialogue with** Constitutional AI, Bloom auto-evals, "Refusal Mediated by a Single Direction" (Arditi et al., NeurIPS 2024)
- **As a methodological contribution to** AI for media bias (cross-family judging is necessary infrastructure)
- **As field-defining** if we add the multi-source synthesis benchmark

Recommended target venues, in priority order:
1. **NeurIPS 2026 (alignment/safety track)** — primary
2. **ICLR 2027** — fallback if NeurIPS rejects
3. **FAccT 2027** — methodology angle
4. **Anthropic Alignment Science Blog** — high-visibility companion piece

---

## Where the field is right now

### Bias-detection benchmarks (the encoder-side terrain)

Authors who own this space: Spinde/Gipp lab (BABE, MAGPIE, Annolexical), Wessel et al. (MBIB), BiasLab.
Recent flagship: **MAGPIE** (Horych et al., LREC-COLING 2024) — 59-task multi-task bias-detection mixture.
**Don't compete here.** This is encoder-fine-tuning territory; our frontier-LLM evaluation is orthogonal.

### LLM-as-judge bias

Owned by: Zheng et al. (MT-Bench, NeurIPS 2023), Panickssery et al. (NeurIPS 2024), Wataoka et al. (NeurIPS 2024).
Recent: "Self-Preference Bias is Mediated by Perplexity" (2024), "Justice or Prejudice?" (2024), "Play Favorites" (Aug 2025).
**Our contribution to this lineage:** first cross-family-judge demonstration *in a sociopolitical evaluation domain*.

### LLM political-bias auditing

Owned by: Santurkar et al. (OpinionQA, ICML 2023), Rozado (PLOS One 2024), Motoki (Public Choice 2024).
Recent flagship: **"Left, Right, or Center? Evaluating LLM Framing in News Classification and Generation"** (Kennedy et al., arXiv 2601.05835, January 2026) — direct competitor.
**Critical positioning:** Their question is "what bias do LLMs *default to*"; ours is "how *instruction-controllable* is bias output." Different axis.

### Multi-source synthesis (UNDERSERVED)

Owned by: NeuS (Lee et al., NAACL 2022) — the only major precedent.
Pre-dates frontier LLMs entirely. **Open territory.**

### The Anthropic political-neutrality-eval

Released Nov 2025 (anthropic.com/news/political-even-handedness, github.com/anthropics/political-neutrality-eval). Paired-prompts methodology, 6 task categories × 150 topics, even-handedness/refusal/hedging metrics.
**Direct opportunity for positioning.** Their methodology assumes paired prompts under identical templates. Ours studies the orthogonal axis: how does instruction perturbation differentially shape behavior across families? This complement is publishable on its own.

---

## What our findings actually support, ranked by strength

### Tier S — confirmed, strong, headline-worthy

**S1. Instruction-controllability of bias absorption.** Eval B 3-arm condition analysis. Removing "be neutral, do not adopt framing" triples absorption suppression (combined LMM, OR=3.13, p<0.001). Targets converge under baseline; diverge under full. (NF-3 extended)

**S2. Cross-family judge favoritism.** Eval C interaction β=−1.42 [−1.90, −0.94], p<0.0001. Confirmed in pre-registered FDR-corrected family. First demonstration in sociopolitical-evaluation domain.

**S3. Three-factor structure of bias scoring.** EFA on Eval B custom_scores collapses 12 bias types to 3 latent factors (structural / epistemic / lexical). The "GPT-4.1 less biased" effect lives in structural (β=−0.57, p=0.001), null in epistemic, slightly inverted in lexical. (NF-11)

### Tier A — confirmed, supporting findings

**A1. Generation > absorption when summary clearly biased.** Models invent more new bias than they parrot from sources at threshold ≥ 5. (NF-3)

**A2. Continuous fidelity correlation: instruction dampens, not decouples.** Source–summary correlations remain ~0.13–0.29 across all conditions (positive, significant), but slope drops from ~0.20 (baseline) to ~0.13 (full). The model still tracks source bias *direction*; the instruction dampens its *response amplitude*.

**A3. Eval B target main effect is instruction-following compliance.** GPT-4.1's lower BPS (β=−0.41, p_FDR=0.0003) only manifests under explicit neutrality instruction; baseline shows no significant target effect.

### Tier B — exploratory / null but informative

**B1. Bias-direction asymmetry null.** No detectable target asymmetry in flagging left-coded vs right-coded language. Power-limited (lexicon coverage ~7%).

**B2. Attribution-rule × direction null.** Removing the attribution rule does NOT asymmetrically inflate flagging by political direction.

**B3. Detection P/R/F1 trade-off.** Sonnet has higher recall (β=−0.095, p=0.017), GPT-4.1 has numerically higher precision; F1 identical (~0.78).

---

## The multi-source synthesis benchmark — strong recommendation: BUILD IT

### Why it's the right move

1. **Genuinely underserved.** NeuS (NAACL 2022) is the only precedent and pre-dates instruction-tuned frontier models entirely. There's no published frontier-LLM benchmark of multi-source synthesis bias.
2. **Real-world relevance.** Mirrors AllSides Headline Roundups and Ground.News Blindspot — products people actually use. Reviewers like benchmarks tied to deployed systems.
3. **Methodologically novel.** Lets us measure "balance" as a property of synthesis rather than as an absence of bias in single-source summaries.
4. **Pairs naturally with our headline findings.** Instruction-controllability + cross-family judging show up MORE STARKLY in synthesis (more dimensions of behavior to vary).

### How to do it well (per the agent's analysis)

- **200–400 events** for venue-paper scope; 30 events is fine for pilot-bullet.
- **Named-entity-balanced sampling** to avoid single-figure confounds.
- **Input-order randomization** as a control — order effects are real (cf. Input Order Shapes LLM Semantic Alignment, arXiv 2512.02665).
- **Two metrics**: (a) blind-applied L/C/R lean classifier on the synthesis (use our existing Eval C scaffolding); (b) "frame share" measured atomically à la FActScore against per-source claim sets.
- **Per-event variance** must be reported. A model that averages to balanced by alternating L-favoring and R-favoring across events is NOT balanced.

### Estimated cost

- Dataset construction: ~$50 (3 articles × 200 events × scraping + cleaning, mostly automated via AllSides roundups)
- Model rollouts: 200 events × 2 targets × 1 condition (synthesis prompt) ≈ 400 calls × ~$0.04 (longer context with 3 articles) = **~$15–25**
- Judgment by both judges: 400 × 2 × ~$0.05 = **~$40**
- Optional: condition variants (default / "balanced synthesis" / "neutral synthesis") = 3× the rollout cost ≈ **+$45**
- **Total: ~$100–150** for the full benchmark

### Predicted findings (if we run this)

Based on what we've already shown:
1. **Synthesis fidelity is condition-controllable** — same directional finding as Eval B but more dramatic
2. **Synthesis lean drift exists and is family-asymmetric** — Sonnet's syntheses may lean differently than GPT-4.1's
3. **Cross-family judge × synthesis bias interaction is large** — current Eval C interaction was 1.42 lean-class units; expect similar or larger
4. **Per-event variance is high** — averages-to-balanced is misleading

Each of these is publishable on its own. The PACKAGE is field-defining.

---

## Interpretability angle — strong recommended add-on

The agent flagged this as the highest-leverage interpretability extension:

### SAE feature-steering ablation

**What:** Anthropic has published SAE features for "Pro-life and anti-abortion" and "Left-wing political ideologies" (anthropic.com/research/evaluating-feature-steering). Use these features as a steering control: instead of (or alongside) prompting "be neutral," steer the corresponding feature(s).

**Hypothesis test:** If feature-steering produces the same absorption-suppression effect as the neutrality prompt, the neutrality instruction is operating through these features. If they differ substantially, the instruction is engaging a more diffuse pathway.

**Why this is publishable:**
- **Either result is informative.** Match → mechanistic explanation of the prompt effect. Mismatch → instructions and features dissociate, suggesting "instruction-following" is its own thing not reducible to value features.
- **Connects to flagship interpretability work** — Arditi et al. NeurIPS 2024 ("Refusal Mediated by Single Direction") is the exact intellectual lineage.
- **Uses already-released SAE features** — no need to train your own SAEs.

**Cost:** Modest. Requires Anthropic API access to a model with feature-steering. ~$50–100 of API + ~10 hours of code.

**Risk:** Anthropic may not have the relevant features available for the public API. Mitigation: use the Sparse Autoencoder release on Llama 3 (Goodfire AI) or train a small SAE on a smaller open model.

---

## Three pitch candidates, ranked

### Pitch A: "Instruction-Controllable Bias" (RECOMMENDED, alignment lead)

> Bias in LLM news handling is instruction-controllable, and the controllability
> is family-asymmetric. Removing one sentence from the system prompt triples
> bias absorption (OR=3.13). The 'less biased model' finding decomposes into
> instruction-compliance gradients. Single-judge evaluations of LLM political
> behavior systematically favor the judge's own family by 1.4 lean-class units.

**Venue fit:** NeurIPS 2026 / ICLR 2027 (alignment track), Anthropic Alignment Science Blog.
**Strength:** Positions vs Anthropic's own paired-prompts evaluation; clean alignment-relevant claim; field-defining if paired with synthesis benchmark.
**Risk:** Requires careful hedging on "neutrality is value-shaped vs surface-shaped" — mechanistic interpretability extension would strengthen the claim.

### Pitch B: "Audit Methodology" (durable, narrower)

> Cross-family LLM-as-judge is necessary for fair evaluation of LLM political
> behavior. Single-judge evaluations of media-bias tasks systematically advantage
> the judge's own family. This contaminates current model cards and corporate
> political-neutrality benchmarks.

**Venue fit:** FAccT, AIES, Nature Machine Intelligence (short).
**Strength:** Methodology recommendation is widely cited; durable contribution.
**Risk:** Author becomes "the cross-family judge person" — narrower thought leadership.

### Pitch C: "Synthesis-First" (most ambitious, most field-defining)

> Real-world LLM media impact runs through synthesis, not detection. We
> introduce the first frontier-LLM benchmark of multi-source synthesis bias
> using AllSides headline roundups, and show three findings that change the
> field: (1) frontier LLMs invent more bias than they inherit; (2)
> instruction-following dominates default ideological lean; (3) cross-family
> judges are necessary infrastructure. Detection benchmarks measured the
> wrong thing.

**Venue fit:** NeurIPS Datasets & Benchmarks, NAACL/ACL main, Science / Nature MI commentary.
**Strength:** Highest impact; flag-planting; defines the next research generation.
**Risk:** Requires the synthesis benchmark to be substantial (200+ events, ~$150 budget).

### Recommendation: Pitch A as headline, integrate Pitch C as methodological backbone

Lead with Pitch A's framing in the abstract and intro. Use Pitch C's synthesis benchmark as the empirical setting. Derive the instruction-controllability finding from that setting. Cite Pitch B's cross-family-judge result as a supporting methodology contribution.

This gives you a paper that:
- Reads as alignment/safety to alignment-track reviewers
- Reads as a benchmark contribution to ACL/NAACL reviewers
- Provides methodological guidance to FAccT-style reviewers
- Has a clean elevator pitch for journalists / policy

---

## Concrete next-step priorities

| Priority | Action | Cost | Status |
|---|---|---|---|
| P1 | Build multi-source synthesis benchmark (pilot 30 events) | ~$30 | proposed |
| P2 | SAE feature-steering ablation (pilot) | ~$50 | proposed |
| P3 | Continuous fidelity correlation per condition | done | ✓ implemented |
| P4 | Per-construct factor analysis | done | ✓ implemented |
| P5 | Write paper outline using Pitch A framing | — | proposed |
| P6 | Re-do all figures using factor-level analysis | — | proposed |
| P7 | Add explicit "vs Anthropic political-neutrality-eval" methodology section | — | proposed |
| P8 | Headline-only Eval C robustness check | ~$5 | proposed |

---

## What NOT to do

Per the agent's strong recommendations:

1. **Do NOT lead with Eval A.** 15-bias-type detection is the most replicated terrain (BABE/MBIB/MAGPIE/BiasLab/Annolexical). It's the warm-up task in our paper, not the contribution.
2. **Do NOT position as "GPT-4.1 less biased than Sonnet."** Leaderboard finding, will be obsolete in 6 months, and our own decomposition shows it dissolves under instruction conditioning.
3. **Do NOT call it a "comprehensive benchmark."** Frames work as Spinde-lab-style; obscures novelty.
4. **Do NOT skip the explicit positioning vs. the Anthropic political-neutrality-eval.** This is the most-cited corporate artifact of late 2025; not engaging it is a missed opportunity.

---

## Anchor citations (must cite in related work)

- **NeuS** (Lee et al., NAACL 2022, arXiv 2204.04902) — multi-source synthesis prior art
- **MBIB** (Wessel et al., SIGIR 2023, arXiv 2304.13148) — bias-detection benchmark canon
- **MAGPIE** (Horych et al., LREC-COLING 2024, arXiv 2403.07910) — multi-task bias detection
- **BiasLab** (arXiv 2505.16081) — frontier-LLM political-bias evaluation
- **MT-Bench / Self-Preference Bias** (Zheng et al. NeurIPS 2023; Wataoka et al. NeurIPS 2024)
- **Santurkar OpinionQA** (Santurkar et al., ICML 2023, arXiv 2303.17548)
- **Anthropic political-neutrality-eval** (anthropic.com/news/political-even-handedness, Nov 2025)
- **Constitutional AI** (Bai et al., arXiv 2212.08073) — alignment framing
- **Refusal Mediated by Single Direction** (Arditi et al., NeurIPS 2024) — interpretability lineage
- **Bloom auto-evals** (alignment.anthropic.com/2025/bloom-auto-evals/) — Anthropic's behavioral-eval tool
- **FActScore** (Min et al., EMNLP 2023, arXiv 2305.14251) — atomic-decomposition methodology
- **Left, Right, or Center?** (Kennedy et al., arXiv 2601.05835, Jan 2026) — direct competitor
- **Rozado** (PLOS One 2024, doi:10.1371/journal.pone.0306621) — political-bias evaluation lineage

---

## Open questions for the author

1. Are you committed to the alignment angle (Pitch A) as primary, or is media-bias-research-community framing (Pitch C) more aligned with the audience you want?
2. Would adding a co-author with mech-interp expertise be feasible? The SAE feature-steering ablation is significantly stronger with that collaboration.
3. Is the ~$150 budget for the multi-source synthesis benchmark within scope? If not, the 30-event pilot at ~$30 still produces a publishable methods bullet.
4. NeurIPS 2026 deadline is May 15, 2026. Tight but feasible if synthesis benchmark is implemented in next 2 weeks.

---

## Changelog

| Date | Change | By |
|------|--------|----|
| 2026-05-07 | Initial framing document. Synthesizes Opus agent literature review, three pitch candidates, multi-source synthesis recommendation, anchor citations, alignment positioning. | Claude |
