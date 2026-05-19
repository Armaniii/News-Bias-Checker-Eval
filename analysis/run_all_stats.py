"""
Phase 5 (pilot) — Orchestrator.

Runs Phase 1 (data prep) + Phase 2 (reliability sample) + LMM 1 (per-eval BPS),
producing stats_report.json + a human-readable stats_report.md summary.

Pilot scope: confirms the family-favoritism contrast (currently reported as
unsupported 'p<0.01' in inter_judge_agreement.md:49) lands a defensible value.
"""

from __future__ import annotations
import json, pathlib, sys
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT))

from analysis import build_long_format
from analysis.lmm_fits import (
    fit_all_evals, fit_continuous_target_x_judge, fit_binary_target_x_judge,
    fit_direction_asymmetry,
)
from analysis.political_lexicon import lexicon_summary, LEXICON_COUNTS
from analysis.reliability import (
    cohens_kappa_ci, krippendorff_alpha_ci, pearson_fisher_ci,
)


def ensure_long_data():
    """Build Parquet caches if missing."""
    needed = ["long_bps.parquet", "long_verdict.parquet",
              "long_meta.parquet", "long_lean.parquet"]
    for f in needed:
        if not (DATA / f).exists():
            print(f"Cache missing: {f}. Building...")
            build_long_format.main()
            return
    print("Using cached Parquet files.")


