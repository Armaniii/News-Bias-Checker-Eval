# Survey dual-coding sheet — human second coder (BLIND)

You are the independent second coder for the judge-validation prevalence
survey (paper Appendix A). Code each paper on the five binary fields
below **without looking at** `judge_validation_survey.md` (the first
pass's codes). Mark Y / N / U (unclear). Coding basis: the paper's
abstract + methods/evaluation sections, via the URL given. ~2–4 min per
paper; you only need to find whether each practice is *reported*, not
evaluate its quality.

**The five fields:**
- **C1** — reports ANY inter-judge or judge–human agreement statistic
  (κ, α, F1-vs-human, % agreement — anything quantitative)?
- **C2** — uses judges from 2+ DIFFERENT model families (e.g., GPT +
  Claude), not just one judge or same-family variants?
- **C3** — validates the judge against human labels on a sample
  (quantitative or qualitative side-by-side)?
- **C4** — states an acceptance threshold the judge had to meet BEFORE
  its scores were used (a pre-committed gate, not post-hoc reporting)?
- **C5** — pre-specifies any fallback procedure if the judge proves
  unreliable?

| # | Paper | URL | C1 | C2 | C3 | C4 | C5 |
|---|-------|-----|----|----|----|----|----|
| 1 | Self-Rewarding Language Models | arxiv.org/abs/2401.10020 | | | | | |
| 2 | SimPO | arxiv.org/abs/2405.14734 | | | | | |
| 3 | SambaLingo | arxiv.org/abs/2404.05829 | | | | | |
| 4 | LongWriter | arxiv.org/abs/2408.07055 | | | | | |
| 5 | Language Imbalance Driven Rewarding | arxiv.org/abs/2410.08964 | | | | | |
| 6 | Magpie | arxiv.org/abs/2406.08464 | | | | | |
| 7 | SEFL (educational feedback) | arxiv.org/abs/2502.12927 | | | | | |
| 8 | Multimodal Cognitive Reframing Therapy | arxiv.org/abs/2502.06873 | | | | | |
| 9 | HealthBench (OpenAI) | arxiv.org/abs/2505.08775 | | | | | |
| 10 | Tulu 3 (AI2) | arxiv.org/abs/2411.15124 | | | | | |
| 11 | MedTutor | arxiv.org/abs/2601.06979 | | | | | |
| 12 | MSRS (multi-source RAG) | arxiv.org/abs/2508.20867 | | | | | |
| 13 | Preference Tuning under Domain Shift | arxiv.org/abs/2601.05882 | | | | | |
| 14 | AppellateGen (legal) | arxiv.org/abs/2601.01331 | | | | | |
| 15 | The AI Scientist (Sakana) | arxiv.org/abs/2408.06292 | | | | | |
| 16 | DeepSeek-R1 | arxiv.org/abs/2501.12948 | | | | | |
| 17 | STORM (NAACL 2024) | arxiv.org/abs/2402.14207 | | | | | |
| 18 | Aya Model (Cohere) | arxiv.org/abs/2402.07827 | | | | | |
| 19 | PersonaGym | arxiv.org/abs/2407.18416 | | | | | |
| 20 | MT-Bench-101 (ACL 2024) | aclanthology.org/2024.acl-long.401/ | | | | | |
| 21 | HelloBench | arxiv.org/abs/2409.16191 | | | | | |
| 22 | AutoSurvey | arxiv.org/abs/2406.10252 | | | | | |
| 23 | Igniting Creative Writing in SLMs | arxiv.org/abs/2508.21476 | | | | | |
| 24 | SWAG: Storytelling With Action Guidance | arxiv.org/abs/2402.03483 | | | | | |
| 25 | LAURA (code review) | arxiv.org/abs/2512.01356 | | | | | |

**When done:** commit this file; agreement vs. the first pass gets
computed per field (5 × 25 cells), reported in the Appendix A caption,
and disagreements resolved by discussion with the written basis in the
survey log. This closes reviewer items EIC-W8 / R1-m5b / R2-W6a / R3-W8 /
DA-M2 (all five reviewers independently required a human second coder).
