# LLM-Judge Prevalence Survey — progress log (crash-safe, append-only)

Started: 2026-07-07
Claim under test: "most work using LLM judges reports no inter-judge reliability statistics, and none pre-commits acceptance thresholds."

Coding fields (binary Y/N/UNCLEAR):
- C1: reports ANY inter-judge or judge-human agreement statistic
- C2: uses judges from 2+ DIFFERENT model families
- C3: validates the judge against human labels on a sample
- C4: pre-commits an acceptance threshold for judge quality BEFORE using scores (stated gate, not post-hoc)
- C5: any pre-specified fallback if the judge is unreliable

Inclusion: 2024-2026 papers that USE LLM-as-judge to score outputs and draw substantive conclusions (not judge-methods papers). Every paper inspected via arXiv abstract/HTML or ACL Anthology; URL recorded.

---
## Paper 1: Self-Rewarding Language Models
- Venue/year: ICML 2024 (arXiv:2401.10020)
- URL: https://arxiv.org/abs/2401.10020 (inspected ar5iv HTML)
- Judge: GPT-4 (head-to-head win rates, 256 test prompts; AlpacaEval 2.0). Claude 2 used only for early-stopping checkpoint selection, not headline eval.
- C1 agreement stat: N — 50-instruction author human eval described as "consistent with GPT-4's judgments" (Fig 5), but no agreement coefficient/statistic computed.
- C2 2+ judge families: N — substantive conclusions from GPT-4 only (Claude 2 role = training-time validation, not reported eval).
- C3 human validation of judge: Y — 50 instructions, 3 blind author-annotators, majority vote, compared qualitatively to GPT-4 judgments.
- C4 pre-committed threshold: N — none stated.
- C5 fallback: N — none stated.

## Paper 2: SimPO: Simple Preference Optimization with a Reference-Free Reward
- Venue/year: NeurIPS 2024 (arXiv:2405.14734)
- URL: https://arxiv.org/abs/2405.14734 (inspected arXiv HTML v3... via html fetch)
- Judge: GPT-4 Turbo (AlpacaEval 2, Arena-Hard, MT-Bench) — single family.
- C1: N. C2: N (GPT-4 variants only). C3: N. C4: N. C5: N.
- Note: acknowledges "potential biases from model-based evaluations" as limitation, no mitigation.

## Paper 3: SambaLingo: Teaching Large Language Models New Languages
- Venue/year: arXiv 2024 (2404.05829)
- URL: https://arxiv.org/abs/2404.05829 (inspected arXiv HTML)
- Judge: GPT-4 scores multilingual chat responses to real user prompts; Claude Opus re-run as second judge ("in line with our previous results").
- C1: N — no statistic; native speakers read "a few examples" of GPT-4 reasoning and "unanimously agree" (qualitative spot-check only).
- C2: Y — GPT-4 (OpenAI) + Claude Opus (Anthropic) as judges.
- C3: N — rationale spot-check on a few examples, no human labels collected/compared on a sample; paper itself says "further work is needed" on GPT-4/human alignment in other languages.
- C4: N. C5: N.

## Paper 4: LongWriter: Unleashing 10,000+ Word Generation from Long Context LLMs
- Venue/year: arXiv 2024 / ICLR 2025 (arXiv:2408.07055)
- URL: https://arxiv.org/abs/2408.07055 (inspected full PDF, pp.3-8 + full-text grep)
- Judge: GPT-4o scores output quality S_q on 6 dimensions (LongBench-Write).
- C1: N — full-text grep for agreement/kappa/correlation/annotator/inter-rater: nothing for the judge.
- C2: N — GPT-4o only.
- C3: N — manual checks were for training-data selection, not judge validation.
- C4: N. C5: N.
- Note: Table 3 footnote acknowledges self-judging bias ("we utilize GPT4-o to judge ... may bring unfairness when judging itself"); no mitigation.

## Paper 5: Language Imbalance Driven Rewarding for Multilingual Self-improving
- Venue/year: arXiv 2024 (2410.08964)
- URL: https://arxiv.org/abs/2410.08964 (inspected full PDF via text extraction)
- Judge: GPT-4 Turbo (X-AlpacaEval win rates, MT-Bench), GPT-4 0-10 quality score; GPT-4o re-run as robustness check (Appendix D.2).
- C1: N — GPT-4 vs GPT-4o consistency described qualitatively ("aligns with"); no agreement statistic, no human comparison.
- C2: N — GPT-4/GPT-4o are the same (OpenAI) family.
- C3: N — cites prior work (Hada et al. 2023) on judge limitations instead of validating.
- C4: N. C5: N.
- Note: Appendix D devoted to judge bias mitigation (language bias, translationese) — bias-aware but no reliability stats.

