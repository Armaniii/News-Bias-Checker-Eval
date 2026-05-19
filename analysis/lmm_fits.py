"""
Phase 4 (pilot) — Per-eval BPS model: bps ~ target * judge with article-level
clustering.

Strategy:
  1. Try linear mixed model with random intercept by article_id (LMM).
  2. If LMM fit is singular (variance component on boundary), fall back to OLS
     with cluster-robust standard errors clustered on article_id. This is the
     standard recommendation when ICC ~= 0; mixed model and cluster-robust OLS
     give identical fixed-effect estimates in the limit, but cluster-robust SEs
     don't blow up.

Each model tests:
  * Main effect of target: is GPT-4.1's BPS different from Sonnet's?
  * Main effect of judge:  harshness asymmetry between Opus and GPT-5.
  * target × judge interaction: family favoritism — the headline claim
    that currently appears as an unsupported "p<0.01" in
    inter_judge_agreement.md:49.
"""

from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats


def _icc_from_lmm(result) -> float:
    """ICC = sigma^2_group / (sigma^2_group + sigma^2_residual)."""
    var_re = float(result.cov_re.iloc[0, 0]) if hasattr(result.cov_re, "iloc") \
             else float(np.asarray(result.cov_re).item())
    var_resid = float(result.scale)
    if var_re + var_resid == 0:
        return float("nan")
    return var_re / (var_re + var_resid)


def fit_lmm_bps_per_eval(df_bps: pd.DataFrame, eval_letter: str) -> dict:
    """
    Fit: bps ~ C(target) * C(judge), groups=article_id.

    Coding:
      target: 'sonnet' (ref) vs 'gpt'
      judge:  'opus'   (ref) vs 'gpt5'

    Returns a dict with main effects, interaction, ICC, and a paired-t-test
    sanity check on judge-averaged data.
    """
    sub = df_bps[df_bps["eval"] == eval_letter].copy()
    if len(sub) == 0:
        return {"eval": eval_letter, "status": "no_data"}

    sub["target"] = pd.Categorical(sub["target"], categories=["sonnet", "gpt"])
    sub["judge"]  = pd.Categorical(sub["judge"],  categories=["opus", "gpt5"])

    out = {
        "eval": eval_letter,
        "n_obs": int(len(sub)),
        "n_articles": int(sub["article_id"].nunique()),
    }

    res = None
    method_used = None

    # Try LMM first
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            md = smf.mixedlm(
                "bps ~ C(target) * C(judge)",
                data=sub, groups=sub["article_id"],
            )
            res = md.fit(method="lbfgs", reml=False)
            # Probing res.bse triggers Hessian inversion — if it raises,
            # the LMM is singular and we should fall back.
            _ = res.bse
            _ = res.conf_int()
            method_used = "lmm_random_intercept"
            out["model"] = "bps ~ C(target) * C(judge) + (1|article_id), MLE"
            out["icc_article"] = _icc_from_lmm(res)
            try:
                out["var_article"] = float(res.cov_re.iloc[0, 0])
            except Exception:
                out["var_article"] = float(np.asarray(res.cov_re).item())
            out["var_residual"] = float(res.scale)
            out["converged"] = bool(res.converged)
        except Exception as e:
            out["lmm_fallback_reason"] = f"{type(e).__name__}: {e}"
            res = None

    # Fallback: OLS with cluster-robust SEs (ICC ~= 0 → equivalent to LMM)
    if res is None:
        try:
            res = smf.ols("bps ~ C(target) * C(judge)", data=sub).fit(
                cov_type="cluster", cov_kwds={"groups": sub["article_id"]},
            )
            method_used = "ols_cluster_robust"
            out["model"] = "bps ~ C(target) * C(judge), OLS + cluster-robust SE on article_id"
            out["icc_article"] = 0.0  # By construction, no random effect was fittable
            out["r_squared"] = float(res.rsquared)
        except Exception as e:
            out["status"] = "fit_failed"
            out["error"] = str(e)
            return out

    out["method"] = method_used

    # Pull contrasts (works for both LMM and OLS)
    params = res.params; pvals = res.pvalues; bse = res.bse; ci = res.conf_int()

    def pull(name):
        if name not in params.index:
            return None
        return {
            "estimate": float(params[name]),
            "se": float(bse[name]),
            "ci_low": float(ci.loc[name, 0]),
            "ci_high": float(ci.loc[name, 1]),
            "p": float(pvals[name]),
        }

    out["target_main"] = pull("C(target)[T.gpt]")
    out["judge_main"]  = pull("C(judge)[T.gpt5]")
    out["interaction"] = pull("C(target)[T.gpt]:C(judge)[T.gpt5]")

    # Marginal target effect (averaged across judges) — useful for sanity-check
    # against paired t-test on judge-averaged BPS.
    if out["target_main"] is not None and out["interaction"] is not None:
        marg_est = out["target_main"]["estimate"] + 0.5 * out["interaction"]["estimate"]
        out["target_marginal_estimate"] = float(marg_est)

    # Sanity check: paired t-test on judge-averaged BPS, target effect only
    avg = sub.groupby(["article_id", "target"])["bps"].mean().unstack()
    if avg.shape[1] == 2 and avg.dropna().shape[0] > 5:
        paired = avg.dropna()
        t, p = stats.ttest_rel(paired["gpt"], paired["sonnet"])
        out["sanity_paired_t_target"] = {
            "n_pairs": int(paired.shape[0]),
            "mean_diff_gpt_minus_sonnet": float((paired["gpt"] - paired["sonnet"]).mean()),
            "t": float(t), "p": float(p),
        }

    out["status"] = "ok"
    return out


