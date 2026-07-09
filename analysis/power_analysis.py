"""Power/precision table for the three confirmatory tests (registered
deliverable, PRE_REGISTRATION §6.6.11).

COMPUTED POST HOC (2026-07-08, after Stage-2 collection) and labeled as
such: the deliverable was not produced before collection, a deviation
found and logged during panel review. Inputs are the observed Stage-2
dispersion estimates; H26's pre-collection simulation (registration
§6.8.11: 77-95% at the anchored sensitivity estimate) is reproduced as
the registered row.

Output: data/power_analysis.csv
"""
import json, csv, pathlib, sys
import numpy as np
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT/"analysis"))

res = json.load(open(ROOT/"data"/"hypotheses_stage2.json"))
rng = np.random.default_rng(7)
N_SIM = 20_000
rows = []

# ---- H28: TOST power (paired diffs; sd back-derived from the CI90) ----
h28 = res["H28"]
n = h28["n_pairs"]
se = (h28["ci90"][1] - h28["ci90"][0]) / (2 * 1.645)
sd = se * np.sqrt(n)
tcrit = stats.t.ppf(0.95, n - 1)
for bound in (2.0, 1.0):
    for true in (0.0, h28["mean_diff"]):
        d = rng.normal(true, sd, size=(N_SIM, n))
        m, s = d.mean(1), d.std(1, ddof=1) / np.sqrt(n)
        rej = ((m - (-bound)) / s > tcrit) & ((bound - m) / s > tcrit)
        rows.append(dict(test="H28_TOST", parameter=f"bound=±{bound}",
                         true_effect=true, n=n, power=round(rej.mean(), 3),
                         method="simulation (normal, sd from observed CI90)",
                         post_hoc=True))

# ---- H29: probability the kappa CI lower bound clears the 0.85 floor ----
h29 = res["H29"]
se29 = (h29["ci95"][1] - h29["ci95"][0]) / (2 * 1.96)
for true_k in (h29["kappa"], 0.88, 0.86):
    p = 1 - stats.norm.cdf((0.85 + 1.96 * se29 - true_k) / se29)
    rows.append(dict(test="H29_interval", parameter="CI lower ≥ 0.85",
                     true_effect=true_k, n=h29["n_pairs"],
                     power=round(float(p), 3),
                     method="normal approx, se from article-clustered bootstrap CI",
                     post_hoc=True))

# ---- H26: registered pre-collection simulation + post-hoc MDD ----
rows.append(dict(test="H26_directional", parameter="pooled one-sided, α=.05",
                 true_effect="asymmetry ratio 2.0-2.7 (anchored sensitivity)",
                 n="80+80 articles", power="0.77-0.95",
                 method="registration §6.8.11 simulation (pre-collection)",
                 post_hoc=False))
h26 = res["H26"]["pooled"]
# per-article rate dispersion implied by the t statistic
se26 = h26["asymmetry"] / h26["t"]
mdd = round((stats.norm.ppf(0.95) + stats.norm.ppf(0.80)) * se26, 4)
rows.append(dict(test="H26_directional", parameter="MDD at 80% power",
                 true_effect=f"observed +{h26['asymmetry']:.4f}",
                 n="80+80 articles", power=f"MDD={mdd:+.4f}",
                 method="normal approx, se from observed t",
                 post_hoc=True))

out = ROOT/"data"/"power_analysis.csv"
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print(f"wrote {out}")
for r in rows:
    print(f"  {r['test']:<16} {r['parameter']:<22} true={r['true_effect']}"
          f"  power={r['power']}")
