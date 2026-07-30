#!/usr/bin/env python3
"""bench_source_traceability.py — a deterministic reliability benchmark for
LLM judges: does a judge's cited quoted evidence actually appear in the source?

MOTIVATION. When an LLM judge justifies a verdict by quoting phrases
("...the source calls it 'X'..."), a minimal reliability requirement is that
those phrases exist in the source. A judge that cites phrases absent from the
source is fabricating evidence — a failure that is checkable with NO human
ground truth and NO second model, by regex quote-extraction + substring
matching. This generalizes the pilot check (analysis/verify_var_artifact.py)
into a scorer that ranks ANY set of judge verdicts.

METRIC (per judge). Over verdicts whose reason cites >=1 quoted phrase:
  - fabrication_rate : fraction where NONE of the cited quotes appear in the
                       source (all-absent) — lower is better.
  - quote_untraceable: fraction of individual cited quotes absent from source.
Both are deterministic and reproducible (boundary-aware quote regex; lowercase
substring match; contaminated pilot articles excluded per PRE_REG 6.8.9).

USAGE (scores every judge present in one or more verdict caches):
  python3 analysis/bench_source_traceability.py \
      --caches data/voice_adoption.cache.jsonl data/voice_adoption.ext.cache.jsonl
Each cache row must have: article_id, judge, parsed.reason (free text).
Add a new judge to the leaderboard simply by pointing at its verdict cache.
"""
import argparse, csv, json, re, sys, pathlib
from collections import defaultdict
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "analysis"))
csv.field_size_limit(10**7)
import paper1_config as cfg

# boundary-aware quote extraction (v2: straight ' requires word boundaries so
# possessives/contractions in the judge's prose do not mint phantom quotes).
Q = re.compile(r"‘([^’]{3,60})’"     # ' ... '
               r"|“([^”]{3,60})”"     # " ... "
               r'|"([^"]{3,60})"'                    # " ... "
               r"|(?<!\w)'([^']{3,60})'(?!\w)")      # ' ... ' (boundary-safe)


def load_sources():
    src = {}
    for corpus in ("articles_v2.csv", "articles_v3.csv"):
        p = ROOT / corpus
        if not p.exists():
            continue
        for r in csv.DictReader(open(p, encoding="utf-8")):
            src.setdefault(r["id"], (r.get("text_clean") or r.get("text") or "").lower())
    return src


def score(caches):
    src = load_sources()
    stat = defaultdict(lambda: {"verdicts": 0, "fabricated": 0,
                                "quotes": 0, "quotes_absent": 0})
    for cache in caches:
        cp = pathlib.Path(cache)
        if not cp.exists():
            print(f"  (skip missing {cache})"); continue
        for line in open(cp, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            aid = r.get("article_id")
            if aid in cfg.STAGE1_CONTAMINATED_ARTICLES or aid not in src:
                continue                      # excluded / unknown source
            p = r.get("parsed")
            reason = p.get("reason") if isinstance(p, dict) else None
            if not reason:
                continue
            quotes = [g.strip().lower() for m in Q.finditer(reason)
                      for g in m.groups() if g]
            if not quotes:
                continue                      # not scorable (cites no quotes)
            judge = cfg.JUDGE_FAMILY.get(r.get("judge"), r.get("judge_family", "?"))
            s = stat[judge]
            s["verdicts"] += 1
            absent = [q for q in quotes if q not in src[aid]]
            s["quotes"] += len(quotes)
            s["quotes_absent"] += len(absent)
            if len(absent) == len(quotes):
                s["fabricated"] += 1
    return stat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--caches", nargs="+", required=True,
                    help="verdict cache jsonl file(s); rows need article_id, judge, parsed.reason")
    args = ap.parse_args()
    stat = score(args.caches)
    print(f"\n{'='*72}\nSOURCE-TRACEABILITY OF JUDGE-CITED EVIDENCE (lower = better)\n{'='*72}")
    print(f"{'judge family':14s}{'scorable':>10}{'fabricat.':>11}{'quote-untrace.':>16}")
    for judge in sorted(stat, key=lambda j: stat[j]["fabricated"] / max(stat[j]["verdicts"], 1)):
        s = stat[judge]
        fab = s["fabricated"] / max(s["verdicts"], 1)
        unt = s["quotes_absent"] / max(s["quotes"], 1)
        print(f"{judge:14s}{s['verdicts']:>10}{fab:>10.1%}{unt:>15.1%}")
    print("\nfabrication_rate = verdicts where EVERY cited quote is absent from the source.")
    print("quote-untraceable = share of individual cited quotes absent from the source.")


if __name__ == "__main__":
    main()