# BATCH 1 COMPLETE (5/25)

## Paper 6: Magpie: Alignment Data Synthesis from Scratch by Prompting Aligned LLMs with Nothing
- Venue/year: ICLR 2025 (arXiv:2406.08464)
- URL: https://arxiv.org/abs/2406.08464 (inspected arXiv HTML v2)
- Judge: GPT-4-Turbo(1106)/GPT-4(0314) via AlpacaEval 2 + Arena-Hard.
- C1: N. C2: N (GPT-4 variants only). C3: N. C4: N. C5: N.

## Paper 7: SEFL: Harnessing Large Language Model Agents for Semi-Automated Educational Feedback (Synthetic Educational Feedback Loops)
- Venue/year: arXiv 2025 (2502.12927)
- URL: https://arxiv.org/abs/2502.12927 (inspected arXiv HTML v2)
- Judge: 4 LLM judges — GPT-4o, Claude-3.5-Sonnet, Command-R+, DeepSeek-V3 — rate feedback quality.
- C1: Y — pairwise Cohen's kappa between each LLM judge and human raters, range 0.17-0.58.
- C2: Y — 4 different families (OpenAI, Anthropic, Cohere, DeepSeek).
- C3: Y — 150 random instances rated by all 4 LLMs and human raters.
- C4: N — no threshold; Command R+ "sits at the lower extreme" yet all judges retained.
- C5: N.

## Paper 8: Multimodal Cognitive Reframing Therapy via Multi-hop Psychotherapeutic Reasoning
- Venue/year: arXiv 2025 (2502.06873; NAACL/ACL-family submission)
- URL: https://arxiv.org/abs/2502.06873 (inspected arXiv HTML v1)
- Judge: GPT-4 scores generated therapy responses; separate human eval by 2 hired psychotherapists (pairwise).
- C1: N — no kappa/correlation between GPT-4 and human evaluators reported.
- C2: N — GPT-4 only automated judge.
- C3: Y (weak) — Table 3 shows human and GPT-4 evaluation side-by-side on same test set; consistency qualitative, no statistic. Justified by citing prior work that GPT-4 "closely aligns with human evaluations".
- C4: N. C5: N.

## Paper 9: HealthBench: Evaluating Large Language Models Towards Improved Human Health
- Venue/year: arXiv 2025 (2505.08775, OpenAI)
- URL: https://arxiv.org/abs/2505.08775 (inspected arXiv HTML v1)
- Judge: GPT-4.1 grades responses against 48,562 physician-written rubric criteria.
- C1: Y — meta-evaluation: grader macro F1 = 0.709 vs physician-physician agreement (0.569-0.730 across themes); grader "in the upper half of physicians for six out of seven themes".
- C2: N — grader ablations are all OpenAI models (GPT-4.1 variants, o3, o4-mini).
- C3: Y — ~60,896 meta-examples with physician labels.
- C4: N — extensive post-hoc meta-eval, but no pre-stated acceptance gate.
- C5: N.

## Paper 10: Tulu 3: Pushing Frontiers in Open Language Model Post-Training
- Venue/year: arXiv 2024, AI2 (2411.15124; COLM 2025)
- URL: https://arxiv.org/abs/2411.15124 (inspected full PDF via text extraction)
- Judge: AlpacaEval 2 (GPT-4-judged) in dev suite; new HREF unseen eval uses Llama-3.1-70B-Instruct judge chosen from pool {GPT-4, GPT-4-Turbo, Llama-3.1 7B/70B}; LLM-as-judge also used for preference-data annotation (GPT-4o).
- C1: Y — "our composite evaluation procedure resulted in an agreement of 69.4% with humans, which is comparable to the inter-human agreement of 67%" (HREF).
- C2: Y — GPT-4-family judge (AlpacaEval 2) + Llama-family judge (HREF) across benchmarks; multiple families tested as candidate judges.
- C3: Y — 4 human judgments per response pair over 16 models; judge/setup selected by agreement with majority human judgment, per task category.
- C4: N — judge chosen by highest relative agreement; no absolute pre-committed acceptance threshold stated.
- C5: Y (partial) — where LM judge had lower human agreement (Open QA, Fact Checking), procedure falls back to embedding similarity vs human references; a measured, per-category fallback, though not framed as a contingency gate.

