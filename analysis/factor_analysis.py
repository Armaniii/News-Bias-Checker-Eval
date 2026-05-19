"""
Per-construct factor analysis on Eval B custom_scores (NF-11).

The 12 per-bias-type custom scores in eval-b-susceptibility/seed.yaml may
load on fewer latent factors. Common a-priori grouping:
  - Lexical:    spin, word_choice, subjective_adjectives, sensationalism
  - Structural: slant, bias_by_omission
  - Epistemic:  unsubstantiated_claims, opinion_as_fact, mind_reading
  - Other:      mudslinging, negativity_bias, elite_populist_bias

We test the data-driven structure with PCA + factor loadings, then re-fit
the per-eval LMM on factor scores rather than individual bias types.
"""

from __future__ import annotations
import json, pathlib, warnings
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA, FactorAnalysis
from sklearn.preprocessing import StandardScaler

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BAD = {"article_24346", "article_42780", "article_51657",
       "article_37862", "article_28565"}

JUDGE_SHORT = {"claude-opus-4-6": "opus", "gpt-5": "gpt5"}
TARGET_SHORT = {"claude-sonnet-4-5": "sonnet", "gpt-4.1": "gpt"}
BIAS_TYPES = ["spin", "unsubstantiated_claims", "opinion_as_fact",
    "sensationalism", "mudslinging", "mind_reading", "slant",
    "bias_by_omission", "subjective_adjectives", "word_choice",
    "negativity_bias", "elite_populist_bias"]


def load_long_scores(conditions=("baseline", "ablation", "full")) -> pd.DataFrame:
    """Returns long-format: row per (article, target, judge, condition) × 12 cols."""
    rows = []
    base = ROOT / "results" / "judgment" / "eval-b"
    for condition in conditions:
        for target_full, target_s in TARGET_SHORT.items():
            for judge_full, judge_s in JUDGE_SHORT.items():
                d = base / condition / target_full / judge_full
                if not d.exists():
                    continue
                for f in sorted(d.glob("*.json")):
                    try:
                        r = json.load(open(f))
                    except Exception:
                        continue
                    aid = r.get("article_id", "")
                    if aid in BAD:
                        continue
                    cs = r.get("custom_scores") or {}
                    if not isinstance(cs, dict):
                        continue
                    row = {"article_id": aid, "target": target_s,
                           "judge": judge_s, "condition": condition}
                    for bt in BIAS_TYPES:
                        v = cs.get(bt)
                        row[bt] = float(v) if isinstance(v, (int, float)) else np.nan
                    rows.append(row)
    return pd.DataFrame(rows)


def run_pca(df: pd.DataFrame, n_components: int = 4) -> dict:
    X = df[BIAS_TYPES].dropna()
    if len(X) < 20:
        return {"error": "insufficient data"}
    Z = StandardScaler().fit_transform(X)
    pca = PCA(n_components=n_components)
    scores = pca.fit_transform(Z)
    var_explained = pca.explained_variance_ratio_
    loadings = pca.components_
    return {
        "n_obs": int(len(X)),
        "n_components": n_components,
        "variance_explained": [float(v) for v in var_explained],
        "cumulative_variance": [float(v) for v in np.cumsum(var_explained)],
        "loadings": {  # PC[i][bias_type] = loading
            f"PC{i+1}": {bt: float(loadings[i, j])
                         for j, bt in enumerate(BIAS_TYPES)}
            for i in range(n_components)
        },
        "scores": scores,  # (N, n_components)
        "row_index": X.index.tolist(),
    }


def run_efa(df: pd.DataFrame, n_factors: int = 3) -> dict:
    """Maximum-likelihood factor analysis (rotated)."""
    X = df[BIAS_TYPES].dropna()
    if len(X) < 20:
        return {"error": "insufficient data"}
    Z = StandardScaler().fit_transform(X)
    fa = FactorAnalysis(n_components=n_factors, random_state=0, rotation="varimax")
    fa.fit(Z)
    loadings = fa.components_  # (n_factors, n_features)
    return {
        "n_obs": int(len(X)),
        "n_factors": n_factors,
        "loadings": {
            f"F{i+1}": {bt: float(loadings[i, j])
                        for j, bt in enumerate(BIAS_TYPES)}
            for i in range(n_factors)
        },
        "noise_variance": [float(v) for v in fa.noise_variance_],
    }