def fit_all_evals(df_bps: pd.DataFrame) -> dict:
    return {f"eval_{e}": fit_lmm_bps_per_eval(df_bps, e) for e in ["a", "b", "c"]}


def fit_continuous_target_x_judge(df: pd.DataFrame, outcome_col: str,
                                   group_col: str = "article_id") -> dict:
    """
    Generic fitter for `outcome ~ target * judge + (1|group)` on continuous data.
    Reuses the LMM-with-OLS-fallback pattern. Used for explanation_quality (LMM 2)
    and any other continuous meta-judgment dimension.

    Both `target` and `judge` columns must be present and limited to two levels.
    """
    sub = df.copy()
    sub["target"] = pd.Categorical(sub["target"], categories=["sonnet", "gpt"])
    sub["judge"]  = pd.Categorical(sub["judge"],  categories=["opus", "gpt5"])
    sub = sub.dropna(subset=[outcome_col, "target", "judge", group_col])

    out = {
        "outcome": outcome_col,
        "n_obs": int(len(sub)),
        "n_groups": int(sub[group_col].nunique()),
    }

    formula = f"{outcome_col} ~ C(target) * C(judge)"
    res = None
    method_used = None

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            md = smf.mixedlm(formula, data=sub, groups=sub[group_col])
            res = md.fit(method="lbfgs", reml=False)
            _ = res.bse; _ = res.conf_int()
            method_used = "lmm_random_intercept"
            out["model"] = f"{formula} + (1|{group_col}), MLE"
            out["icc_group"] = _icc_from_lmm(res)
            try:
                out["var_group"] = float(res.cov_re.iloc[0, 0])
            except Exception:
                out["var_group"] = float(np.asarray(res.cov_re).item())
            out["var_residual"] = float(res.scale)
            out["converged"] = bool(res.converged)
        except Exception as e:
            out["lmm_fallback_reason"] = f"{type(e).__name__}: {e}"
            res = None

    if res is None:
        try:
            res = smf.ols(formula, data=sub).fit(
                cov_type="cluster", cov_kwds={"groups": sub[group_col]},
            )
            method_used = "ols_cluster_robust"
            out["model"] = f"{formula}, OLS + cluster-robust SE on {group_col}"
            out["icc_group"] = 0.0
            out["r_squared"] = float(res.rsquared)
        except Exception as e:
            out["status"] = "fit_failed"
            out["error"] = str(e)
            return out

    out["method"] = method_used
    params, pvals, bse, ci = res.params, res.pvalues, res.bse, res.conf_int()

    def pull(name):
        if name not in params.index:
            return None
        return {
            "estimate": float(params[name]),
            "se": float(bse[name]),
            "ci_low": float(ci.loc[name, 0]),
            "ci_high": float(ci.loc[name, 1]),
            "p": float(pvals[name]),
        }

    out["target_main"] = pull("C(target)[T.gpt]")
    out["judge_main"]  = pull("C(judge)[T.gpt5]")
    out["interaction"] = pull("C(target)[T.gpt]:C(judge)[T.gpt5]")
    if out["target_main"] and out["interaction"]:
        out["target_marginal_estimate"] = float(
            out["target_main"]["estimate"] + 0.5 * out["interaction"]["estimate"]
        )

    # Sanity check
    avg = sub.groupby([group_col, "target"])[outcome_col].mean().unstack()
    if avg.shape[1] == 2 and avg.dropna().shape[0] > 5:
        paired = avg.dropna()
        t, p = stats.ttest_rel(paired["gpt"], paired["sonnet"])
        out["sanity_paired_t_target"] = {
            "n_pairs": int(paired.shape[0]),
            "mean_diff_gpt_minus_sonnet": float((paired["gpt"] - paired["sonnet"]).mean()),
            "t": float(t), "p": float(p),
        }

    out["status"] = "ok"
    return out


