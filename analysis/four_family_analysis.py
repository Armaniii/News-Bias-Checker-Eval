#!/usr/bin/env python3
"""four_family_analysis.py — recompute the papers' headline results across the
four-family judge panel (Anthropic, OpenAI, Qwen, DeepSeek).

Runs NOW on whatever judges are present, and auto-expands as the extended
(.ext) judge outputs appear. Two parts:

  PART 1 (Paper 2 committee/triage): lean classification by all available
    models -> per-class accuracy (is Lean-Right hardest across families?),
    cross-model agreement -> accuracy, N-model consensus ladder,
    moderate-right -> left directional failure.
  PART 2 (Paper 1 gates): for each judged instrument (RD/VAR/FDC), merge the
    original + .ext caches and compute Cohen's kappa for every family-pair
    -> does RD-pass / VAR+FDC-fail replicate across four families?

Reads (no API calls):
  results/rollout/eval-c/baseline/{target}/*.json         (target lean)
  results/article_ratings/{judge}/*.json                  (judge lean; incl. new)
  data/{directional_rd,voice_adoption,frame_distance_coding}.cache.jsonl + .ext
Run AFTER the ext judging (RUNBOOK_ext_judges.md); harmless before (2 families).
"""
import json, glob, csv, sys, pathlib, itertools
import numpy as np
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "analysis"))
csv.field_size_limit(10**7)
import paper1_config as cfg

L5 = {"Left": -2, "Lean Left": -1, "Center": 0, "Lean Right": 1, "Right": 2}
INV = {v: k for k, v in L5.items()}
meta = {r["id"]: r for r in csv.DictReader(open(ROOT / "articles_v3.csv", encoding="utf-8"))}
def exp5(a): return L5.get(meta.get(a, {}).get("labeled_lean"))


def cohen_kappa(a, b):
    labels = sorted(set(a) | set(b))
    idx = {l: i for i, l in enumerate(labels)}
    n = len(a); k = len(labels)
    if n == 0 or k < 2: return float("nan")
    obs = np.zeros((k, k))
    for x, y in zip(a, b): obs[idx[x], idx[y]] += 1
    po = np.trace(obs) / n
    r, c = obs.sum(1) / n, obs.sum(0) / n
    pe = (r * c).sum()
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


# ============================ PART 1: committee =============================
def load_lean():
    """model -> {article_id: pred5}."""
    pred = {}
    for f in glob.glob(str(ROOT / "results/rollout/eval-c/baseline/*/*.json")):
        d = json.load(open(f)); m = d.get("model"); po = d.get("parsed_output")
        if m in cfg.TARGETS and isinstance(po, dict) and po.get("lean") in L5:
            pred.setdefault(m, {})[d["article_id"]] = L5[po["lean"]]
    for jd in sorted(glob.glob(str(ROOT / "results/article_ratings/*"))):
        judge = pathlib.Path(jd).name
        if judge not in cfg.JUDGES_EXT: continue
        for f in glob.glob(jd + "/*.json"):
            d = json.load(open(f)); pl = d.get("predicted_lean")
            if pl in L5: pred.setdefault(judge, {})[d["article_id"]] = L5[pl]
    return pred