# BATCH 2 COMPLETE (10/25)

## Paper 11: MedTutor: A Retrieval-Augmented LLM System for Case-Based Medical Education
- Venue/year: arXiv 2026 (2601.06979)
- URL: https://arxiv.org/abs/2601.06979 (inspected arXiv HTML v1, two passes)
- Judge: 4 LLM judges — MedGemma-27B, GPT-4.1-mini, Gemini-2.5-Flash, Gemini-2.5-Pro; plus board-certified radiologists as human evaluators.
- C1: UNCLEAR — text says "analysis using correlation between LLMs outputs and human expert judgments reveals a moderate alignment", but no coefficient located in inspected text; Krippendorff's alpha reported only BETWEEN the two human radiologists (human-human IAA).
- C2: Y — Google (MedGemma/Gemini) + OpenAI (GPT-4.1-mini) families.
- C3: Y — radiologists rated the same outputs; LLM-vs-human score comparison reported (LLM avg 4.20 vs human 2.88 on relevance; inflation noted).
- C4: N. C5: N.

## Paper 12: MSRS: Evaluating Multi-Source Retrieval-Augmented Generation
- Venue/year: arXiv 2025 (2508.20867)
- URL: https://arxiv.org/abs/2508.20867 (inspected arXiv HTML v1, two passes)
- Judge: G-Eval LLM-based relevance scoring as a main metric; judge model identity not clearly named in inspected text (G-EVAL #1/#2 label generator models, not judges).
- C1: N — human eval (2 expert annotators, 40 samples) assesses dataset/output quality, not judge reliability; no agreement stats.
- C2: UNCLEAR — evaluator model(s) not clearly identified in inspected text.
- C3: N. C4: N. C5: N.

## Paper 13: An Empirical Study on Preference Tuning Generalization and Diversity Under Domain Shift
- Venue/year: arXiv 2026 (2601.05882)
- URL: https://arxiv.org/abs/2601.05882 (inspected arXiv HTML v1)
- Judge: GPT-5-nano (OpenAI API), win rate vs reference responses.
- C1: N. C2: N (single judge). C3: N. C4: N. C5: N.
- Note: Limitations concede "we rely on LLM-as-a-judge... automated judges can favor specific stylistic patterns, and we do not perform large-scale human evaluation".

## Paper 14: AppellateGen: A Benchmark for Appellate Legal Judgment Generation
- Venue/year: arXiv 2026 (2601.01331)
- URL: https://arxiv.org/abs/2601.01331 (inspected arXiv HTML v1)
- Judge: DeepSeek-V3.2 scores generations on 0-5 Likert scale with rubrics.
- C1: N. C2: N (DeepSeek only). C3: N. C4: N. C5: N.

## Paper 15: The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery
- Venue/year: arXiv 2024, Sakana AI (2408.06292)
- URL: https://arxiv.org/abs/2408.06292 (inspected full PDF via text extraction)
- Judge: GPT-4o automated reviewer scores generated papers (NeurIPS-style 1-10); headline claim ("papers exceed acceptance threshold") rests on it.
- C1: Y — vs ICLR 2022 OpenReview human decisions: balanced acc 0.65 vs 0.66 (human), F1 0.57 vs 0.49, AUC 0.65 both; LLM-vs-avg-human score correlation 0.18 vs human-human 0.14.
- C2: N — GPT-4o is the operative reviewer; Claude 3.5 Sonnet / GPT-4o-mini / Llama 3.1 405B tested as candidates but "substantially worse" and not used.
- C3: Y — validated on 500 ICLR 2022 papers with human labels (note: validation corpus is human-written papers, not its own AI-generated papers — distribution shift caveat).
- C4: N — decision threshold (score 6 = weak accept) is a task threshold, not a pre-committed judge-quality gate.
- C5: N.

# BATCH 3 COMPLETE (15/25)

## Paper 16: DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning
- Venue/year: arXiv 2025, DeepSeek-AI (2501.12948)
- URL: https://arxiv.org/abs/2501.12948 (inspected arXiv HTML v1)
- Judge: GPT-4-Turbo-1106 via AlpacaEval 2.0 + Arena-Hard pairwise judging.
- C1: N. C2: N. C3: N. C4: N. C5: N.
- Note: only judge-hygiene step mentioned: passing "only the final summary" to avoid length bias.

## Paper 17: Assisting in Writing Wikipedia-like Articles From Scratch with Large Language Models (STORM)
- Venue/year: NAACL 2024 (arXiv:2402.14207)
- URL: https://arxiv.org/abs/2402.14207 (inspected full PDF via text extraction)
- Judge: Prometheus-13B (Llama-2-based evaluator LLM) scores articles on 5-pt rubric co-designed with Wikipedia editors; Mistral-7B-Instruct judges citation support.
- C1: N — Krippendorff's alpha reported only among human editors (IAA); no judge-human agreement statistic.
- C2: Y (literal) — Prometheus (Llama-family) + Mistral-family judges, though for different metrics, not triangulation of the same score.
- C3: Y (weak) — separate human eval (10 experienced Wikipedia editors, 20 article pairs) run in parallel; reveals "evaluator LLM overrating machine-generated text"; qualitative comparison only.
- C4: N. C5: N.

## Paper 18: Aya Model: An Instruction Finetuned Open-Access Multilingual Language Model
- Venue/year: ACL 2024 (arXiv:2402.07827, Cohere For AI)
- URL: https://arxiv.org/abs/2402.07827 (inspected full PDF via text extraction)
- Judge: GPT-4 as "proxy judge" for simulated win rates across 10 languages; parallel professional-annotator human eval in 7 languages.
- C1: Y — GPT-4-vs-human agreement 70.4%/77.3% (Aya vs mT0x/mT0), human-human IAA 65-77%; Appendix Table 16/17 per-language agreement 38.9%-86.5%.
- C2: N — GPT-4 only.
- C3: Y — human preferences used "to ground and validate simulated preferences"; subset double-annotated "to calibrate the LLM-as-a-judge agreements".
- C4: N — closest-to-gate: Portuguese/Yoruba excluded because GPT-4 judge performance "is not reported" for them (capability-coverage exclusion, not a quality threshold).
- C5: N.

## Paper 19: PersonaGym: Evaluating Persona Agents and LLMs
- Venue/year: arXiv 2024 (2407.18416; EMNLP Findings 2025)
- URL: https://arxiv.org/abs/2407.18416 (inspected full PDF via text extraction)
- Judge: ensemble of GPT-4o + Llama-3-70B score agent responses 1-5 against task rubrics (PersonaScore).
- C1: Y — Table 3: Spearman/Kendall-Tau correlations between PersonaScore and human evaluation scores (100 personas).
- C2: Y — OpenAI + Meta families, ensembled "to ensure robustness and reduce individual model bias".
- C3: Y — human evaluation on sampled personas used to validate PersonaScore.
- C4: N. C5: N (ensembling is robustness-by-design, not a stated unreliability contingency).

## Paper 20: MT-Bench-101: A Fine-Grained Benchmark for Evaluating LLMs in Multi-Turn Dialogues
- Venue/year: ACL 2024 (aclanthology.org/2024.acl-long.401)
- URL: https://aclanthology.org/2024.acl-long.401/ (inspected anthology PDF via text extraction)
- Judge: GPT-4 scores dialogues (1-10); alternate Qwen-72B-Chat judge leaderboard as self-bias check.
- C1: Y — GPT-4-vs-human agreement 87% vs human-human 80% (100 dialogues, 5 experts); Fleiss Kappa GPT-4-vs-humans reported (Table 9).
- C2: Y — GPT-4 + Qwen-72B-Chat judges; rankings "consistent".
- C3: Y — 100 sampled dialogues, 5 expert annotators, majority vote.
- C4: N. C5: N.

# BATCH 4 COMPLETE (20/25)

## Paper 21: HelloBench: Evaluating Long Text Generation Capabilities of LLMs
- Venue/year: arXiv 2024 (2409.16191)
- URL: https://arxiv.org/abs/2409.16191 (inspected arXiv HTML v1)
- Judge: HelloEval = GPT-4o with checklist, weights regression-fit on human annotations; GPT-4o-mini as cheap variant.
- C1: Y — "HelloEval shows the highest correlation with human evaluation", Spearman rho reported (31.93, p=4.67e-7).
- C2: N — OpenAI judges only.
- C3: Y — human annotation data collected on outputs of 4 models in preparation stage for fitting/validating.
- C4: N. C5: N.

## Paper 22: AutoSurvey: Large Language Models Can Automatically Write Surveys
- Venue/year: NeurIPS 2024 (arXiv:2406.10252)
- URL: https://arxiv.org/abs/2406.10252 (inspected arXiv HTML v2)
- Judge: mixture of GPT-4, Claude-3-Haiku, Gemini-1.5-Pro score survey quality.
- C1: Y — Spearman's rho vs human expert rankings; mixture best at 0.5429.
- C2: Y — 3 families, score-averaged.
- C3: Y — meta-evaluation: experts judge survey pairs; LLM vs human rankings correlated.
- C4: N. C5: N.

## Paper 23: Igniting Creative Writing in Small Language Models: LLM-as-a-Judge versus Multi-Agent Refined Rewards
- Venue/year: arXiv 2025 (2508.21476)
- URL: https://arxiv.org/abs/2508.21476 (inspected arXiv HTML v1)
- Judge: final eval "excellence rates" scored by GPT-4o, Ernie-4.5, DeepSeek-V3 + trained human evaluator team; LLM-based reward frameworks also used in training.
- C1: Y (weak) — agreement of their LLM-based assessment frameworks with human judgments "exceeding 70%", 80-87% (Fig 2); benchmark judges themselves not separately validated.
- C2: Y — OpenAI + Baidu + DeepSeek families.
- C3: Y — professionally trained evaluators; agreement rates vs humans reported.
- C4: N. C5: N.

## Paper 24: SWAG: Storytelling With Action Guidance
- Venue/year: arXiv 2024 (2402.03483; EMNLP Findings 2024 per listing)
- URL: https://arxiv.org/abs/2402.03483 (inspected arXiv HTML v2)
- Judge: GPT-4-Turbo pairwise story comparisons; separate human eval (Surge AI, 50 pairs).
- C1: N — no agreement statistic; human eval run as separate arm.
- C2: N — single LLM judge.
- C3: N — no validation framing; they note judge-human discrepancy ("most likely due to GPT-4-Turbo inherent bias towards GPT-3.5-Turbo") and keep both.
- C4: N. C5: N.

## Paper 25: LAURA: Enhancing Code Review Generation with Context-Enriched Retrieval-Augmented LLM
- Venue/year: arXiv 2025 (2512.01356)
- URL: https://arxiv.org/abs/2512.01356 (inspected arXiv HTML v1)
- Judge: ChatGPT-4o (gpt-4o-2024-11-20) sole judge over anonymized review-comment sets.
- C1: N. C2: N. C3: N — human eval conducted separately, no cross-validation. C4: N. C5: N.

# BATCH 5 COMPLETE (25/25)

## Excluded after inspection (not usable / out of scope)
- MAVIS (arXiv:2508.13415): inspected HTML v1 — evaluation uses trained reward models, not LLM judges. Excluded.
- GREP / Expert Preference-based Evaluation of Related Work Generation (arXiv:2508.07955): judge-methods paper (contribution IS the evaluation framework). Excluded per inclusion rule.
- HealthBench initially looked human-only from abstract; methods inspection confirmed model grader — INCLUDED as Paper 9.
- Tulu 3 abstract did not mention judges; full-PDF inspection confirmed judge usage — INCLUDED as Paper 10.

---
# FINAL TALLIES (N=25)
- C1 any inter-judge/judge-human agreement statistic: Y=10 (40%), N=14 (56%), UNCLEAR=1 (MedTutor)
- C2 judges from 2+ model families: Y=9 (36%), N=15 (60%), UNCLEAR=1 (MSRS)
- C3 judge validated vs human labels on a sample: Y=14 (56%, of which 3-4 qualitative-only), N=11 (44%)
- C4 pre-committed acceptance threshold: Y=0 (0%), N=25 (100%)
- C5 pre-specified fallback: Y=1 (4%, Tulu 3 partial), N=24 (96%)
- C1 AND C3 (quantitative human validation): 10/25 (40%)
- Pattern: model/method papers consuming off-the-shelf judged benchmarks (SimPO, Magpie, DeepSeek-R1, LongWriter, LangImbalance, SWAG, LAURA, PrefTuning, AppellateGen, SambaLingo, MSRS) are C1=N 11/11; benchmark/eval-construction papers mostly validate.