def fit_direction_asymmetry(df_verdict: pd.DataFrame) -> dict:
    """
    NF-1 — Bias-direction asymmetry analysis.

    For each detection: outcome ∈ {0, 1} for is_left_coded and is_right_coded.
    Two GEE-logit models per target (one per outcome) with article_lean
    (5-class, ordered) as a control.

    Also produces descriptive cell counts and per-target asymmetry summaries.

    Hypothesis tested:
        H_asym_target × article_lean: target_main on the directional-flag
        outcome quantifies whether one target flags directional language at
        a different rate than the other, controlling for article lean.
    """
    import statsmodels.api as sm

    out = {
        "n_detections_total": int(len(df_verdict)),
        "n_with_known_lean": int(df_verdict["article_lean_opus"].isin(
            ["Left", "Lean Left", "Center", "Lean Right", "Right"]).sum()),
    }

    # Restrict to detections with known article lean
    df = df_verdict[df_verdict["article_lean_opus"].isin(
        ["Left", "Lean Left", "Center", "Lean Right", "Right"])].copy()
    df["article_lean_opus"] = pd.Categorical(
        df["article_lean_opus"],
        categories=["Left", "Lean Left", "Center", "Lean Right", "Right"], ordered=True)
    # Ordinal encoding for use as numeric covariate
    LEAN_ORD = {"Left": -2, "Lean Left": -1, "Center": 0, "Lean Right": +1, "Right": +2}
    df["lean_ordinal"] = df["article_lean_opus"].astype(str).map(LEAN_ORD)
    df["target"] = pd.Categorical(df["target"], categories=["sonnet", "gpt"])

    # Descriptive: mean is_left and is_right by (target, article_lean_opus)
    desc = (df.groupby(["target", "article_lean_opus"], observed=False)
              [["is_left_coded", "is_right_coded"]].mean().round(4))
    out["descriptive_by_target_lean"] = {
        f"{tgt}__{lean}": v for (tgt, lean), v in desc.to_dict(orient="index").items()
    }

    # Counts of flagged directions
    out["overall_counts"] = df.flagged_direction.value_counts().to_dict()
    out["by_target_counts"] = (df.groupby(["target", "flagged_direction"],
                                          observed=False).size()
                                 .unstack(fill_value=0).to_dict(orient="index"))

    # GEE-logit: is_left_coded ~ target * lean_ordinal + (cluster: article)
    # And the same for is_right_coded.
    out["models"] = {}
    for outcome in ["is_left_coded", "is_right_coded"]:
        sub = df.dropna(subset=[outcome, "target", "lean_ordinal", "article_id"])
        if len(sub) < 10:
            out["models"][outcome] = {"status": "insufficient_data", "n": len(sub)}
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                gee = smf.gee(f"{outcome} ~ C(target) * lean_ordinal", "article_id",
                              data=sub, family=sm.families.Binomial(),
                              cov_struct=sm.cov_struct.Exchangeable())
                res = gee.fit()
            params, pvals, bse, ci = res.params, res.pvalues, res.bse, res.conf_int()

            def pull(name):
                if name not in params.index:
                    return None
                return {
                    "log_odds": float(params[name]),
                    "odds_ratio": float(np.exp(params[name])),
                    "se": float(bse[name]),
                    "ci_low_or": float(np.exp(ci.loc[name, 0])),
                    "ci_high_or": float(np.exp(ci.loc[name, 1])),
                    "p": float(pvals[name]),
                }

            out["models"][outcome] = {
                "status": "ok",
                "n_obs": int(len(sub)),
                "n_articles": int(sub["article_id"].nunique()),
                "intercept": pull("Intercept"),
                "target_main":  pull("C(target)[T.gpt]"),
                "lean_main":    pull("lean_ordinal"),
                "interaction":  pull("C(target)[T.gpt]:lean_ordinal"),
                "model": f"{outcome} ~ C(target) * lean_ordinal, GEE logit + exchangeable on article_id",
            }
        except Exception as e:
            out["models"][outcome] = {"status": "fit_failed", "error": str(e)}

    return out