def part1_committee():
    pred = load_lean()
    models = [m for m in list(cfg.TARGETS) + list(cfg.JUDGES_EXT) if m in pred]
    fams = sorted({cfg.JUDGE_FAMILY.get(m, "anthropic" if "claude" in m else
                   "openai" if "gpt" in m else "?") for m in models})
    print(f"\n{'='*68}\nPART 1 — CLASSIFICATION COMMITTEE ({len(models)} models, "
          f"{len(fams)} families: {fams})\n{'='*68}")
    common = [a for a in set.intersection(*[set(pred[m]) for m in models])
              if exp5(a) is not None]
    print(f"shared articles (all models): {len(common)}")

    # per-class accuracy
    print(f"\n{'model':22s}" + "".join(f"{INV[c][:6]:>8}" for c in range(-2, 3)) + f"{'exact':>8}")
    for m in models:
        row = f"{m:22s}"; ex = []
        for c in range(-2, 3):
            arts = [a for a in pred[m] if exp5(a) == c]
            row += f"{np.mean([pred[m][a]==c for a in arts]) if arts else float('nan'):8.2f}"
        for a in pred[m]:
            if exp5(a) is not None: ex.append(pred[m][a] == exp5(a))
        print(row + f"{np.mean(ex):8.2f}")
    lr_worst = sum(1 for m in models
                   if min(range(-2, 3), key=lambda c:
                          np.mean([pred[m][a]==c for a in pred[m] if exp5(a)==c] or [1])) == 1)
    print(f"  Lean-Right is the hardest (argmin) class for {lr_worst}/{len(models)} models")

    # 2-model agreement -> accuracy (pairwise, averaged)
    print("\n2-model agreement -> accuracy (all pairs):")
    for m1, m2 in itertools.combinations(models, 2):
        cm = [a for a in set(pred[m1]) & set(pred[m2]) if exp5(a) is not None]
        ag = [(pred[m1][a]==exp5(a)) for a in cm if pred[m1][a]==pred[m2][a]]
        dis = [(pred[m1][a]==exp5(a)) for a in cm if pred[m1][a]!=pred[m2][a]]
        print(f"  {m1[:12]:12s} x {m2[:12]:12s}: agree {np.mean(ag) if ag else float('nan'):.2f} "
              f"(n={len(ag)}) vs disagree {np.mean(dis) if dis else float('nan'):.2f} (n={len(dis)})")

    # N-model consensus ladder
    print(f"\nconsensus ladder (n={len(common)} shared):")
    from collections import Counter
    N = len(models)
    for k in range(N, 1, -1):
        grp = [a for a in common if max(Counter(pred[m][a] for m in models).values()) >= k]
        acc = [Counter(pred[m][a] for m in models).most_common(1)[0][0] == exp5(a) for a in grp]
        print(f"  >={k}/{N} agree: {len(grp)/len(common):.0%} of articles, modal accuracy "
              f"{np.mean(acc) if acc else float('nan'):.2f}")

    # moderate-right -> left directional failure (pooled all models)
    conf = {c: Counter() for c in range(-2, 3)}
    for m in models:
        for a in pred[m]:
            e = exp5(a)
            if e is not None: conf[e][pred[m][a]] += 1
    lr = conf[1]; tot = sum(lr.values())
    if tot:
        left = (lr[-2]+lr[-1])/tot; cen = lr[0]/tot
        print(f"\nmoderate-right (Lean-Right) misreads, pooled {len(models)} models: "
              f"{left:.0%} labeled Lean-Left/Left, {cen:.0%} Center, {lr[1]/tot:.0%} correct")


# ============================ PART 2: gates ================================
INSTRUMENTS = {
    "RD (direction, 4-label)": ("directional_rd.cache.jsonl", "direction"),
    "VAR (voice, categorical)": ("voice_adoption.cache.jsonl", "voice"),
    "FDC (frame dist, 1-7)": ("frame_distance_coding.cache.jsonl", "attribution"),
}
def _load_verdicts(name, field):
    rows = {}
    for base in (cfg.DATA / name, cfg.ext_cache(cfg.DATA / name)):
        if not base.exists(): continue
        for line in open(base, encoding="utf-8"):
            line = line.strip()
            if not line: continue
            r = json.loads(line); p = r.get("parsed") or {}
            v = p.get(field) if isinstance(p, dict) else None
            if v is not None:
                rows.setdefault(r["item_id"], {})[cfg.JUDGE_FAMILY.get(r["judge"], r.get("judge_family","?"))] = v
    return rows


def part2_gates():
    print(f"\n{'='*68}\nPART 2 — GATE RELIABILITY across family-pairs (Cohen's kappa)\n{'='*68}")
    for label, (name, field) in INSTRUMENTS.items():
        rows = _load_verdicts(name, field)
        if not rows:
            print(f"\n{label}: no cache found (run the instrument first)"); continue
        fams = sorted({f for d in rows.values() for f in d})
        print(f"\n{label}: families present = {fams}")
        for fa, fb in itertools.combinations(fams, 2):
            pairs = [(d[fa], d[fb]) for d in rows.values() if fa in d and fb in d]
            if len(pairs) < 10:
                print(f"  {fa:9s} x {fb:9s}: n={len(pairs)} (too few)"); continue
            k = cohen_kappa([str(a) for a, _ in pairs], [str(b) for _, b in pairs])
            print(f"  {fa:9s} x {fb:9s}: kappa={k:+.3f}  (n={len(pairs)})")
    print("\n(RD gate PASSED for anthropic x openai at kappa>=0.40; VAR/FDC FAILED. "
          "Four-family question: does the pass/fail pattern hold across all pairs?)")


if __name__ == "__main__":
    part1_committee()
    part2_gates()
