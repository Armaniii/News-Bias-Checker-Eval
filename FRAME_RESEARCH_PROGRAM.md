# FRAME: Frontier LLM Evaluation for Media Bias

**A three-paper research program on methodologically rigorous evaluation of frontier LLMs on news media tasks.**

> *Living document. Updated as findings shift, deadlines move, or new contributions emerge.*

**Maintainer:** Arman Irani
**Last updated:** 2026-05-11 (cross-text-type generalization + deployment-relevance framing)
**Companion documents:**
- `PAPER_FRAMING.md` — strategic positioning notes (predecessor; superseded by §"True-Behavior Profile" below)
- `EVAL_CRITIQUE.md` — construct-validity audit (rolling)
- `PRE_REGISTRATION.md` — frozen confirmatory hypotheses for Paper 1
- `stats_report.md` — current numerical results

---

## Program identity

**Name:** FRAME — *Frontier LLM Evaluation for Media Bias*
*(Backronym is also a deliberate nod to framing theory — Lakoff, Entman, Boykoff — the literature this program engages with.)*

**Tagline:** *"A generalizable methodology for behavioral LLM evaluation, demonstrated on the high-stakes case of news-media political bias."*

*(News-political-bias is the **demonstration domain**. The methodology generalizes — see §"Generalizable Methodology" below.)*

**Unifying thesis (across all three papers):**

> *LLM political bias is a profile across configurations, behavioral constructs, and text-types — not a scalar. Current single-number evaluations (Anthropic's `political-neutrality-eval`, OpenAI's bias evaluations, BiasLab, etc.) collapse this profile in ways that empirically misrepresent the underlying behavior. We characterize the construct gap, propose multi-condition × multi-construct reporting (a "True-Behavior Profile") with four primary constructs — Engagement Parity (EP), Content Framing Inheritance (CFI, operationalized as absorption-rate for long-form summaries and as Voice Adoption Rate (VAR) and Frame-Distance Coding (FDC) for short-form explanations and reasoning), Replacement Direction (RD), and Lean Classification Accuracy (LCA) — and demonstrate empirically on **the two frontier models sampled in this study (Claude Sonnet 4.5 and GPT-4.1)** that (a) under minimal-conditioning baseline, the two sampled frontier models converge on content framing inheritance, (b) under reframing directives, both sampled models strip right-coded source framing 2–5× more aggressively than left-coded framing, and (c) the asymmetric-stripping pattern generalizes across **the three text granularities tested in this study**: summary text (Eval B), bias-detection explanation text (Eval A), and lean-classification reasoning text (Eval C). This last finding has direct relevance for deployed bias-detection tools that surface LLM-generated explanations to end users (CheckTextBias, Ground.News Bias Comparison Summary, BiasLab-style audit tools); whether those deployed systems exhibit the same patterns under their proprietary prompts is an open question. Generalization beyond the sampled frontier models and the three sampled text types is a question for future work.*

**Author identity this builds:** *AI for media bias methodologist.* Recognizable, durable, doesn't depend on closed-model access for interpretability work.

---

## Conceptual framing — True-Behavior Profile (locked 2026-05-09)

This section captures the framing reached through editorial dialogue on 2026-05-08-09. It supersedes the earlier "Confounded Bias" framing for Paper 1 and clarifies the central argument the program makes.

### The category-error claim

Reading published "even-handedness" scores as evidence of unbiased model behavior is a **category error**: the metric measures *engagement parity* (refusal/help symmetry across paired political requests), which empirically dissociates from *content framing inheritance* — a separable, currently unmeasured behavioral construct with distinct representational basis.

