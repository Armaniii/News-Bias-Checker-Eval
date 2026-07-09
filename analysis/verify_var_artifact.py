"""Deterministic verification of the pilot VAR artifact claim (paper §4.1):
a large share of the pilot judge's 'inheriting' verdicts cite quoted terms
that do not appear anywhere in the source article.

No AI judgment in the loop: regex quote-extraction + lowercase substring
matching only. Run: python3 analysis/verify_var_artifact.py

v2 (2026-07-08), after two defects were found by adversarial review of v1:
  1. Quote regex treated the straight apostrophe as a quote delimiter, so
     possessives/contractions in the judge's own prose minted phantom
     "quoted terms". Fixed: straight single quotes now require word
     boundaries; curly quotes are unambiguous and unchanged. A side effect
     of the fix: spans containing internal apostrophes are no longer
     extractable (conservative; they leave the sample).
  2. The six identity-contaminated pilot articles (paper1_config.
     STAGE1_CONTAMINATED_ARTICLES, PRE_REGISTRATION §6.8.9: excluded from
     all Stage-1-derived analyses) were not excluded; on those articles the
     source text is the wrong story, so absent quotes are corpus error,
     not judge error.
The script prints a sensitivity table over both corrections. v1 reported
549/1175 = 46.7% (both defects present).

Residual limitation (documented, not fixed): matching runs against the
current full cleaned source text, not the as-judged input (which was
truncated at 4,000 chars and predates two hygiene passes). The truncation
direction is generous to the judge — terms beyond the truncation point
count as 'present' though the judge never saw them.
"""
import csv, json, re, sys, pathlib
csv.field_size_limit(10_000_000)
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT/"analysis"))
import paper1_config as cfg

v2 = {r["id"]: (r.get("text_clean") or r.get("text") or "").lower()
      for r in csv.DictReader(open(ROOT/"articles_v2.csv", encoding="utf-8"))}

Q_V1 = re.compile(r"[‘'\"“]([^’'\"”]{3,60})[’'\"”]")        # buggy (kept for the sensitivity row)
Q_V2 = re.compile(                                            # boundary-aware
    r"‘([^’]{3,60})’"
    r"|“([^”]{3,60})”"
    r'|"([^"]{3,60})"'
    r"|(?<!\w)'([^']{3,60})'(?!\w)")

def classify(reason, src, rx):
    quoted = [g.strip().lower() for m in rx.finditer(reason or "")
              for g in m.groups() if g]
    if not quoted:
        return "no_quoted_terms"
    missing = [q for q in quoted if q not in src]
    if len(missing) == len(quoted): return "ALL_ABSENT"
    return "SOME_ABSENT" if missing else "all_present"

rows = []
for line in open(cfg.DATA/"voice_adoption.cache.jsonl", encoding="utf-8"):
    r = json.loads(line)
    if r.get("judge_family") != "anthropic" or r.get("article_id") not in v2:
        continue
    p = r.get("parsed") or {}
    if p.get("voice") == "inheriting":
        rows.append((r["article_id"], p.get("reason") or ""))

print(f"inheriting verdicts (pilot, Sonnet judge): {len(rows)}")
print(f"{'condition':<38}{'ALL_ABSENT':>11}{'with quotes':>12}{'rate':>8}")
for label, rx, excl in [
        ("v1: buggy regex, no exclusion",  Q_V1, False),
        ("regex fixed only",               Q_V2, False),
        ("exclusion only",                 Q_V1, True),
        ("v2: regex fixed + exclusion",    Q_V2, True)]:
    kept = [(a, reason) for a, reason in rows
            if not (excl and a in cfg.STAGE1_CONTAMINATED_ARTICLES)]
    c = {}
    for a, reason in kept:
        k = classify(reason, v2[a], rx)
        c[k] = c.get(k, 0) + 1
    nq = len(kept) - c.get("no_quoted_terms", 0)
    aa = c.get("ALL_ABSENT", 0)
    print(f"{label:<38}{aa:>11}{nq:>12}{aa/nq:>8.1%}")
