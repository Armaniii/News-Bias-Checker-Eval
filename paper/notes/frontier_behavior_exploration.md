# Frontier-model behavior: deep exploration for bias-detection (2026-07-14)
Cached data only, no API calls, pre-registration ignored per instruction.
4 models: targets Claude Sonnet 4.5 + GPT-4.1 (eval-A/B/C); judges
Claude Sonnet 4.6 + GPT-5 (article_ratings). All statistically checked.

## 1. Lean-Right is the single hardest class for EVERY model
Exact accuracy by true class (each of 4 models):
| model | Left | Lean L | Center | **Lean R** | Right |
|---|---|---|---|---|---|
| Sonnet 4.5 | .97 | .23 | .50 | **.07** | .90 |
| GPT-4.1 | .88 | .47 | .75 | **.46** | .72 |
| Sonnet 4.6 | .92 | .78 | .55 | **.20** | .80 |
| GPT-5 | .82 | .70 | .53 | **.42** | .60 |
- Mean models-wrong (of 4) by class: **Lean-Right 2.85**, Lean-Left 1.82,
  Center 1.68, Right 0.98, Left 0.38. The moderate-right zone is the failure.
- Stronger expert lean → EASIER: Spearman |lean rating| vs n-wrong = **-0.37**
  (p=7e-8). Length does not predict difficulty (rho=-0.09, ns).

## 2. Misclassified moderate-right is pulled LEFT, not just to center
Predicted-class distribution given true class (pooled 4 models):
- true **Lean-Right**: only 29% correct; **33% called Lean-Left or Left**,
  21% Center. (i.e. more often labeled left-of-true than centrist.)
- true **Center**: 58% correct; **32% called Lean-Left**, 4% Lean-Right.
- true Lean-Left: 54% correct, 28% called (further) Left.
- true Right: 76% correct; true Left 90% correct — extremes are safe.
- **DEPLOYMENT CONSEQUENCE**: a "balanced feed" or bias-label tool built on
  frontier-model lean classification will systematically under-count
  right-leaning content — moderate-right reads as center/left. This is the
  sharp, consequential form of "center-collapse."

## 3. Multi-model consensus is a strong, cheap accuracy signal
- 4/4 unanimous (44% of articles): **87% accurate**
- >=3/4 agree (74%): 75% | >=2/4 (99%): 62% — monotone.
- Extends the 2-model triage: unanimity among independent frontier models
  is the best free confidence signal available.

## 4. Hardest TOPICS: policy-abstract > identity-concrete
mean models-wrong/4: elections_governance 1.92, economy 1.92,
climate_energy 1.88, foreign_defense 1.52, immigration 1.48,
health_education 1.29, crime_justice 1.28, social_culture_rights 1.04.
- Deployment-domain guidance: lean classification is least reliable on
  elections/economy/climate coverage.

## 5. Models have different detection "personalities"
Share of each target's ablation-condition flags:
- Sonnet 4.5: word choice 17%, **bias by omission 14%**, opinion-as-fact 12%,
  subjective adjectives 12% (mean 6.4 flags/article)
- GPT-4.1: **sensationalism 15%**, subjective adjectives 14%, opinion-as-fact
  12%, spin 12% (mean 6.0)
- Claude hunts what's LEFT OUT; GPT hunts emotional TONE. This mechanistically
  explains the near-chance cross-model agreement on omission (kappa 0.14):
  one model looks for it, the other doesn't.

## 6. Claude gives right-leaning articles thinner summaries (model-specific)
Sonnet 4.5, by source lean (L vs R):
- perspectives 4.46 vs **3.84** (p=.001), key facts 9.47 vs **8.69** (p=.002),
  summary length 89 vs **81 words** (p=.004) — all three thinner on right.
- GPT-4.1: all near-null (p=.09/.93/.18).
- Because GPT does NOT show it, the asymmetry is unlikely to be an article
  property (fewer real sources on the right) — it is Claude's treatment.
  Upgrades the paper's currently-"unverifiable" perspective finding to
  model-specific behavioral.

## 7. Which specific text gets highlighted is barely reproducible
- Cross-model span word-overlap (Sonnet vs GPT, both flagging same article):
  **Jaccard 0.26**. Two frontier models highlight largely different text even
  when both flag the article.
- DEPLOYMENT: no single model's highlight is authoritative; only cross-model
  agreed highlights should be shown as reliable.

## Bottom line for a bias-detection product
The reliable primitives are: detection VOLUME (a valid intensity meter,
Finding 4), cross-model AGREEMENT (triage), and concrete word-level flags.
The unreliable primitives are: any single lean label near the center-right,
any omission/framing/unsupported flag, and any specific highlight — all
model-specific opinion, not detected fact. And the systematic failure mode
is directional: moderate-right content is read as center/left by all
frontier models tested.