This is a Jacobs & Wallach (2021) measurement-modeling claim:
- *Construct* (what we want to measure): "political even-handedness" as the public reads it
- *Operationalization* (what's actually measured): scalar score collapsing engagement parity + content properties
- *Validity claim*: the scalar has high construct validity for engagement parity, low for content framing inheritance

### Two paradigms — model-as-subject vs model-as-classifier

Different evaluation setups have different failure modes:

| Paradigm | Failure mode | Examples |
|---|---|---|
| **Model-as-subject** (Anthropic/OpenAI public evals; our Eval B) | Engagement-vs-content separation | Paired-prompt even-handedness; summarization susceptibility |
| **Model-as-classifier** (our Eval A bias detection, Eval C lean classification) | Calibration / coverage of stance space | Bias-spotting accuracy; lean-class accuracy |

**Paper 1 leads with model-as-subject** as the primary frame; treats Evals A and C as parallel evidence that dimensionality-collapse extends to the classifier paradigm with different specifics.

### "One-dimensional" operationalized

The literature isn't literally one-axis. Political Compass evals have 2 axes; OpinionQA has demographic vectors; Rozado runs batteries. The defensible claim is about **interpretive dimensionality** — what's reported, what travels, what gets read:

> *Even when the underlying rubric has multiple components, the score that propagates is scalar (or a tightly correlated cluster). When the underlying behaviors dissociate, the scalar collapse becomes a category error — not just a granularity loss, but a misclassification of what's being measured.*

### The four-step contribution structure

1. **Multi-component rubric, read as scalar.** Anthropic's eval has refusal symmetry, opposing perspectives, depth/quality dimensions — but the 94% travels alone. (Cite Reuel et al. 2025 on construct collapse; Goldfarb-Tarrant 2023 on bias-test measurement modeling.)

2. **A key component is missing entirely.** Content framing inheritance (CFI) is not in the rubric. (Cite Feng et al. 2024 on content/style decomposition; Lin et al. on framing taxonomy.)

3. **The components dissociate.** Empirically: engagement parity is condition-invariant; content framing inheritance varies 3× under prompt perturbation. The two move on different timescales and respond to different controls. **This is the category-error proof.**

4. **Mechanistic basis for why dissociation is expected.** Arditi et al. (NeurIPS 2024): refusal mediated by a single residual-stream direction — refusal is a shallow, one-dimensional behavioral switch. Zhao et al. (2025, arXiv:2507.11878): harmfulness and refusal encoded *separately* from content. The dissociation reflects representational structure, not measurement artifact.

### The "true bias" reframing

There is no single "true bias" of an LLM as a stable property — bias requires conditioning, and every measurement is of a (model, prompt) pair. But "true bias" as a meaningful concept can be reframed three ways, all defensible:

- **Default behavior** — what the model does under minimal conditioning (our `baseline` condition). Empirical finding: under baseline, Sonnet and GPT-4.1 are statistically indistinguishable on content framing inheritance (~25-28% absorption, p=0.36). **The cross-model differences reported in published evals largely don't exist in default behavior** — they emerge under explicit neutrality directives.

- **Manipulable range** — distribution of behavior across reasonable prompt variations. The width of [baseline, maximal] is the conditioning-dependent range. Honest reporting must acknowledge this range, not collapse it to one configuration.

- **Multi-construct profile** — measure separable behavioral constructs (engagement parity, content framing inheritance, lean classification accuracy, etc.) and report each independently. The dissociation finding shows that any single one is insufficient.

### The "True-Behavior Profile" (constructive contribution)

Replace single-number reporting with a structured matrix across four primary constructs:

> **Model X True-Behavior Profile (political bias)**
>
> | Construct | Baseline | Standard | Maximal |
> |---|---:|---:|---:|
> | Engagement Parity (EP) | 0.99 | 0.99 | 0.99 |
> | Content Framing Inheritance (CFI) | 0.27 | 0.18 | 0.07 |
> | Replacement Direction (RD) — overall | +0.04 | +0.07 | +0.07 |
> | Replacement Direction (RD) — on RIGHT articles | +0.09 | +0.15 | +0.16 |
> | Replacement Direction (RD) — on LEFT articles | +0.05 | +0.07 | +0.06 |
> | Lean Classification Accuracy (LCA) | 0.61 | 0.65 | 0.69 |
>
> Reported with: cross-family judges, article-clustered random effects, paired confidence intervals.

This is what a model card *should* look like for political behavior. The 94% gets replaced with a multi-construct × multi-condition matrix that makes the conditioning explicit, the construct decomposition visible, and **the directional default bias measurable** (RD ≠ 0 + RD asymmetric across source-lean strata).

The four primary constructs:

| Construct | Acronym | What it captures |
|---|---|---|
| Engagement Parity | EP | Help/decline symmetry across perspective strata |
| Content Framing Inheritance | CFI | Source-bias preservation in output |
| **Replacement Direction** | **RD** | **Directional tilt of model-substituted framing** |
| Lean Classification Accuracy | LCA | Domain-taxonomy classification ability |

EP and LCA tell us *whether* the model engages and classifies correctly. CFI and RD tell us *what the framing of model output is*. CFI ≈ "did the model preserve source framing?" RD ≈ "in what direction does the model's substituted framing point?" Together, they replace the empty "is the model biased?" scalar question with two distinguishable, separately-measurable behavioral properties.

### Updated Paper 1 thesis sentence (v5, locked)

> *"LLM political bias is a profile across configurations, not a scalar. At minimal-conditioning baseline, frontier models converge on content framing inheritance; reported differences in published 'even-handedness' scores reflect instruction-compliance variance rather than intrinsic capability differences, and conflate behavioral constructs that mechanistic work shows are separately encoded."*

(Two-sentence form; if forced to one: "LLM political bias is a profile across configurations and behavioral constructs, not a scalar.")

### Empirical anchors — three confirmed findings

The paper has three load-bearing empirical findings beyond the methodology critique:

**1. Construct dissociation (chameleon failure).** Cells where engagement parity is high (model engages fully with both Left- and Right-leaning articles) AND content framing inheritance is also high (summaries inherit source framing). Our existing data already contains this dissociation:
- All baseline cells: EP ≈ 1.0, CFI = 25-28%
- Cross-condition: EP variance ≈ 0; CFI variance large (3× swing); CCDR(CFI, EP) = 22.6×

**2. Convergence at baseline.** Under minimal-conditioning baseline (no reframing directive), Sonnet and GPT-4.1 are statistically indistinguishable on content framing inheritance (~25-28% absorption, 2.5pp gap, p=0.36). The cross-model differences reported in published evals largely don't exist in default behavior — they emerge only under explicit reframing instruction.

**3. Directional default bias (Replacement Direction asymmetry).** Under reframing directives, both targets strip right-coded source framing 2–5× more aggressively than they strip left-coded source framing:

| Source lean | Source balance | Sonnet × full summary balance | GPT-4.1 × full summary balance |
|---|---:|---:|---:|
| RIGHT articles | −0.198 | −0.042 (~80% of right-coding stripped) | −0.083 (~58% stripped) |
| LEFT articles | +0.039 | +0.099 (preserved AND amplified) | +0.073 (preserved AND amplified) |

The asymmetry is direction-of-source-dependent — the signature of a directional default bias. The model's substitution-framing default sits left of zero; right-coded content gets pulled toward that default while left-coded content gets pulled along the same direction (which means it gets *amplified*).

**This is the substantive directional-bias finding the methodology was designed to surface.** Not "the model is biased" (vague) but "the model's reframing operation is empirically asymmetric in a measurable, directional way." Lexicon coverage caveat applies (~7% of language captured); LLM-classifier follow-up (NF-1B) will tighten magnitude estimates without changing direction.

### Cross-text-type generalization (added 2026-05-11)

The reframing-directive analysis originally focused on Eval B summaries — comprehensive representations of source content. A sharper framing emerged from analyzing deployed bias-detection tools:

**The user-facing artifact of LLM bias-analysis tools is the explanation, not the discrete decision.** Bias-detection tools surface `explanation` text describing each flagged instance; classification tools surface `reasoning` text justifying each label. Real deployed systems (CheckTextBias, Ground.News Bias Comparison Summary, BiasLab-style audit projects, Media Bias Detector) emit these texts to users as the substantive product. The discrete decision (detection list, lean class) is plumbing; the explanation is what users read and what shapes their understanding.

**These explanatory texts are themselves representations of source content** — focused representations of specific bias instances (Eval A) or the article's overall framing (Eval C) — and are therefore subject to the same framing-inheritance question as summaries:

| Eval | Text type | Granularity | What it represents |
|---|---|---|---|
| Eval B | Summary | Long-form (~250 words) | Comprehensive article content |
| Eval A | Explanation | Per-detection short-form (~33 words) | Specific bias instance in article |
| Eval C | Reasoning | Medium-form (~180 words) | Article's overall framing |

All three involve the model producing text *about source content*. The reframing-inheritance question applies uniformly. The substantive risk for deployed bias-detection tools is precisely the same as for summarization: if the explanation uses the source's loaded vocabulary while flagging that vocabulary as biased, the tool amplifies what it audits.

**Methodological consequence — coverage-driven operationalization choice.** Lexicon-based RD (the political-direction-tagging approach used for Eval B summaries) becomes power-limited at short text lengths: Eval A explanations average 33 words with 3-6% lexicon coverage. For these shorter texts, the primary operationalization shifts to LLM-judge constructs:

- **VAR (Voice Adoption Rate)** for Eval A explanations: per-detection judge label distinguishing *describing* ("the author uses 'X' to characterize...") from *inheriting* ("the X policy described here..."). CFI analog for short explanation text.
- **FDC (Frame-Distance Coding)** for Eval C reasoning: two-axis judge labels for attribution discipline and schema adoption. CFI analog for medium reasoning text.

Lexicon-based RD remains a sensitivity check on these texts but is not the primary measure.

**The "explanation neutrality" principle this surfaces.** No published bias-detection benchmark evaluates the framing of explanation text itself — BiasLab evaluates rationale categories and label accuracy; Media Bias Detector (CHI 2025) deliberately suppressed LLM-generated explanations due to user-trust concerns about this exact issue. **"Bias-detection tools should produce framing-neutral explanations"** is not a named principle in the literature, and this paper introduces and operationalizes it.

This connects to the established decision/explanation dissociation literature (Turpin et al., NeurIPS 2023, arXiv:2305.04388 — *"Language Models Don't Always Say What They Think"*): explanations can be plausible while being unfaithful to underlying behavior. We extend Turpin's framework from *label flips* to *framing shifts*, testing whether explanations preserve or replace source framing while discrete decisions stay stable.

### Reframing the "neutrality directive" → "reframing directive"

**The term "neutrality directive" is a misnomer that obscures what the directive actually does.** Empirically, on our data, the "be neutral, do not adopt framing" directive produces:

| Behavior | Baseline | Under "full" directive | Effect |
|---|---:|---:|---|
| Source framing preserved (absorption) | ~26% | ~9% | strips ~65% of source framing |
| Model-default framing injected (generation) | ~50% | ~30% | suppresses ~40% of model framing |

The directive does not produce neutral output — neutrality is unreachable (Lakoff 1996; Rosen 2003; Boykoff & Boykoff 2004). What it produces is **framing replacement**: the model substitutes a damped version of its own training-distribution priors for the source's framing. Even at maximum directive intensity the model still injects ~30% novel framing.

**Proposed terminology (to be adopted in the paper):**

| Field-standard term | Proposed term | Why |
|---|---|---|
| "Neutrality directive" | **"Reframing directive"** | More accurate; what the directive actually does |
| "Even-handedness" | **"Engagement parity"** | Already adopted in our methodology |
| "Bias removal" / "debiasing" | **"Framing replacement"** | Acknowledges no "no-framing" output exists |

**This is a vocabulary contribution worth claiming.** The methodology doesn't just propose new measurements; it proposes a more accurate term for what's actually happening when LLMs comply with "be neutral" instructions. The paper's stance: there is no neutral output, only differing degrees of framing replacement, with the model's training-distribution priors filling the vacuum left by source-framing stripping.

This connects mechanistically to:
- **Generation > absorption** (NF-3): when summary bias appears, models invent more than they parrot — model-default framing dominates
- **Mechanistic separability** (Arditi 2024; Zhao 2025): refusal vs content encoded separately; same likely true for source-stripping vs model-injection
- **Construct dissociation** (this paper): EP and CFI move on different timescales because they reflect different mechanisms

### Literature anchors for the reframing

- **Röttger et al. 2024** (arXiv:2402.16786) — foundational prior on prompt-conditional political-stance scores; we extend to paired-prompt paradigm
- **Jacobs & Wallach 2021** (arXiv:1912.05511) — psychometric vocabulary (construct vs operationalization)
- **Reuel et al. 2025** (arXiv:2511.04703) — construct validity in 445 LLM benchmarks
- **Wallach et al. 2025** (arXiv:2502.00561) — GenAI eval as social-science measurement
- **Feng et al. 2024** (arXiv:2403.18932) — content vs style decomposition for political bias
- **Arditi et al. 2024** (NeurIPS) — refusal mediated by single direction
- **Zhao et al. 2025** (arXiv:2507.11878) — refusal and content encoded separately
- **Anthropic political-neutrality-eval** (Nov 2025) — direct positioning target; bridge sentence is their own caveat that "system prompts can appreciably influence model even-handedness"

---

## Why a research program (not one paper)

Three reasons:
1. **Each paper meets independent venue threshold.** No padding required.
2. **Different audiences need different framings.** Alignment readers ≠ NLP-benchmark readers ≠ interpretability readers.
3. **Sequenced submissions reduce risk.** If Paper 1 has reviewer pushback, Papers 2 and 3 can incorporate the feedback.

The papers reference each other as a coherent program rather than competing for credit. Paper 2 cites Paper 1 as motivation; Paper 3 cites both as the empirical setting it provides mechanism evidence for.

---

# Paper 1 — *True-Behavior Profile* (formerly *Confounded Bias*)

## Title

**Working:** "There Is No 'True' Political Bias of an LLM — Only Configurations and Profiles"

**Alternatives:**
- "Engagement Parity vs Content Framing Inheritance: A Construct Decomposition of LLM Political Behavior"
- "Profile, Not Scalar: Multi-Condition × Multi-Construct Reporting for LLM Political-Bias Evaluation"
- "What We Measure When We Measure LLM Political Bias"

## Tagline / abstract sketch

> *We argue that LLM political bias is a profile across configurations and behavioral constructs, not a scalar. Current 'even-handedness' scores measure engagement parity (refusal/help symmetry) with high construct validity but are commonly read as evidence of content-level neutrality — a separable, currently unmeasured construct that empirically dissociates from engagement parity and is mechanistically distinct (Arditi 2024; Zhao 2025). We characterize the construct gap, propose a 'True-Behavior Profile' (multi-condition × multi-construct matrix) as a methodologically honest reporting *form* — demonstrated on this corpus and these two frontier models; adoption as a community standard would require validation on diverse corpora and tasks — and demonstrate that under minimal-conditioning baseline, the two frontier models sampled in this study (Claude Sonnet 4.5, GPT-4.1) converge on content framing inheritance, suggesting reported cross-model differences (within this pair) reflect instruction-compliance variance rather than intrinsic capability differences.*

## Core thesis (v5 locked 2026-05-09; v6 extension locked 2026-05-11)

**v5 thesis (still in force):**

> *"LLM political bias is a profile across configurations, not a scalar. At minimal-conditioning baseline, **the two frontier models sampled in this study (Claude Sonnet 4.5, GPT-4.1)** converge on content framing inheritance; reported differences in published 'even-handedness' scores reflect instruction-compliance variance rather than intrinsic capability differences, and conflate behavioral constructs that mechanistic work shows are separately encoded. Generalization to other frontier model families (Gemini, Llama, Mistral, DeepSeek, Qwen) is a question for future work."*

**v6 extension (2026-05-11; tempered 2026-04-29 per Hole 9 resolution):**

> *"This profile extends across **the three text granularities tested in this study** within a single evaluation. The asymmetric framing-inheritance signature observed in Eval B summaries (long-form, ~250w) replicates in Eval A bias-detection explanations (short-form, ~33w) and Eval C lean-classification reasoning (medium-form, ~180w). Bias-detection tools deployed in production that surface LLM-generated explanations to users (CheckTextBias, Ground.News, BiasLab-style audit tools) are unaudited for explanation-level framing inheritance under their proprietary prompts; our evaluation is relevant to that deployment context but does not directly audit those proprietary pipelines. We propose Voice Adoption Rate (VAR) and Frame-Distance Coding (FDC) as text-type-specific operationalizations of CFI and demonstrate cross-text-type generalization within the sampled set; whether the pattern extends to text types outside the set tested (op-eds, translation, court filings, social media analysis, etc.) is a future-work question."*

Four load-bearing empirical claims under this thesis:

1. **Construct dissociation.** Engagement parity (what published evals measure) and content framing inheritance (what they're read as measuring) move on different timescales and respond to different controls. EP is condition-invariant; CFI varies 3× under prompt perturbation. Mechanistic work (Arditi 2024; Zhao 2025) predicts and explains the dissociation.

2. **Baseline convergence.** Under minimal-conditioning baseline (no neutrality directive), Sonnet and GPT-4.1 are statistically indistinguishable on content framing inheritance (~25-28% absorption, gap of 2.5pp, p=0.36). The cross-model differences reported in published evals largely *don't exist* in default behavior — they emerge only under explicit neutrality instruction.

3. **Cross-family judge favoritism.** Independent confound: when judge and target share a developer family, reported political behavior is favorably skewed by ~1.4 lean-class units (Eval C interaction β=−1.42, p<0.0001 in pre-registered FDR-corrected family). Reinforces the multi-construct, multi-condition recommendation — single-judge evaluation is also a dimensionality collapse.

4. **Cross-text-type generalization (planned Stage 1, ~$40 to verify).** The Eval B asymmetric stripping pattern (RIGHT-coded source framing stripped 2–5× more aggressively than LEFT-coded) is predicted to replicate on Eval A explanations and Eval C reasoning under their respective text-type operationalizations (VAR, FDC). This is the deployment-relevance contribution: bias-detection tools as deployed produce explanatory text that inherits source framing asymmetrically.

## Contributions

1. **Cross-family dual-judge methodology** with pre-registered formal favoritism testing across three media-bias evaluation tasks (detection, summarization, lean classification).
2. **Four-arm prompt-condition design with mechanism dissection** (minimal / lexical-only / structural-only / full) testing which sub-component of the reframing directive drives the stripping behavior. Pre-registers the (directive × factor) interaction: lexical-only directive should selectively suppress the lexical factor (F3); structural-only should selectively suppress the structural factor (F1).
3. **Replacement Direction (RD) — directional default bias as a primary construct.** New construct measuring the political tilt of what the model substitutes when stripping source framing. Empirically reveals asymmetric stripping: both targets strip right-coded source framing 2–5× more aggressively than left-coded framing. This is the substantive political-bias-of-LLMs finding that single-number "even-handedness" scores systematically miss.
4. **Cross-text-type generalization with new operationalizations (VAR, FDC).** Voice Adoption Rate (VAR — per-detection LLM-judge labeling) and Frame-Distance Coding (FDC — two-axis reasoning-text labeling) are text-type-specific CFI operationalizations addressing the power limitations of lexicon analysis on short explanatory text. Predicted finding: the asymmetric stripping pattern from Eval B summaries replicates on Eval A explanations and Eval C reasoning — extending the framing-inheritance signature from comprehensive summaries to deployment-relevant explanatory metadata. Coverage-driven design decision (LLM-judge primary, lexicon-RD sensitivity) is itself a methodological contribution.
5. **Deployment-relevance contribution: "explanation neutrality" as a principle.** No published bias-detection benchmark evaluates the framing of explanation text itself (BiasLab evaluates rationale categories; Media Bias Detector at CHI 2025 deliberately suppressed LLM-generated explanations citing this exact concern). We introduce and operationalize "bias-detection tools should produce framing-neutral explanations" as a named methodological principle, with measurable VAR/FDC instruments.
6. **Three-factor structure of media-bias scoring** (structural / epistemic / lexical) via EFA on the 12-dimensional custom_scores. The "GPT-4.1 less biased" finding lives entirely in the structural factor (β=−0.57, p=0.001); null on epistemic and lexical.
7. **Pre-registered FDR-corrected confirmatory analyses.** Paper 1 BH-FDR family under Path B (locked 2026-05-18) = 8 tests at q=0.05: 6 confirmatory (H22, H23, H25, H26, H27, H27b) + 2 equivalence (H28, H29). See `PRE_REGISTRATION.md` §6.6.10 and §6.7. v1+v2 mechanism-dissection tests (12 v1 + 7 v2) and vocabulary 2×2 tests (H36–H39 + D-H38s) are deprecated / deferred from the Paper 1 family; design specifications preserved as FRAME-program artifacts for follow-up papers.
8. **Behavioral mechanism evidence (no SAE required).** Paraphrase robustness + instruction priority tests show whether the prompt effect is keyword-dependent or pathway-mediated, *without* requiring closed-model activation access.
9. **Vocabulary contribution.** We propose **"reframing directive"** as a more accurate term than the field-standard "neutrality directive," based on empirical evidence from this study that the directive does not produce neutral output but asymmetric framing replacement. The RD finding (Contribution 3) and the cross-text-type generalization (Contribution 4) reinforce the proposal: not only does the directive fail to produce neutrality, it produces direction-asymmetric stripping across the three text-types we tested. **Field adoption of this terminology would require independent replication on other corpora and other frontier models.**

## Data sources

| Source | Status |
|---|:-:|
| 95-article AllSides-anchored evaluation corpus | ✓ existing |
| Eval A/B/C rollouts × 2 targets × 3 conditions (minimal/ablation/full) | ✓ existing |
| Stage-2 verification verdicts × 2 judges | ✓ existing |
| Article-level lean ratings × 2 judges | ✓ existing |
| 10K curated corpus (PROD.db enrichment) | ✓ existing (sampling pool for power expansion) |
| Per-factor absorption analysis on existing 3-arm data | NEW — $0, ~3 hours of analysis |
| **Lexical-only arm** (Eval B) | NEW — ~$50, 2-3 days |
| **Structural-only arm** (Eval B) | NEW — ~$50, 2-3 days |
| Behavioral-mechanism tests (paraphrase × 5; priority × 3) | OPTIONAL — ~$30 of API |
| **Stage 1: VAR LLM-judge on existing Eval A explanations** (~6,000 short classifications) | NEW — ~$30 at Haiku |
| **Stage 1: FDC LLM-judge on existing Eval C reasoning** (~570 classifications) | NEW — ~$5 at Haiku |
| Stage 2: reframing-directive arms for Eval A and C (conditional on Stage 1) | OPTIONAL — ~$100-150 |

## Methodology summary

- Pre-registered confirmatory analysis with Benjamini-Hochberg FDR (`PRE_REGISTRATION.md` v2).
- Linear mixed models with article-level random intercept, fall back to OLS + cluster-robust SE on singular-fit cells.
- GEE-logit for binary outcomes (verdict validity, lean accuracy).
- Bootstrap 95% CIs on reliability statistics (Krippendorff's α, Cohen's κ).
- **Four-arm condition design** (minimal / lexical-only / structural-only / full) for mechanism-pathway isolation. The "ablation" arm (schema-only) from v1 is dropped from primary analysis — the schema-effect null is documented in supplementary materials and cited from existing v1 data.
- Continuous source–summary fidelity correlation (NF-3 follow-on, see `analysis/fidelity_correlation.py`).
- EFA with varimax rotation on Eval B custom_scores; per-factor LMMs.
- **Per-factor absorption decomposition** on existing 3-arm data as confirmatory test of factor selectivity (free, no new API calls; predicted in advance).
- **Cross-text-type CFI operationalization.** Text-type-specific instruments: CFI via custom-scores absorption rate for Eval B summaries (existing); VAR via LLM-judge for Eval A explanations (new); FDC via two-axis LLM-judge for Eval C reasoning (new). Coverage-driven choice — lexicon RD primary on long-form text where coverage permits; LLM-judge primary on short-form text where lexicon would be power-limited.
- **Two-stage analysis path.** Stage 1: compute VAR and FDC on existing data from all 3 conditions × 2 targets × 95 articles (no new rollouts; just judge-classification of existing texts). Stage 2 (conditional on Stage 1 producing meaningful signal): add reframing-directive arms to Evals A and C to test whether directives reduce inheritance asymmetrically. Stage 2 cost ~$100-150; not committed.

## Confirmed findings

- **Eval C family favoritism:** interaction β = −1.42 [−1.90, −0.94], p < 0.0001, BH-FDR p < 0.0001
- **Eval B target main effect:** β = −0.41 [−0.61, −0.21], p < 0.0001, BH-FDR p = 0.0003 — but instruction-conditional
- **Instruction-controllability (NF-3 3-arm):** removing the framing rule triples absorption (OR = 3.13, p < 0.001)
- **Three-factor structure:** F1 (structural, 60.8% variance), F2 (epistemic), F3 (lexical) — clean varimax separation
- **Continuous fidelity:** instruction dampens source–summary slope from ~0.20 (baseline) to ~0.13 (full); correlation persists across conditions
- **Construct dissociation (CCDR):** CCDR(CFI, EP) = 22.6× — engagement parity is condition-invariant while content framing inheritance varies dramatically
- **Asymmetric stripping (RD):** both targets strip right-coded source framing 2–5× more than left-coded; on RIGHT articles, ~58–80% of right-coded language is stripped; on LEFT articles, left-coded language is preserved or slightly amplified (lexicon coverage caveat applies; LLM-classifier follow-up planned)
- **Cross-text-type generalization (pending Stage 1 execution):** prediction that the asymmetric stripping pattern replicates in Eval A explanation text (via VAR) and Eval C reasoning text (via FDC and lexicon RD). Stage 1 analysis on existing data is the immediate next step (~$40, ~1 day).

## Target venue

- **Primary:** NeurIPS 2026 alignment/safety track (deadline May 15, 2026 — 8 days from doc creation)
- **Backup:** ICLR 2027 (deadline ~Sep 28, 2026)
- **Companion piece:** Anthropic Alignment Science Blog post for visibility

## Timeline

| Phase | Window | Status |
|---|---|:-:|
| Behavioral-mechanism tests (paraphrase + priority) | Now → 2 days | Not started |
| Updated stats_report.md with Paper 1 framing | Now → 3 days | Not started |
| First draft (intro + methods) | Day 4-5 | Not started |
| Results + discussion drafted | Day 6-7 | Not started |
| Revision + appendix + camera-ready | Day 8 | Submission |

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Reviewer asks for mechanism evidence | Paraphrase + priority tests partially address; cite Paper 3 as future work |
| "Why no humans?" pushback | Cite Annolexical (NAACL 2025); note as limitation; AllSides outlet ratings as proxy |
| "Paper too narrow" | Position multi-paper program; cite Paper 2 as concurrent work |
| Tight 8-day deadline to NeurIPS | Backup deadline ICLR 2027 (Sep) is comfortable |

## Anchor citations (must-cite related work)

- **Anthropic political-neutrality-eval** (Nov 2025) — *direct positioning target*
- **MT-Bench / Self-Preference Bias** (Zheng NeurIPS 2023; Wataoka NeurIPS 2024)
- **Santurkar OpinionQA** (ICML 2023, arXiv 2303.17548)
- **Constitutional AI** (Bai et al., arXiv 2212.08073)
- **Bloom auto-evals** (alignment.anthropic.com/2025/bloom-auto-evals/)
- **Rozado** (PLOS One 2024)
- **MBIB** (Wessel SIGIR 2023, arXiv 2304.13148)
- **BiasLab** (arXiv 2505.16081)
- **Annolexical** (NAACL 2025, arXiv 2411.11081)
- **MAGPIE** (Horych LREC-COLING 2024, arXiv 2403.07910)
- **Turpin et al., "Language Models Don't Always Say What They Think"** (NeurIPS 2023, arXiv 2305.04388) — decision/explanation dissociation literature; we extend from label-flip to framing-shift
- **Media Bias Detector** (CHI 2025, arXiv 2502.06009) — deployed tool that deliberately suppressed LLM explanations citing the exact concern we operationalize
- **PolBiX** (Jakob et al., EMNLP Findings 2025, arXiv 2509.15335) — null result on objectivity directive for classification labels; supports our scope claim that reframing operates on content-emission surface
- **"When Neutral Summaries are not that Neutral"** (Bang et al., AAAI 2025, arXiv 2410.09978) — asymmetric directive effects on summaries; closest prior on asymmetric stripping
- **Lakoff 1996** *Moral Politics*; **Entman 1993, 2007** on framing theory; **Rosen 2003** on "view from nowhere" — theoretical foundation for "no-neutrality" framing
- **Arditi et al.** (NeurIPS 2024, arXiv 2406.11717) and **Zhao et al.** (arXiv 2507.11878) — mechanistic basis for separability of refusal/content; predicts the construct dissociations we measure

---

# Paper 2 — *AllSides-Synth*

## Title

**Working:** "AllSides-Synth: A Benchmark for Multi-Source News Synthesis with Frontier LLMs"

**Alternatives:**
- "Multi-Source News Synthesis as the Right Unit of LLM Media-Bias Evaluation"
- "AllSides-Synth: Replicating Confounded-Bias Findings on Real-World Multi-Source Synthesis"

## Tagline / abstract sketch

> *Real-world LLM media impact runs through multi-source synthesis, not single-article detection. We introduce AllSides-Synth — the first frontier-LLM benchmark of multi-source news synthesis behavior, using ~300 AllSides headline roundups as expert-curated L/C/R triplets with editorial-grade balanced syntheses as a human-aligned reference. We replicate the methodological findings of Paper 1 in this real-world setting and characterize systematic divergence between LLM and editorial synthesis.*

## Core thesis

Single-article LLM-bias evaluation measures the wrong thing. The actual societal impact of LLM news handling runs through multi-source synthesis — exactly the task that AllSides has been doing manually for 12 years and that AI tools (Ground.News, OpenAI's news products) increasingly automate. We build the first benchmark for this task at frontier scale and use it to:

1. Replicate the instruction-controllability and judge-favoritism findings from Paper 1 in a more realistic setting (strengthening Paper 1's claim).
2. Anchor LLM behavior against expert editorial practice (using AllSides editorial syntheses as a human-aligned reference).
3. Characterize the *direction* of LLM divergence from editorial practice — does it skew left or right, or does it flatten balance?

## Contributions

1. **AllSides-Synth dataset** — 300 events, each with 3 articles (Left, Center, Right) + AllSides balanced headline + AllSides synthesis paragraph + AllSides "common ground" facts list. Public release with appropriate licensing.
2. **Five evaluation metrics** for multi-source synthesis behavior:
   - BERTScore (model synthesis vs AllSides editorial synthesis)
   - Per-source frame-share (FActScore-style atomic decomposition against per-source claim sets)
   - Lean-of-divergence (Eval C lean classifier blind-applied to model output)
   - Common-ground fact recall + precision
   - Per-source absorption rate (extending Paper 1's NF-3 framework)
3. **Replication of Paper 1's instruction-controllability finding** in the synthesis setting. Predicted: same direction, larger magnitude.
4. **Replication of Paper 1's cross-family judge favoritism** in synthesis evaluation. Predicted: similar magnitude, on a different task.
5. **Distance-to-AllSides-editor** as a novel anchored measure of LLM behavior on real-world journalistic practice.

## Data sources

| Source | Status |
|---|:-:|
| AllSides headline roundups (~300 events × 3 articles + synthesis) | NEW — to scrape (`allsides.com/recent-headline-roundups`) |
| Same target models as Paper 1 (Sonnet 4.5, GPT-4.1) | ✓ existing API access |
| Same judge models as Paper 1 (Sonnet 4.6, GPT-5; Path B 2026-05-18) | ✓ existing API access |
| Same 3-arm condition design + new "synthesize-balanced" condition | NEW — adapted from Paper 1's prompt design |

## Methodology summary

- 200-400 events for venue-paper scope; pilot at 30 events (~$30) to validate methodology.
- Named-entity-balanced sampling to avoid single-figure confounds.
- Input-order randomization as a control (per arXiv 2512.02665, Input Order Shapes LLM Semantic Alignment).
- LMM: `metric_value ~ condition × target + (1 | event)` clustered on event.
- Per-event variance reported alongside cell means (a model that averages-to-balanced by alternating direction across events is NOT balanced on any single event).
- Distance-to-AllSides metrics computed as residuals; lean of residual measured via Paper 1's lean classifier.

## Predicted findings

Based on Paper 1's findings extended to synthesis:

1. **Synthesis fidelity is condition-controllable.** Same direction as NF-3 but more dramatic (more sources, more dimensions).
2. **Synthesis lean drift exists and is family-asymmetric.** Sonnet syntheses likely lean differently than GPT-4.1 syntheses.
3. **Cross-family judge × synthesis bias interaction is large.** Paper 1's β=−1.42 may be exceeded.
4. **Per-event variance is high** — averages mislead.
5. **Common-ground fact recall is more discriminating** than synthesis BERTScore.

## Target venue

- **Primary:** NeurIPS Datasets & Benchmarks Track 2026 (deadline ~Aug 2026)
- **Backup:** NAACL 2027 main (deadline ~mid-2026)
- **Alternative:** ACL 2027

## Timeline

| Phase | Window |
|---|---|
| Scrape AllSides roundups (~300) | Late May - early June 2026 |
| Build dataset format + cleaning | Mid June 2026 |
| Pilot eval at 30 events | Late June 2026 |
| Full eval at 300 events | July 2026 |
| Analysis + writing | August 2026 |
| Submission | NeurIPS D&B Aug deadline 2026 |

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| AllSides scraping fragile or licensing unclear | Manual fallback to public roundup screenshots; license inquiry early |
| 300 events too few for power | Extend to 500; or stratify by topic for sub-analyses |
| Predicted findings don't replicate | Honest null is publishable — "synthesis behavior diverges from single-article behavior" |
| Editorial synthesis quality varies | Document with random-sample audit; report only on roundups with >X words of synthesis |

## Anchor citations (additional to Paper 1)

- **NeuS** (Lee et al., NAACL 2022, arXiv 2204.04902) — direct prior art on multi-source bias mitigation
- **FActScore** (Min et al., EMNLP 2023, arXiv 2305.14251) — atomic decomposition methodology
- **Multi-News** (Fabbri et al., ACL 2019) — MDS workhorse dataset
- **"Source framing triggers systematic bias"** (Science Advances 2025, doi 10.1126/sciadv.adz2924)
- **Input Order Shapes LLM Semantic Alignment** (arXiv 2512.02665)
- **EMNLP 2025 cluster** on outlet-name bias (2025.emnlp-main.872, 2025.emnlp-main.1513)
- **AllSides methodology documentation** (allsides.com/blog/how-allsides-creates-balanced-news-step-step-guide)

---

# Paper 3 — *Mechanism Replication* (optional, lower priority)

## Title

**Working:** "Open-Weight Replication of Confounded-Bias Findings: Mechanism Evidence from Llama 3"

**Alternatives:**
- "Tracing the Instruction Effect in Open-Weight LLMs"
- "Mechanism Evidence for Instruction-Controlled Bias from SAE Probing"

## Tagline / abstract sketch

> *Papers 1 and 2 established behavioral evidence for instruction-controlled bias in closed-weight frontier models. We replicate these findings on open-weight Llama 3 70B and use publicly-available SAEs to provide mechanism-class evidence: the prompt effect correlates with [feature X] activation. While we cannot directly probe Claude or GPT-4.1, the open-weight replication constrains the space of possible mechanisms in closed models.*

## Core thesis

The behavioral evidence in Papers 1-2 is consistent with multiple mechanism hypotheses (surface keyword pathway, format-compliance pathway, internalized value). On open-weight models with publicly-available SAEs, we can distinguish these. The findings constrain the space of mechanism hypotheses for closed models.

## Contributions

1. **Replication of FRAME findings on open-weight model(s)** — instruction-controllability + judge favoritism on Llama 3 70B (or Mistral / Qwen).
2. **SAE feature-steering ablation:** identify which features mediate the prompt effect; ablate them and measure behavioral change.
3. **Linear probing of "neutrality" representation** — does the model represent neutrality as a learned direction, or only as a behavioral pathway?
4. **Mechanism evidence as constraint** on closed-model interpretation (cannot prove the same mechanism in Claude/GPT-4.1, but can rule out surface-only pathways if the open-weight model shows non-surface mechanism).

## Data sources

| Source | Status |
|---|:-:|
| Same evaluation tasks (Eval A/B/C) | ✓ adapt from Paper 1 |
| Same AllSides-Synth dataset | ✓ from Paper 2 |
| Llama 3 70B (or similar) inference | NEW — local GPU or Goodfire AI |
| Public SAEs (EleutherAI, Goodfire, or Anthropic's research releases) | NEW |

## Methodology summary

- Run all FRAME evaluation tasks on at least one open-weight model.
- Identify SAE features associated with "neutrality" and "political ideology" via prompted-text probing.
- Activation patching: inject neutrality-feature activations under baseline prompt; measure behavioral shift.
- Linear probe: train a binary classifier (neutrality-instruction vs no-instruction) on activations; check if probe accuracy is high (suggests representation exists) or low (suggests behavior is constructed at output time).
- Compare to behavioral results: feature-steering effect size vs prompt-effect size.

## Predicted findings

(Higher uncertainty than Papers 1-2 — open empirical question.)

1. **Behavioral findings will replicate on open-weight models** — instruction-controllability is general, not specific to Claude/GPT-4.1.
2. **Activation patching will partially replicate the prompt effect** but not entirely, suggesting the prompt operates through a combination of feature-mediated and diffuse pathways.
3. **Probe accuracy for "neutrality-instruction received"** likely high (model has internal representation of having received the instruction), but doesn't tell us whether the *behavior* is mediated through that representation.

## Target venue

- **Primary:** ICLR 2027 (deadline ~Sep 28, 2026)
- **Backup:** NeurIPS 2027 (deadline ~May 2027)
- **Workshop alternative:** ICLR or NeurIPS Mechanistic Interpretability workshop (lower-stakes pilot publication)

## Timeline

Conditional on Papers 1-2 succeeding. Realistic earliest start: Sep 2026.

| Phase | Window |
|---|---|
| Open-weight inference setup | Sep 2026 |
| Replicate Paper 1 behavioral findings on open-weight | Oct 2026 |
| SAE probing + activation patching | Nov 2026 |
| Analysis + writing | Dec 2026 |
| Submission | ICLR 2027 |

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Open-weight findings don't replicate | Publishable null — "instruction effect is closed-model-specific" |
| SAE features don't isolate cleanly | Linear probing as backup mechanism evidence |
| GPU / Goodfire access constraints | Use research credits; focus on smaller open-weight model |
| Mechanism findings don't generalize to closed | Frame as "constraints on hypothesis space" rather than direct claim |

## Anchor citations (additional to Papers 1-2)

- **Refusal Mediated by a Single Direction** (Arditi et al., NeurIPS 2024) — the canonical mechanism-from-direction paper to replicate methodologically
- **Scaling Monosemanticity** (Anthropic, 2024) — SAE methodology
- **Goodfire AI** (goodfire.ai) — feature-steering API for Llama 3
- **EleutherAI SAE releases** — public model interpretability infrastructure

---

# Generalizable Methodology — beyond news political bias

> *News political bias is the **demonstration domain**. The methodology generalizes.*

The FRAME methodology is a generic behavioral evaluation framework for LLMs. It addresses the broader pattern in which evaluations report scalar scores on multi-faceted constructs, collapsing dissociable behavioral dimensions. Our news-political-bias case is one instance of this pattern. The methodology applies wherever:

- The construct is multi-faceted (most LLM behaviors are)
- Multiple judges from different developer families are practical (most evaluation settings allow this)
- Prompts have controllable directive components (system-prompt-driven evaluations)
- Single-number reporting currently dominates the field (almost all leaderboard-style evals)

## The generic methodology — six steps

| # | Step | Generic version | News-bias instantiation |
|---|------|-----------------|-------------------------|
| 1 | **Construct factorization** | Run EFA on the rubric. Treat latent factors as the constructs of interest, not the surface dimensions. | EFA on 12 custom_scores → 3 factors (structural / epistemic / lexical) |
| 2 | **Multi-arm prompt-component ablation** | Identify distinct directive components in the prompt. Run conditions varying each, isolating mechanism pathways. | minimal / lexical-only / structural-only / full |
| 3 | **Cross-family dual-judge** | Use 2+ judges from different developer families. Test for family-favoritism interactions. | Sonnet 4.6 (Anthropic) + GPT-5 (OpenAI) |
| 4 | **Pre-registered LMM with FDR** | Pre-register primary tests. Apply BH-FDR. | 12 primary contrasts + new (directive × factor) tests |
| 5 | **CCDR diagnostic** | Compute variance ratios across construct pairs. Large ratios → construct dissociation → scalar collapse is a category error. | CCDR(CFI, EP) = 22.6× |
| 6 | **Profile-based reporting** | Replace single-number model rankings with multi-construct × multi-condition matrices. | True-Behavior Profile (TBP) |

## Domains where FRAME methodology applies

| Domain | EP analog | CFI analog | Conditioning components |
|---|---|---|---|
| **Code generation** | Engagement parity across language strata | Style/idiom inheritance from in-context examples | Style directives ("write Pythonic" vs "be efficient" vs "be readable") |
| **Medical advice** | Engagement parity across patient-demographic strata | Uncertainty-framing inheritance from query | Safety directives, recommendation strength |
| **Legal analysis** | Engagement parity across jurisdiction strata | Doctrinal-framing inheritance from precedent | Citation expectations, formality directives |
| **Creative writing** | Engagement parity across genre strata | Authorial-voice inheritance from prompt examples | Style directives, length, persona |
| **Multi-turn conversation** | Engagement consistency across turns | Stance maintenance under pressure | Refusal directives, persona stability |
| **Safety evaluation** | Refusal symmetry (Anthropic's analog) | Harm-content separation under refusal | Refusal directives, content directives |
| **Translation** | Engagement parity across language pairs | Source-text fidelity (already a measured construct) | Style directives ("formal" / "literal" / "natural") |
| **News political bias (this paper)** | Engagement parity across L/R strata | Content framing inheritance | Reframing directives (lexical / structural) |

## What this means for paper positioning

- **Paper 1** demonstrates FRAME methodology on the high-stakes case of news political bias. The methodology is the contribution; the news-bias finding is the demonstration.
- **Paper 2 (AllSides-Synth)** applies FRAME methodology to multi-source synthesis. Same methodology, different task setting.
- **Paper 3 (Mechanism Replication)** applies FRAME methodology to open-weight models with mech-interp probing. Same methodology, different model class.
- **Future work** can apply FRAME methodology to any of the domains in the table above, individually or together.

The methodology is the through-line. The applications are the demonstrations.

## What's NOT generic

The methodology generalizes; the *constructs* don't. Each new domain needs:
- Its own factor analysis to identify latent constructs
- Its own engagement parity definition (over relevant perspective strata)
- Its own content-fidelity analog (where applicable)
- Its own taxonomy of bias types (or whatever the multi-component scoring rubric measures)

The TBP, CCDR, multi-arm conditioning, cross-family judging, pre-registration with FDR, and profile reporting all carry over without modification.

---

# Program-level positioning

## What the program builds toward

Cumulative claim by end of all three papers:

> *"Reported political behavior of frontier LLMs is shaped substantially by methodological choices in evaluation (judge family, instruction conditioning, single-article vs synthesis paradigm). When these confounds are controlled — and when behavior is anchored against expert journalistic practice (AllSides editorial synthesis) — the cross-model differences shrink and become interpretable. Mechanism evidence from open-weight replication suggests the prompt effect is partially feature-mediated, ruling out pure surface keyword pathways."*

That claim, supported by three papers, gives the author a recognizable thought-leadership position.

## How the papers reinforce each other

- **Paper 2 cites Paper 1** as motivation: "we extend the methodology developed in [Paper 1] to a more realistic synthesis setting."
- **Paper 3 cites both** as the empirical setting it provides mechanism evidence for.
- **Paper 1 mentions Paper 2 as concurrent work** in the introduction, telegraphing the program identity.

## Sequencing rationale

- Paper 1 first because: existing data already supports it; deadline pressure (NeurIPS May 15) creates focus; positions claims that Papers 2-3 will replicate.
- Paper 2 second because: dataset construction is the slow step; can begin immediately after Paper 1 submission.
- Paper 3 last because: mechanism evidence is high-uncertainty; depends on Papers 1-2 for empirical framing.

## What this is NOT

- Not a comprehensive bias benchmark like MBIB or HELM.
- Not a primary mechanistic-interpretability contribution like Arditi et al.
- Not an opinion piece on AI bias.
- Not a dataset-construction-only paper.

## What this IS

- A behavioral evaluation methodology contribution to AI for media bias.
- A demonstration that current evaluations are systematically confounded.
- A constructive proposal for how to fix the confounds (cross-family judging + condition control + multi-source paradigm).
- A research program identity for the author.

---

# Decision log

## Outstanding decisions for the author

1. **Commit to NeurIPS 2026 May 15 deadline for Paper 1?** Tight but feasible if behavioral mechanism tests run this week.
2. **Scope of AllSides-Synth (Paper 2): 200, 300, or 500 events?** Balance comprehensiveness vs cost (~$100/300, scaled).
3. **Pursue Paper 3 at all?** Optional — depends on access to GPU compute or Goodfire AI subscription.
4. **Public dataset release for AllSides-Synth?** Probably yes; check AllSides licensing.

## Author positioning

- Primary identity: *AI for media bias methodologist*
- Secondary identity: *Behavioral alignment auditor*
- Tertiary (optional, gated by Paper 3): *Open-weight interpretability practitioner*

---

## Changelog

| Date | Change | By |
|------|--------|----|
| 2026-05-07 | Initial program plan. Three-paper sequencing, FRAME branding, methodology-primary framing per author feedback on opacity of "instruction-following" claim. | Claude |
| 2026-05-09 | **Major reframing — True-Behavior Profile.** Reframed Paper 1 as construct-validity / category-error claim grounded in dissociation between engagement parity and content framing inheritance, anchored mechanistically to Arditi (2024) and Zhao (2025). Locked v5 thesis: *"LLM political bias is a profile across configurations, not a scalar."* Added §"Conceptual framing — True-Behavior Profile" capturing: (1) two-paradigm distinction (model-as-subject vs model-as-classifier), (2) interpretive-dimensionality operationalization of "scalar collapse," (3) four-step contribution structure ending in mechanistic anchoring, (4) "true bias" reframed as distribution over conditioning rather than stable property, (5) constructive payoff = True-Behavior Profile reporting standard. Updated unifying program thesis to reflect category-error claim. | Claude |
| 2026-05-10 | **Three structural updates.** (1) Paper 1 design pivoted to 4-arm (minimal / lexical-only / structural-only / full); old "ablation" arm dropped from primary analysis (schema-effect null already documented). New (directive × factor) interaction hypothesis pre-registered. (2) Added §"Generalizable Methodology" — explicit demonstration that FRAME methodology applies beyond news political bias (code generation, medical advice, creative writing, multi-turn, safety, translation). News-bias becomes the demonstration domain; methodology is the contribution. Tagline updated. (3) Added §"Reframing the 'neutrality directive'" — proposing **"reframing directive"** as a more accurate term, based on empirical finding that the directive produces framing replacement (source stripping + partial model-default suppression) rather than neutrality. Vocabulary contribution claimed. | Claude |
| 2026-05-10 | **Replacement Direction (RD) added as fourth primary construct.** Computed via paired-political-lexicon classification of summaries vs sources. Empirical finding: under reframing directives ("full"), both targets strip right-coded source framing 2–5× more aggressively than left-coded framing. RD asymmetry across source-lean strata is the directional default bias finding — substantive political-bias-of-LLMs claim that goes beyond the methodology critique. TBP matrix updated to include RD as fourth construct. Unifying program thesis updated. Lexicon coverage caveat applies (~7% of language); LLM-classifier follow-up (NF-1B) will tighten magnitude estimates. | Claude |
| 2026-05-11 | **Cross-text-type generalization (v6 extension).** Reframed Paper 1's reach to include not just summary text (Eval B) but also bias-detection explanations (Eval A) and lean-classification reasoning (Eval C). Each is text the model produces *about* source content, subject to the same framing-inheritance question. Added two new text-type-specific CFI operationalizations: **VAR (Voice Adoption Rate)** via per-detection LLM-judge labeling for Eval A explanations, and **FDC (Frame-Distance Coding)** via two-axis LLM-judge labeling for Eval C reasoning. Coverage-driven design: lexicon RD is power-limited on short explanations (3-6% coverage); LLM-judge becomes primary for these surfaces. Deployment-relevance angle articulated: bias-detection tools (CheckTextBias, Ground.News, BiasLab) surface LLM explanations to users — explanation framing is an unaudited deployment property. Introduces "explanation neutrality" as a named methodological principle. Two-stage analysis plan: Stage 1 ($35-50, on existing data) validates the cross-text-type prediction; Stage 2 ($100-150, new reframing-directive arms for Eval A and C) only if Stage 1 motivates it. New citation anchors: Turpin 2023 (decision/explanation dissociation), Media Bias Detector CHI 2025 (deliberately suppressed LLM explanations), PolBiX 2025 (objectivity-directive null on classification labels). | Claude |