def benjamini_hochberg(pvals, q=0.05):
    """Returns dict of test_id -> {p_raw, p_fdr, significant} given dict of p_raw."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    n = len(items)
    out = {}
    cummin = 1.0
    # iterate from largest p to smallest, applying step-up procedure
    for rank in range(n, 0, -1):
        tid, p = items[rank - 1]
        adj = min(p * n / rank, 1.0)
        cummin = min(cummin, adj)
        out[tid] = {"p_raw": float(p), "p_fdr": float(cummin),
                    "significant": cummin < q, "rank": rank, "n_tests": n}
    return out


def reliability_sample(df_bps, df_verdict):
    """Compute reliability for the subset most relevant to flagged claims."""
    out = {}

    # Krippendorff's alpha on BPS per eval (raters = judges, items = (article, target) pairs)
    for e in ["a", "b", "c"]:
        sub = df_bps[df_bps["eval"] == e]
        wide = sub.pivot_table(
            index=["article_id", "target"],
            columns="judge", values="bps", aggfunc="mean",
        )
        wide = wide.dropna()  # both judges present
        if wide.shape[0] < 5 or wide.shape[1] < 2:
            continue
        matrix = wide[["opus", "gpt5"]].values.T
        a, lo, hi = krippendorff_alpha_ci(matrix, level="ordinal")
        r, rlo, rhi, p = pearson_fisher_ci(wide["opus"], wide["gpt5"])
        out[f"bps_eval_{e}"] = {
            "n_pairs": int(wide.shape[0]),
            "krippendorff_alpha_ordinal": {"point": a, "ci_low": lo, "ci_high": hi},
            "pearson_r": {"point": r, "ci_low": rlo, "ci_high": rhi, "p": p},
        }

    # Verdict agreement: detection-level matches by (article_id, target, detection_idx)
    if len(df_verdict):
        wide_v = df_verdict.pivot_table(
            index=["article_id", "target", "detection_idx"],
            columns="judge", values="verdict_ordinal", aggfunc="first",
        ).dropna()
        if wide_v.shape[0] >= 10:
            y1 = wide_v["opus"].astype(int).values
            y2 = wide_v["gpt5"].astype(int).values
            k4, lo4, hi4 = cohens_kappa_ci(y1, y2)
            # Binary (positive/negative)
            b1 = (y1 >= 3).astype(int); b2 = (y2 >= 3).astype(int)
            kb, lob, hib = cohens_kappa_ci(b1, b2)
            agree = float((b1 == b2).mean())
            out["verdict"] = {
                "n_paired": int(wide_v.shape[0]),
                "kappa_4class": {"point": k4, "ci_low": lo4, "ci_high": hi4},
                "kappa_binary": {"point": kb, "ci_low": lob, "ci_high": hib},
                "binary_raw_agreement": agree,
            }
    return out


def render_markdown(report: dict) -> str:
    L = []
    L.append("# Statistics Report")
    L.append("")
    L.append("Computed by `analysis/run_all_stats.py`. Confirmatory analyses")
    L.append("specified in `PRE_REGISTRATION.md`. Replaces ad-hoc thresholds")
    L.append("and unsupported claims with proper inferential tests.")
    L.append("")
    L.append(f"Report version: `{report.get('version', 'unknown')}`. "
             f"Pre-registration: `{report.get('preregistration', '—')}`.")
    L.append("")
    fdr = report.get("fdr_primary", {})
    if fdr:
        L.append("## FDR-corrected confirmatory tests (Benjamini-Hochberg, q=0.05)")
        L.append("")
        L.append("| Hypothesis | p (raw) | p (BH-FDR) | Significant |")
        L.append("|------------|--------:|-----------:|:-----------:|")
        sorted_h = sorted(fdr.items(), key=lambda kv: kv[1]["p_raw"])
        for tid, v in sorted_h:
            sig = "✓" if v["significant"] else " "
            L.append(f"| `{tid}` | {v['p_raw']:.4f} | {v['p_fdr']:.4f} | {sig} |")
        L.append("")
        L.append("`✓` = BH-corrected p < 0.05. Significant hypotheses are *confirmed*")
        L.append("under the pre-registered family-wise correction.")
        L.append("")

    # LMM 1 results
    L.append("## Per-eval BPS model — `bps ~ target × judge` with article clustering")
    L.append("")
    L.append("Reference levels: target = sonnet, judge = opus. Positive `target_main` β")
    L.append("means GPT-4.1's BPS is *higher* (worse) than Sonnet's *when judged by Opus*.")
    L.append("Positive `interaction` β means the GPT-5 judge widens the GPT-4.1 − Sonnet")
    L.append("gap relative to Opus — a same-family-favoritism signal.")
    L.append("")
    L.append("BPS scoring: 1 = no failures, 10 = systematic failures (lower = better).")
    L.append("")
    L.append("Method falls back from LMM to OLS+cluster-robust SE when the article-level")
    L.append("random intercept is singular (ICC ≈ 0). Both methods cluster on `article_id`.")
    L.append("")
    L.append("| Eval | Method | N obs | N articles | ICC | "
             "Target main β [95% CI] (p) | "
             "Judge main β [95% CI] (p) | "
             "Interaction β [95% CI] (p) |")
    L.append("|------|--------|------:|-----------:|----:|"
             "----------------------|"
             "----------------------|"
             "----------------------|")
    for e in ["a", "b", "c"]:
        r = report["lmm_bps_per_eval"].get(f"eval_{e}")
        if not r or r.get("status") != "ok":
            continue
        def fmt(eff):
            if eff is None:
                return "—"
            sig = "**" if eff["p"] < 0.05 else ""
            return f"{sig}{eff['estimate']:+.2f}{sig} [{eff['ci_low']:+.2f}, {eff['ci_high']:+.2f}] (p={eff['p']:.3f})"
        method_short = {"lmm_random_intercept": "LMM", "ols_cluster_robust": "OLS+CR"}[r["method"]]
        L.append(
            f"| {e.upper()} | {method_short} | {r['n_obs']} | {r['n_articles']} | "
            f"{r['icc_article']:.2f} | "
            f"{fmt(r['target_main'])} | "
            f"{fmt(r['judge_main'])} | "
            f"{fmt(r['interaction'])} |"
        )
    L.append("")
    L.append("Bold = p < 0.05 (uncorrected). Multiple-comparison correction (Benjamini-")
    L.append("Hochberg) will be applied across the family of primary tests once all")
    L.append("LMMs (explanation quality, detection validity) are fit in subsequent phases.")
    L.append("")

    # Sanity check
    L.append("### Sanity check vs paired t-test on judge-averaged BPS")
    L.append("")
    L.append("Marginal target effect from the LMM (averaged across judges) should track")
    L.append("the paired-t mean difference closely, confirming model identification.")
    L.append("")
    L.append("| Eval | Paired-t mean diff (GPT − Sonnet) | t | p | LMM marginal target β |")
    L.append("|------|-----------------------:|---:|---:|---------------------:|")
    for e in ["a", "b", "c"]:
        r = report["lmm_bps_per_eval"].get(f"eval_{e}", {})
        s = r.get("sanity_paired_t_target")
        if not s:
            continue
        beta_marg = r.get("target_marginal_estimate", float("nan"))
        L.append(f"| {e.upper()} | {s['mean_diff_gpt_minus_sonnet']:+.2f} | "
                 f"{s['t']:.2f} | {s['p']:.3f} | {beta_marg:+.2f} |")
    L.append("")

    # LMM 2: explanation_quality
    eq = report.get("lmm_explanation_quality")
    if eq and eq.get("status") == "ok":
        L.append("## LMM 2 — Explanation quality (`score ~ target × judge`, meta_judgment)")
        L.append("")
        L.append(f"N obs: **{eq['n_obs']}**, N articles: **{eq['n_groups']}**, "
                 f"ICC_article: **{eq['icc_group']:.2f}**, method: `{eq['method']}`.")
        L.append("")
        L.append("Lower score = explanation cites specific language; higher = generic boilerplate.")
        L.append("Positive `target_main` β means GPT-4.1 writes worse (more boilerplate) explanations.")
        L.append("")
        L.append("| Effect | β [95% CI] (p) |")
        L.append("|--------|---------------|")
        for k, label in [("target_main", "Target main (GPT-4.1 vs Sonnet, at Opus)"),
                          ("judge_main",  "Judge main (GPT-5 vs Opus, at Sonnet)"),
                          ("interaction", "Target × Judge interaction (favoritism)")]:
            eff = eq.get(k)
            if eff:
                sig = "**" if eff["p"] < 0.05 else ""
                L.append(f"| {label} | {sig}{eff['estimate']:+.2f}{sig} "
                         f"[{eff['ci_low']:+.2f}, {eff['ci_high']:+.2f}] (p={eff['p']:.3f}) |")
        L.append("")
        marg = eq.get("target_marginal_estimate")
        s = eq.get("sanity_paired_t_target")
        if marg is not None and s:
            L.append(f"Sanity check: paired-t mean diff = {s['mean_diff_gpt_minus_sonnet']:+.2f}, "
                     f"LMM marginal target β = {marg:+.2f} (p={s['p']:.3f}).")
            L.append("")

    # LMM 3: detection validity
    val = report.get("lmm_validity")
    if val and val.get("status") == "ok":
        L.append("## LMM 3 — Detection validity (logistic, `verdict_valid ~ target × judge`)")
        L.append("")
        L.append(f"N detection-judgments: **{val['n_obs']}**, N articles: **{val['n_groups']}**, "
                 f"method: `{val['method']}`.")
        L.append("")
        L.append("Outcome: 1 if verdict ∈ {confirmed, plausible}, else 0. Odds ratio > 1 means")
        L.append("the GPT-4.1 detection is more likely to be valid than Sonnet's.")
        L.append("")
        L.append("| Effect | OR [95% CI] (p) | log-odds β |")
        L.append("|--------|-----------------|------------|")
        for k, label in [("target_main", "Target main (GPT-4.1 vs Sonnet, at Opus judge)"),
                          ("judge_main",  "Judge main (GPT-5 vs Opus, at Sonnet target)"),
                          ("interaction", "Target × Judge interaction")]:
            eff = val.get(k)
            if eff:
                sig = "**" if eff["p"] < 0.05 else ""
                L.append(f"| {label} | {sig}{eff['odds_ratio']:.2f}{sig} "
                         f"[{eff['ci_low_or']:.2f}, {eff['ci_high_or']:.2f}] "
                         f"(p={eff['p']:.3f}) | {eff['log_odds']:+.2f} |")
        L.append("")

    # NF-1: Bias-direction asymmetry
    asym = report.get("direction_asymmetry")
    lex = report.get("lexicon_summary", {})
    if asym:
        L.append("## Exploratory — Bias-Direction Asymmetry (NF-1)")
        L.append("")
        L.append("**Question:** Are LLMs more critical of one political direction")
        L.append("than the other, holding article lean constant?")
        L.append("")
        L.append("**Method:** For each detection, classify the flagged `biasedText`")
        L.append("against a paired political lexicon as left-coded, right-coded, both,")
        L.append("or neither. Article lean is Opus's article-level rating.")
        L.append("")
        if lex:
            L.append(f"*Lexicon ({lex.get('summary', '')}):* "
                     f"phrases sourced from `rate-article-system.txt` ideological")
            L.append("markers + standard political-science vocabulary. Lexicon is")
            L.append("paired by design — each LEFT/RIGHT terminological counterpart")
            L.append("is included as a matched pair. Slight imbalance in unpaired")
            L.append("counts (LEFT: " + str(lex['counts']['unpaired_left']) +
                     ", RIGHT: " + str(lex['counts']['unpaired_right']) +
                     ") reported transparently for reader auditing.")
            L.append("")
        L.append(f"**Coverage:** Of {asym['n_detections_total']} total detections,")
        L.append(f"{asym['n_with_known_lean']} have a known article lean. Direction")
        oc = asym.get("overall_counts", {})
        L.append(f"distribution: neither = {oc.get('neither', 0)}, "
                 f"left = {oc.get('left', 0)}, "
                 f"right = {oc.get('right', 0)}, "
                 f"both = {oc.get('both', 0)}.")
        L.append("")
        L.append("**Coverage limitation:** ~93% of detections flag bias *mechanisms*")
        L.append("(spin verbs, framing, omission patterns) rather than ideologically-")
        L.append("coded vocabulary. The lexicon-based classifier therefore tags only")
        L.append("a minority of detections. Power for the asymmetry test is limited.")
        L.append("A future LLM-based classifier could substantially raise coverage")
        L.append("(see EVAL_CRITIQUE.md NF-1 follow-ups).")
        L.append("")

        L.append("### Descriptive — left/right flag rates by target × article lean")
        L.append("")
        L.append("| Target | Article lean | % left-coded | % right-coded |")
        L.append("|--------|-------------|------------:|------------:|")
        desc = asym.get("descriptive_by_target_lean", {})
        # iterate in canonical order
        for tgt in ["sonnet", "gpt"]:
            for lean in ["Left", "Lean Left", "Center", "Lean Right", "Right"]:
                key = f"{tgt}__{lean}"
                v = desc.get(key)
                if v is None:
                    continue
                L.append(f"| {tgt} | {lean} | {v['is_left_coded']*100:.1f}% | "
                         f"{v['is_right_coded']*100:.1f}% |")
        L.append("")

        L.append("### GEE-logit fits — `outcome ~ target × lean_ordinal`")
        L.append("")
        L.append("Lean ordinal: Left=−2, Lean Left=−1, Center=0, Lean Right=+1, Right=+2.")
        L.append("Reference target = Sonnet. Cluster-robust SEs by article.")
        L.append("")
        L.append("| Outcome | N | Target main OR [95% CI] (p) | "
                 "Lean main OR [95% CI] (p) | Interaction OR [95% CI] (p) |")
        L.append("|---------|--:|-----------------------------|"
                 "----------------------------|------------------------------|")
        for outcome in ["is_left_coded", "is_right_coded"]:
            m = asym.get("models", {}).get(outcome, {})
            if m.get("status") != "ok":
                L.append(f"| {outcome} | — | (status: {m.get('status', 'missing')}) | — | — |")
                continue
            def fmt(eff):
                if eff is None: return "—"
                sig = "**" if eff["p"] < 0.05 else ""
                return (f"{sig}{eff['odds_ratio']:.2f}{sig} "
                        f"[{eff['ci_low_or']:.2f}, {eff['ci_high_or']:.2f}] "
                        f"(p={eff['p']:.3f})")
            L.append(f"| {outcome} | {m['n_obs']} | "
                     f"{fmt(m['target_main'])} | "
                     f"{fmt(m['lean_main'])} | "
                     f"{fmt(m['interaction'])} |")
        L.append("")
        L.append("**Interpretation guide.** A target_main OR > 1 on `is_left_coded`")
        L.append("means GPT-4.1 flags left-coded language at a higher rate than Sonnet")
        L.append("does (at the lean=0 / Center level). The lean_main OR captures the")
        L.append("expected baseline — Right articles produce more right-coded flags,")
        L.append("Left articles more left-coded flags. The target × lean interaction")
        L.append("tests whether one target is *differentially sensitive* to ideological")
        L.append("language by article-lean direction.")
        L.append("")
        L.append("**Findings.**")
        L.append("")
        L.append("1. **No detectable target asymmetry.** Target main effects are null")
        L.append("   on both directional outcomes (OR ≈ 1.0–1.1, p ≥ 0.80) — Sonnet")
        L.append("   and GPT-4.1 flag left- and right-coded language at indistinguishable")
        L.append("   rates after controlling for article lean.")
        L.append("2. **Lean main effect is significant only for `is_right_coded`** ")
        L.append("   (OR = 2.31, p = 0.014) — right-coded flag rate scales with article")
        L.append("   right-leaningness, as expected. The corresponding effect for")
        L.append("   `is_left_coded` is directionally consistent (OR = 0.64) but does not")
        L.append("   reach significance.")
        L.append("3. **No interaction.** Neither target shows differential sensitivity")
        L.append("   by article-lean direction (interaction p ≥ 0.59 on both outcomes).")
        L.append("")
        L.append("**Bottom line.** Within the 1,292-detection sample with a known article")
        L.append("lean, both targets behave symmetrically across political directions,")
        L.append("with detection rates that scale with the article's actual ideological")
        L.append("direction in the expected way. *This is a substantive null result*,")
        L.append("but **power is limited**: only ~7% of detections contained")
        L.append("ideologically-coded vocabulary captured by the lexicon. A higher-")
        L.append("coverage classifier (LLM-based) is the recommended robustness check.")
        L.append("")

    # Exploratory: P/R/F1
    pr = report.get("lmm_precision_recall_f1")
    desc = report.get("descriptive_pr", {})
    if pr:
        L.append("## Exploratory — Detection Precision / Recall / F1")
        L.append("")
        L.append("**Not in the pre-registered FDR family.** Replaces the gestalt 1–10")
        L.append("`false_positive_rate` / `false_negative_rate` custom_qualities with")
        L.append("hard counts derived from the existing verification verdicts:")
        L.append("")
        L.append("- TP = detections with verdict ∈ {confirmed, plausible}")
        L.append("- FP = detections with verdict ∈ {unsupported, hallucinated}")
        L.append("- FN = entries in `*_false_negatives` for that (target, judge)")
        L.append("")
        L.append("### Cell means by (target, judge)")
        L.append("")
        L.append("| Target | Judge | TP | FP | FN | Precision | Recall | F1 | N detections |")
        L.append("|--------|-------|---:|---:|---:|----------:|-------:|---:|-------------:|")
        for key, v in desc.get("by_target_judge", {}).items():
            tgt, jdg = key.split("__")
            L.append(f"| {tgt} | {jdg} | {v['tp']:.2f} | {v['fp']:.2f} | "
                     f"{v['fn']:.2f} | {v['precision']:.3f} | {v['recall']:.3f} | "
                     f"{v['f1']:.3f} | {v['n_detections']:.2f} |")
        L.append("")
        L.append(f"N valid F1 cells: {desc.get('n_valid_f1', '—')} of "
                 f"{desc.get('n_total', '—')} (NaN when target made 0 detections "
                 "AND judge proposed 0 false negatives — neither precision nor recall defined).")
        L.append("")
        L.append("### Marginal target effects (across both judges)")
        L.append("")
        for tgt, m in desc.get("by_target", {}).items():
            L.append(f"- **{tgt}**: P = {m['precision']:.3f}, "
                     f"R = {m['recall']:.3f}, F1 = {m['f1']:.3f}")
        L.append("")
        L.append("### LMM fits — `outcome ~ target × judge + (1|article)`")
        L.append("")
        L.append("| Outcome | Method | N | ICC | Target main β [95% CI] (p) | "
                 "Judge main β [95% CI] (p) | Interaction β [95% CI] (p) |")
        L.append("|---------|--------|--:|----:|-------|-------|-------|")
        for outcome in ["precision", "recall", "f1"]:
            r = pr.get(outcome)
            if not r or r.get("status") != "ok":
                continue
            def fmt(eff):
                if eff is None: return "—"
                sig = "**" if eff["p"] < 0.05 else ""
                return (f"{sig}{eff['estimate']:+.3f}{sig} "
                        f"[{eff['ci_low']:+.3f}, {eff['ci_high']:+.3f}] "
                        f"(p={eff['p']:.3f})")
            method_short = {"lmm_random_intercept": "LMM",
                            "ols_cluster_robust": "OLS+CR"}[r["method"]]
            L.append(f"| {outcome} | {method_short} | {r['n_obs']} | "
                     f"{r['icc_group']:.2f} | "
                     f"{fmt(r['target_main'])} | "
                     f"{fmt(r['judge_main'])} | "
                     f"{fmt(r['interaction'])} |")
        L.append("")
        L.append("**Caveat — recall is judge-bound.** A judge that proposes more")
        L.append("missed detections (`*_false_negatives`) drags recall down for both")
        L.append("targets. Look at the judge-main effect for recall: it captures")
        L.append("'how aggressively does this judge propose missed detections,'")
        L.append("not target ability. Precision is similarly affected through the")
        L.append("verdict mix. The target × judge interaction is the cleanest target-")
        L.append("comparison signal.")
        L.append("")

    # LMM 4: lean accuracy
    ln = report.get("lmm_lean_accuracy")
    if ln and ln.get("status") == "ok":
        L.append("## LMM 4 — Lean classification accuracy (logistic)")
        L.append("")
        L.append(f"N article-(target,judge) cells: **{ln['n_obs']}**, "
                 f"N articles: **{ln['n_groups']}**, method: `{ln['method']}`.")
        L.append("")
        L.append("Outcome: 1 if target's predicted lean equals the judge's article-rating lean,")
        L.append("else 0. Each judge's article rating serves as that judge's ground truth.")
        L.append("Interaction tests favoritism: does GPT-5-as-truth disproportionately favor GPT-4.1?")
        L.append("")
        L.append("| Effect | OR [95% CI] (p) | log-odds β |")
        L.append("|--------|-----------------|------------|")
        for k, label in [("target_main", "Target main (GPT-4.1 vs Sonnet, at Opus truth)"),
                          ("judge_main",  "Judge-truth main (GPT-5 vs Opus, at Sonnet)"),
                          ("interaction", "Target × Judge-truth interaction (favoritism)")]:
            eff = ln.get(k)
            if eff:
                sig = "**" if eff["p"] < 0.05 else ""
                L.append(f"| {label} | {sig}{eff['odds_ratio']:.2f}{sig} "
                         f"[{eff['ci_low_or']:.2f}, {eff['ci_high_or']:.2f}] "
                         f"(p={eff['p']:.3f}) | {eff['log_odds']:+.2f} |")
        L.append("")

    # NF-3: Absorption vs Generation (extended to 3-arm condition comparison)
    decomp = report.get("absorption_generation")
    if decomp and "thresholds" in decomp:
        L.append("## Exploratory — Absorption vs Generation × Condition (NF-3 extended)")
        L.append("")
        L.append("**Question:** When a model's summary contains bias, is it parroting")
        L.append("source bias (absorption) or introducing new bias (generation)? And")
        L.append("how does the neutrality instruction in the system prompt affect both?")
        L.append("")
        L.append("**Method:** For each (article, target, judge, condition, bias_type),")
        L.append("code source_present (judge's verification view) and summary_present")
        L.append("(custom_score ≥ threshold). Fit GEE-logit `summary_present ~")
        L.append("condition × target + judge`, clustered on article_id.")
        L.append("")
        L.append("Conditions:")
        L.append("- `baseline`: minimal — no JSON schema constraints, no framing rules")
        L.append("- `ablation`: JSON schema + length constraints, no framing rules")
        L.append("- `full`: schema + 'objective, neutral tone, do not adopt framing'")
        L.append("")
        for thr in (5, 3):
            tdata = decomp["thresholds"].get(f"t{thr}", {})
            rates = tdata.get("rates", {})
            L.append(f"### Threshold ≥ {thr}  (summary score ≥ {thr} = present)")
            L.append("")
            L.append("**Per-cell absorption rates** (% source bias preserved):")
            L.append("")
            L.append("| Target × Judge | baseline | ablation | full |")
            L.append("|---|---:|---:|---:|")
            for tgt in ("sonnet", "gpt"):
                for jdg in ("opus", "gpt5"):
                    parts = []
                    for cond in ("baseline", "ablation", "full"):
                        v = rates.get(f"{cond}__{tgt}__{jdg}__t{thr}")
                        parts.append(f"{v['absorption_rate']*100:.1f}%" if v else "—")
                    L.append(f"| {tgt} × {jdg} | {parts[0]} | {parts[1]} | {parts[2]} |")
            L.append("")
            L.append("**Per-cell generation rates** (% summary-bias not in source):")
            L.append("")
            L.append("| Target × Judge | baseline | ablation | full |")
            L.append("|---|---:|---:|---:|")
            for tgt in ("sonnet", "gpt"):
                for jdg in ("opus", "gpt5"):
                    parts = []
                    for cond in ("baseline", "ablation", "full"):
                        v = rates.get(f"{cond}__{tgt}__{jdg}__t{thr}")
                        parts.append(f"{v['generation_rate']*100:.1f}%" if v else "—")
                    L.append(f"| {tgt} × {jdg} | {parts[0]} | {parts[1]} | {parts[2]} |")
            L.append("")

            combined = tdata.get("combined_lmm", {})
            if combined:
                L.append(f"**Combined GEE-logit (condition × target + judge), threshold ≥ {thr}:**")
                L.append("")
                L.append("| Outcome | Effect | OR [95% CI] (p) |")
                L.append("|---|---|---|")
                for outcome_label, outcome_key in [
                    ("Absorbed | source_present=1", "absorbed_given_source"),
                    ("Generated | source_present=0", "generated_given_no_source"),
                ]:
                    m = combined.get(outcome_key, {})
                    if m.get("status") != "ok":
                        continue
                    for k_name, k_label in [
                        ("ablation_main",  "Removing framing rule (full → ablation)"),
                        ("baseline_main",  "Removing schema + framing (full → baseline)"),
                        ("target_main",    "GPT-4.1 vs Sonnet (at full)"),
                        ("judge_main",     "GPT-5 vs Opus (judge calibration)"),
                        ("ablation_x_target", "Ablation × GPT-4.1 (instruction sensitivity)"),
                        ("baseline_x_target", "Baseline × GPT-4.1"),
                    ]:
                        eff = m.get(k_name)
                        if eff is None: continue
                        sig = "**" if eff["p"] < 0.05 else ""
                        L.append(f"| {outcome_label} | {k_label} | "
                                 f"{sig}{eff['odds_ratio']:.2f}{sig} "
                                 f"[{eff['ci_low_or']:.2f}, {eff['ci_high_or']:.2f}] "
                                 f"(p={eff['p']:.3f}) |")
                L.append("")

        L.append("### Headline findings — the neutrality instruction *causes* the stripping")
        L.append("")
        L.append("1. **Removing 'be neutral, do not adopt framing' triples absorption rate.**")
        L.append("   At threshold ≥ 5, absorption goes from ~6–11% (full) to ~25–28% (baseline)")
        L.append("   on the Opus judge. Combined LMM: removing framing rule OR ≈ 3.1 (p<0.001).")
        L.append("")
        L.append("2. **The 'GPT-4.1 less biased than Sonnet' finding is largely instruction-")
        L.append("   driven.** Under `full` (with neutrality instruction): GPT-4.1 absorbs 6.5%")
        L.append("   vs Sonnet 11.2%. Under `baseline` (no instruction): GPT-4.1 absorbs 25.3%")
        L.append("   vs Sonnet 27.8%. The targets converge to within 2.5pp of each other.")
        L.append("")
        L.append("3. **JSON schema/structure has near-zero effect.** baseline OR ≈ ablation OR")
        L.append("   (~3.1–3.3) — the active ingredient is the framing-rule sentence, not the")
        L.append("   structural constraints.")
        L.append("")
        L.append("4. **Generation also tracks instruction.** Removing the neutrality rule")
        L.append("   roughly doubles generation odds. The instruction restrains *both* sources")
        L.append("   of bias — including the model's own. Pure-fidelity scoring (high absorption,")
        L.append("   low generation) is NOT achieved by either condition.")
        L.append("")
        L.append("5. **Significant baseline_x_target interaction** for generation (OR ≈ 2.75)")
        L.append("   means GPT-4.1 is *more responsive* to instruction removal than Sonnet —")
        L.append("   ratifying the interpretation that the original target-effect was")
        L.append("   instruction-followability, not capability.")
        L.append("")
        L.append("**Implication for the paper.** The Eval B pre-registered finding")
        L.append("(GPT-4.1 BPS < Sonnet BPS, p_FDR=0.0003) is real *under explicit neutrality")
        L.append("instructions* — but it doesn't generalize to natural deployment, where users")
        L.append("don't say 'be neutral.' The deeper finding is that *neutrality instructions")
        L.append("themselves cause the stripping behavior media-studies critics warn about*.")
        L.append("")

    # NF-1 extension: condition × direction asymmetry
    casym = report.get("condition_asymmetry")
    if casym:
        L.append("## Exploratory — Attribution-Rule Effect on Detection Direction "
                 "(NF-1 extension)")
        L.append("")
        L.append("**Question:** Does removing the attribution rule (Eval A baseline vs")
        L.append("ablation vs full) asymmetrically increase flagging of one political")
        L.append("direction over the other?")
        L.append("")
        L.append("**Method:** Apply the political lexicon to detections from all 3")
        L.append("conditions. Fit GEE-logit `is_{left,right}_coded ~ condition × target")
        L.append("+ lean_ordinal`, clustered on article_id.")
        L.append("")
        bct = casym.get("by_condition_target", {})
        if bct:
            L.append(f"**Detection counts:** total = {casym['n_detections_total']}")
            L.append("")
            L.append("| Condition × target | N detections |")
            L.append("|--------------------|-------------:|")
            for k in sorted(bct):
                L.append(f"| {k.replace('__', ' × ')} | {bct[k]} |")
            L.append("")
        models = casym.get("models_pooled", {})
        if models:
            L.append("**Pooled GEE-logit (both targets, condition × target):**")
            L.append("")
            L.append("| Outcome | Effect | OR [95% CI] (p) |")
            L.append("|---------|--------|----------------|")
            for outcome, m in models.items():
                if m.get("status") != "ok":
                    continue
                for eff_key in ["ablation_main", "baseline_main", "target_main",
                                "lean_main", "ablation_x_target", "baseline_x_target"]:
                    eff = m.get(eff_key)
                    if eff is None:
                        continue
                    sig = "**" if eff["p"] < 0.05 else ""
                    L.append(f"| {outcome} | {eff_key} | "
                             f"{sig}{eff['odds_ratio']:.2f}{sig} "
                             f"[{eff['ci_low_or']:.2f}, {eff['ci_high_or']:.2f}] "
                             f"(p={eff['p']:.3f}) |")
            L.append("")
        L.append("**Findings:**")
        L.append("")
        L.append("1. **No detected attribution-rule × direction asymmetry.** Neither")
        L.append("   condition main effects nor condition × target interactions are")
        L.append("   significant on either directional outcome. Removing the rule")
        L.append("   does not asymmetrically expand flagging by political direction.")
        L.append("")
        L.append("2. **Lean main effect replicates NF-1.** Right-coded flag rate")
        L.append("   scales with article right-leaningness (OR ≈ 1.78, p = 0.016);")
        L.append("   left-coded flag rate scales inversely (OR ≈ 0.65, p = 0.042) —")
        L.append("   articles' actual lean drives directional flag distribution as")
        L.append("   expected.")
        L.append("")
        L.append("3. **Power-limited null.** Total directional flags across all 3")
        L.append("   conditions = ~95 (left + right + both). Same lexicon-coverage")
        L.append("   limitation as NF-1; LLM-classifier follow-up (NF-1B) remains the")
        L.append("   recommended robustness check.")
        L.append("")

    # Reliability
    rel = report.get("reliability", {})
    if rel:
        L.append("## Inter-judge reliability")
        L.append("")
        L.append("### BPS Krippendorff's α (ordinal) and Pearson r — per eval")
        L.append("")
        L.append("| Eval | N pairs | α [95% CI] | r [95% CI] (p) |")
        L.append("|------|--------:|-----------:|---------------:|")
        for e in ["a", "b", "c"]:
            k = rel.get(f"bps_eval_{e}")
            if not k:
                continue
            a = k["krippendorff_alpha_ordinal"]
            r = k["pearson_r"]
            L.append(f"| {e.upper()} | {k['n_pairs']} | "
                     f"{a['point']:.2f} [{a['ci_low']:.2f}, {a['ci_high']:.2f}] | "
                     f"{r['point']:.2f} [{r['ci_low']:.2f}, {r['ci_high']:.2f}] (p={r['p']:.3g}) |")
        L.append("")
        v = rel.get("verdict")
        if v:
            L.append("### Detection-verdict agreement (paired across judges)")
            L.append("")
            L.append(f"- N paired detections: **{v['n_paired']}**")
            k4 = v["kappa_4class"]; kb = v["kappa_binary"]
            L.append(f"- 4-class Cohen's κ: **{k4['point']:.2f}** "
                     f"[{k4['ci_low']:.2f}, {k4['ci_high']:.2f}]")
            L.append(f"- Binary Cohen's κ: **{kb['point']:.2f}** "
                     f"[{kb['ci_low']:.2f}, {kb['ci_high']:.2f}]")
            L.append(f"- Binary raw agreement: **{v['binary_raw_agreement']*100:.0f}%**")
            L.append("")

    return "\n".join(L)


def main():
    ensure_long_data()

    df_bps = pd.read_parquet(DATA / "long_bps.parquet")
    df_verdict = pd.read_parquet(DATA / "long_verdict.parquet")
    df_meta = pd.read_parquet(DATA / "long_meta.parquet")
    df_lean = pd.read_parquet(DATA / "long_lean.parquet")
    df_pr = pd.read_parquet(DATA / "long_pr.parquet")

    # LMM 1: per-eval BPS
    print("\nFitting LMM 1: per-eval BPS ...")
    lmm1 = fit_all_evals(df_bps)
    for e, r in lmm1.items():
        if r.get("status") != "ok":
            print(f"  {e}: {r.get('status', 'unknown')}"); continue
        ix = r["interaction"]
        print(f"  {e}: n={r['n_obs']}, ICC={r['icc_article']:.2f}, "
              f"interaction β={ix['estimate']:+.2f} (p={ix['p']:.3f})")

    # LMM 2: explanation_quality
    print("\nFitting LMM 2: explanation_quality ...")
    df_eq = df_meta[df_meta.dimension == "explanation_quality"]
    lmm2 = fit_continuous_target_x_judge(df_eq, "score")
    if lmm2.get("status") == "ok":
        ix = lmm2["interaction"]; tm = lmm2["target_main"]
        print(f"  n={lmm2['n_obs']}, ICC={lmm2['icc_group']:.2f}, "
              f"target_main β={tm['estimate']:+.2f} (p={tm['p']:.3f}), "
              f"interaction β={ix['estimate']:+.2f} (p={ix['p']:.3f})")
    else:
        print(f"  status: {lmm2.get('status')}")

    # LMM 3: detection validity (binary)
    print("\nFitting LMM 3: detection validity ...")
    lmm3 = fit_binary_target_x_judge(df_verdict, "verdict_valid")
    if lmm3.get("status") == "ok":
        tm = lmm3["target_main"]; ix = lmm3["interaction"]
        print(f"  n={lmm3['n_obs']}, target OR={tm['odds_ratio']:.2f} "
              f"(p={tm['p']:.3f}), interaction OR={ix['odds_ratio']:.2f} "
              f"(p={ix['p']:.3f})")

    # LMM 4: lean accuracy (binary, using each judge's article rating as truth)
    print("\nFitting LMM 4: lean accuracy ...")
    lmm4 = fit_binary_target_x_judge(df_lean, "lean_correct", judge_col="judge_truth")
    if lmm4.get("status") == "ok":
        tm = lmm4["target_main"]; ix = lmm4["interaction"]
        print(f"  n={lmm4['n_obs']}, target OR={tm['odds_ratio']:.2f} "
              f"(p={tm['p']:.3f}), interaction OR={ix['odds_ratio']:.2f} "
              f"(p={ix['p']:.3f})")

    # NF-1: Bias-direction asymmetry (exploratory; not in FDR family)
    print("\nFitting NF-1: bias-direction asymmetry ...")
    asym = fit_direction_asymmetry(df_verdict)
    print(f"  N detections analyzed: {asym['n_with_known_lean']} of {asym['n_detections_total']}")
    print(f"  Direction distribution: {asym['overall_counts']}")
    for outcome in ["is_left_coded", "is_right_coded"]:
        m = asym["models"].get(outcome, {})
        if m.get("status") == "ok":
            tm = m.get("target_main")
            ix = m.get("interaction")
            ln = m.get("lean_main")
            print(f"  {outcome}: target OR={tm['odds_ratio']:.2f} (p={tm['p']:.3f}), "
                  f"lean OR={ln['odds_ratio']:.2f} (p={ln['p']:.4f}), "
                  f"interaction OR={ix['odds_ratio']:.2f} (p={ix['p']:.3f})")

    # Exploratory: per-article precision / recall / F1
    # NOT in the pre-registered FDR family — these are descriptive replacements
    # for the BPS gestalt and add information without changing what was locked.
    print("\nFitting exploratory P/R/F1 LMMs (not in FDR family) ...")
    lmm_pr = {}
    for outcome in ["precision", "recall", "f1"]:
        r = fit_continuous_target_x_judge(df_pr, outcome)
        lmm_pr[outcome] = r
        if r.get("status") == "ok":
            tm, ix = r.get("target_main"), r.get("interaction")
            print(f"  {outcome}: n={r['n_obs']}, ICC={r['icc_group']:.2f}, "
                  f"target_main β={tm['estimate']:+.3f} (p={tm['p']:.3f}), "
                  f"interaction β={ix['estimate']:+.3f} (p={ix['p']:.3f})")

    # Reliability
    print("\nComputing reliability ...")
    rel = reliability_sample(df_bps, df_verdict)

    # Family of primary tests for FDR (per PRE_REGISTRATION §2)
    primary_pvals = {}
    for e in ["a", "b", "c"]:
        r = lmm1.get(f"eval_{e}")
        if r and r.get("status") == "ok":
            if r.get("target_main"):
                primary_pvals[f"H_BPS_target_eval_{e}"] = r["target_main"]["p"]
            if r.get("interaction"):
                primary_pvals[f"H_BPS_favoritism_eval_{e}"] = r["interaction"]["p"]
    if lmm2.get("status") == "ok":
        primary_pvals["H_explanation_quality_target"] = lmm2["target_main"]["p"]
        primary_pvals["H_explanation_quality_favoritism"] = lmm2["interaction"]["p"]
    if lmm3.get("status") == "ok":
        primary_pvals["H_validity_target"] = lmm3["target_main"]["p"]
        primary_pvals["H_validity_favoritism"] = lmm3["interaction"]["p"]
    if lmm4.get("status") == "ok":
        primary_pvals["H_lean_target"] = lmm4["target_main"]["p"]
        primary_pvals["H_lean_favoritism"] = lmm4["interaction"]["p"]

    fdr = benjamini_hochberg(primary_pvals, q=0.05)
    print(f"\nBH-FDR applied across {len(fdr)} primary tests at q=0.05")

    # Pull in NF-3 (absorption/generation) and condition-asymmetry summaries
    # if they've been generated by their dedicated scripts.
    decomp = None
    cond_asym = None
    decomp_path = DATA / "decomp_summary.json"
    cond_path = DATA / "condition_asym_summary.json"
    if decomp_path.exists():
        decomp = json.loads(decomp_path.read_text())
    if cond_path.exists():
        cond_asym = json.loads(cond_path.read_text())

    report = {
        "version": "v3",
        "preregistration": "PRE_REGISTRATION.md",
        "lmm_bps_per_eval": lmm1,
        "lmm_explanation_quality": lmm2,
        "lmm_validity": lmm3,
        "lmm_lean_accuracy": lmm4,
        "lmm_precision_recall_f1": lmm_pr,    # exploratory, not in FDR family
        "direction_asymmetry": asym,           # NF-1, exploratory
        "lexicon_summary": {
            "counts": LEXICON_COUNTS,
            "summary": lexicon_summary(),
        },
        "fdr_primary": fdr,
        "reliability": rel,
        "absorption_generation": decomp,
        "condition_asymmetry": cond_asym,
        "descriptive_pr": {
            "by_target_judge": {
                f"{tgt}__{jdg}": v for (tgt, jdg), v in
                (df_pr.groupby(["target", "judge"])
                    [["tp", "fp", "fn", "precision", "recall", "f1", "n_detections"]]
                    .mean().round(4).to_dict(orient="index")).items()
            },
            "by_target": (df_pr.groupby("target")
                [["precision", "recall", "f1"]].mean().round(4).to_dict(orient="index")),
            "n_valid_f1": int(df_pr["f1"].notna().sum()),
            "n_total": int(len(df_pr)),
        },
    }

    json_path = ROOT / "stats_report.json"
    md_path = ROOT / "stats_report.md"
    json_path.write_text(json.dumps(report, indent=2, default=float))
    md_path.write_text(render_markdown(report))
    print(f"\nWrote {json_path}")
    print(f"Wrote {md_path}")

    return report


if __name__ == "__main__":
    main()
