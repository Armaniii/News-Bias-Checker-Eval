# True-Behavior Profile — empirical results

Computed by `analysis/true_behavior_profile.py`. Methodology in `METHODS.md`.

## Profile matrix

| Target | Condition | EP [95% CI] | CFI(Opus) | CFI(GPT-5) | LCA(AllSides) 3-class | LCA(Opus) 3-class | LCA(GPT-5) 3-class |
|--------|-----------|-------------|-----------|-----------|----------------------|-------------------|--------------------|
| sonnet | baseline | 1.000 [1.000, 1.000] | 27.8% | 9.8% | 81.1% | 81.7% | 74.7% |
| sonnet | ablation | 1.000 [1.000, 1.000] | 25.1% | 11.3% | 77.9% | 88.2% | 77.9% |
| sonnet | full | 1.000 [1.000, 1.000] | 11.2% | 2.5% | 75.0% | 83.3% | 76.1% |
| gpt | baseline | 0.966 [0.882, 1.000] | 25.3% | 11.7% | 73.7% | 82.8% | 69.5% |
| gpt | ablation | 1.000 [1.000, 1.000] | 24.4% | 9.2% | 70.5% | 82.8% | 70.5% |
| gpt | full | 1.000 [1.000, 1.000] | 6.5% | 1.1% | 69.5% | 79.6% | 74.7% |

**EP** = Engagement Parity, disparate-impact ratio across 3-class lean strata (METHODS §1.1).
**CFI** = Content Framing Inheritance, absorption rate at threshold ≥ 5 (METHODS §1.2).
**LCA** = Lean Classification Accuracy, 3-class match rate across three ground-truth options (METHODS §1.3).

## EP × CFI dissociation test

- **N cells:** 6
- **Pearson r(EP, CFI):** -0.342, p=0.507
- **var(EP):** 0.00017
- **var(CFI):** 0.00374
- **var(CFI)/var(EP) ratio:** 22.6

_Low |r| with var(CFI) >> var(EP) supports the dissociation claim: CFI varies substantially across cells while EP is approximately invariant. This is the empirical anchor for the category-error argument in FRAME §'Conceptual framing'._