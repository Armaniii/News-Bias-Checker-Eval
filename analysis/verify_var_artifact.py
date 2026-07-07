"""Deterministic verification of the pilot VAR artifact claim (paper §4.1):
~47% of the pilot judge's 'inheriting' verdicts cite quoted terms that do
not appear anywhere in the source article.

No AI judgment in the loop: regex quote-extraction + lowercase substring
matching only. Run: python3 analysis/verify_var_artifact.py
Expected output: 549/1175 = 46.7% ALL_TERMS_ABSENT_FROM_SOURCE.
"""
import csv, json, re, sys, pathlib
csv.field_size_limit(10_000_000)
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT/"analysis"))
import paper1_config as cfg

v2 = {r["id"]: (r.get("text_clean") or r.get("text") or "").lower()
      for r in csv.DictReader(open(ROOT/"articles_v2.csv", encoding="utf-8"))}
Q = re.compile(r"[‘'\"“]([^’'\"”]{3,60})[’'\"”]")
from collections import Counter
c, inh_total = Counter(), 0
for line in open(cfg.DATA/"voice_adoption.cache.jsonl", encoding="utf-8"):
    r = json.loads(line)
    if r.get("judge_family") != "anthropic" or r.get("article_id") not in v2:
        continue
    p = r.get("parsed") or {}
    if p.get("voice") != "inheriting":
        continue
    inh_total += 1
    quoted = [q.strip().lower() for q in Q.findall(p.get("reason") or "")]
    if not quoted:
        c["no_quoted_terms"] += 1; continue
    missing = [q for q in quoted if q not in v2[r["article_id"]]]
    c["ALL_TERMS_ABSENT_FROM_SOURCE" if len(missing)==len(quoted)
      else ("SOME_ABSENT" if missing else "all_present")] += 1
n_quote = inh_total - c["no_quoted_terms"]
print(f"inheriting verdicts: {inh_total}; with quoted terms: {n_quote}")
for k, v in c.most_common(): print(f"  {k}: {v}")
aa = c["ALL_TERMS_ABSENT_FROM_SOURCE"]
print(f"RATE: {aa}/{n_quote} = {aa/n_quote:.1%}")