def fit_binary_target_x_judge(df: pd.DataFrame, outcome_col: str,
                               group_col: str = "article_id",
                               judge_col: str = "judge") -> dict:
    """
    Logistic regression with cluster-robust SE for binary outcomes.
    Used for verdict_valid (LMM 3) and lean_correct (LMM 4).

    `judge_col` is parameterized so LMM 4 can use 'judge_truth' instead of 'judge'.
    """
    sub = df.copy()
    sub["target"] = pd.Categorical(sub["target"], categories=["sonnet", "gpt"])
    sub[judge_col] = pd.Categorical(sub[judge_col], categories=["opus", "gpt5"])
    sub = sub.dropna(subset=[outcome_col, "target", judge_col, group_col])

    import statsmodels.api as sm

    formula = f"{outcome_col} ~ C(target) * C({judge_col})"
    out = {
        "outcome": outcome_col,
        "n_obs": int(len(sub)),
        "n_groups": int(sub[group_col].nunique()),
        "model": f"{formula}, GEE logit + exchangeable correlation on {group_col}",
        "method": "gee_logit_exchangeable",
    }

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gee = smf.gee(formula, group_col, data=sub,
                          family=sm.families.Binomial(),
                          cov_struct=sm.cov_struct.Exchangeable())
            res = gee.fit()
    except Exception as e:
        out["status"] = "fit_failed"
        out["error"] = str(e)
        return out

    params, pvals, bse, ci = res.params, res.pvalues, res.bse, res.conf_int()

    def pull(name):
        if name not in params.index:
            return None
        return {
            "log_odds": float(params[name]),
            "odds_ratio": float(np.exp(params[name])),
            "se": float(bse[name]),
            "ci_low_log": float(ci.loc[name, 0]),
            "ci_high_log": float(ci.loc[name, 1]),
            "ci_low_or": float(np.exp(ci.loc[name, 0])),
            "ci_high_or": float(np.exp(ci.loc[name, 1])),
            "p": float(pvals[name]),
        }

    out["target_main"] = pull("C(target)[T.gpt]")
    out["judge_main"]  = pull(f"C({judge_col})[T.gpt5]")
    out["interaction"] = pull(f"C(target)[T.gpt]:C({judge_col})[T.gpt5]")
    out["status"] = "ok"
    return out