def factor_score_lmm(df: pd.DataFrame, pca_result: dict) -> dict:
    """Fit GEE-logit / LMM on factor scores by target × judge × condition."""
    import statsmodels.api as sm
    import statsmodels.formula.api as smf

    X = df[BIAS_TYPES].dropna()
    df_clean = df.loc[X.index].copy()
    scores = pca_result["scores"]
    out = {}
    for i in range(pca_result["n_components"]):
        df_clean[f"factor_{i+1}"] = scores[:, i]

    df_clean["target"] = pd.Categorical(df_clean["target"], categories=["sonnet", "gpt"])
    df_clean["judge"] = pd.Categorical(df_clean["judge"], categories=["opus", "gpt5"])
    df_clean["condition"] = pd.Categorical(
        df_clean["condition"], categories=["full", "ablation", "baseline"])

    for i in range(pca_result["n_components"]):
        col = f"factor_{i+1}"
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                md = smf.mixedlm(
                    f"{col} ~ C(condition) * C(target) + C(judge)",
                    data=df_clean, groups=df_clean["article_id"])
                res = md.fit(method="lbfgs", reml=False)
                _ = res.bse  # probe
            method = "lmm"
        except Exception:
            try:
                res = smf.ols(
                    f"{col} ~ C(condition) * C(target) + C(judge)",
                    data=df_clean,
                ).fit(cov_type="cluster",
                      cov_kwds={"groups": df_clean["article_id"]})
                method = "ols_cluster"
            except Exception as e:
                out[col] = {"status": "fit_failed", "error": str(e)}
                continue

        params, pvals, bse, ci = res.params, res.pvalues, res.bse, res.conf_int()

        def pull(name):
            if name not in params.index:
                return None
            return {
                "estimate": float(params[name]),
                "se": float(bse[name]),
                "ci_low": float(ci.loc[name, 0] if hasattr(ci, "loc")
                                else ci[0][list(params.index).index(name)]),
                "ci_high": float(ci.loc[name, 1] if hasattr(ci, "loc")
                                 else ci[1][list(params.index).index(name)]),
                "p": float(pvals[name]),
            }

        out[col] = {
            "method": method,
            "target_main": pull("C(target)[T.gpt]"),
            "judge_main": pull("C(judge)[T.gpt5]"),
            "ablation_main": pull("C(condition)[T.ablation]"),
            "baseline_main": pull("C(condition)[T.baseline]"),
            "ablation_x_target": pull("C(condition)[T.ablation]:C(target)[T.gpt]"),
            "baseline_x_target": pull("C(condition)[T.baseline]:C(target)[T.gpt]"),
        }
    return out


def main():
    print("=== factor_analysis.py (NF-11) ===\n")
    df = load_long_scores()
    print(f"Rows: {len(df):,}")

    # PCA
    print("\n=== PCA (4 components) ===")
    pca = run_pca(df, n_components=4)
    print(f"N: {pca['n_obs']}")
    print(f"Variance explained: {[f'{v:.1%}' for v in pca['variance_explained']]}")
    print(f"Cumulative:         {[f'{v:.1%}' for v in pca['cumulative_variance']]}")
    print("\nTop loadings per component (|loading| > 0.3):")
    for pc, loadings in pca["loadings"].items():
        srt = sorted(loadings.items(), key=lambda kv: -abs(kv[1]))
        items = [(bt, l) for bt, l in srt if abs(l) > 0.3][:6]
        print(f"  {pc}: " + ", ".join(f"{bt}={l:+.2f}" for bt, l in items))

    # EFA
    print("\n=== EFA (3 factors, varimax rotation) ===")
    efa = run_efa(df, n_factors=3)
    print(f"N: {efa['n_obs']}")
    print("\nVarimax-rotated loadings (|loading| > 0.3):")
    for f, loadings in efa["loadings"].items():
        srt = sorted(loadings.items(), key=lambda kv: -abs(kv[1]))
        items = [(bt, l) for bt, l in srt if abs(l) > 0.3][:6]
        print(f"  {f}: " + ", ".join(f"{bt}={l:+.2f}" for bt, l in items))

    # LMM on factor scores
    print("\n=== LMM on PCA factor scores ===")
    fits = factor_score_lmm(df, pca)
    for col, m in fits.items():
        if "error" in m or m.get("status") == "fit_failed":
            print(f"  {col}: {m.get('error','fit failed')}")
            continue
        tm = m.get("target_main") or {}
        ab = m.get("ablation_main") or {}
        bs = m.get("baseline_main") or {}
        print(f"  {col} ({m.get('method')}): "
              f"target β={tm.get('estimate', float('nan')):+.3f} (p={tm.get('p',1):.3f}), "
              f"abl β={ab.get('estimate', float('nan')):+.3f} (p={ab.get('p',1):.3f}), "
              f"base β={bs.get('estimate', float('nan')):+.3f} (p={bs.get('p',1):.3f})")

    out = {"pca": {k: v for k, v in pca.items() if k != "scores" and k != "row_index"},
           "efa": efa,
           "factor_lmms": fits}
    out_path = DATA / "factor_analysis.json"
    out_path.write_text(json.dumps(out, indent=2, default=float))
    print(f"\nSaved {out_path}")


if __name__ == "__main__":
    main()
