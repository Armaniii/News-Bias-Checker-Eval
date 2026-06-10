"""
curate_v3_200.py — build the N=200 v3 corpus, stratified by lean x theme,
length-bounded, outlet-diversified, fully reproducible (deterministic, no RNG).

Design (locked 2026-05-21, per user spec "properly stratified by lean AND
overarching topic/theme, reasonable length"):

  * Source pool:  data/articles_enriched.parquet (10,000 articles enriched
                  with lean_5class, topic_top1, source_domain, political_flag).
  * Eligibility:  political_flag == True
                  400 <= words <= 1500   (reasonable length band)
                  topic maps to one of the 8 macro-themes below
                  lean_explanation present (for rating_json)
  * Grid:         5 lean classes x 8 macro-themes x 5 articles = 200.
                  => exactly 40 per lean, exactly 25 per theme, 5 per cell.
  * Selection:    deterministic within each cell — rank by topic_top1_score
                  desc (most confident theme assignment), tie-break by
                  closeness to the 900-word band centre, then by url.
  * Outlet cap:   <= MAX_PER_DOMAIN_PER_LEAN articles from any single domain
                  within a lean's 40; <= 1 per domain within a single 5-cell
                  where possible (diversify), relaxed only if a cell can't fill.
  * Unique id:    f"{source_table}_{article_id}" (article_id alone is NOT
                  unique across the merged articles/backup7 tables).

Output: articles_v3.csv (old one backed up to articles_v3_legacy100.csv).
        data/curate_v3_200_report.txt (stratification report).

Re-run: python3 analysis/curate_v3_200.py
"""

from __future__ import annotations
import json, pathlib, re, shutil, sys
from collections import defaultdict, Counter
import pandas as pd


def clean_text(t: str) -> str:
    """Repair scrape/JSON-encoding artifacts in the source text so the prompt
    the model sees is clean prose. The enriched pool stores many articles with
    literal JSON escaping (\\" for quotes) and scraper whitespace cruft
    (\\xa0 non-breaking spaces, tab runs). We undo both; we do NOT attempt to
    strip leading datelines/bylines (unreliable to detect — noted as a
    corpus limitation)."""
    if not isinstance(t, str):
        return ""
    # Undo JSON string-escape artifacts. Collapse double-backslashes first,
    # then loop the quote-unescape to catch nested double-encoding (\\" -> ").
    t = t.replace("\\\\", "\\")
    for _ in range(3):
        if '\\"' not in t and "\\'" not in t:
            break
        t = t.replace('\\"', '"').replace("\\'", "'")
    t = t.replace("\\/", "/").replace("\\n", "\n").replace("\\t", " ")
    # Normalize unicode whitespace.
    t = t.replace("\xa0", " ").replace("​", "").replace("­", "")
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse intra-line whitespace; preserve paragraph breaks.
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENRICHED = ROOT / "data" / "articles_enriched.parquet"
OUT_CSV = ROOT / "articles_v3.csv"
LEGACY = ROOT / "articles_v3_legacy100.csv"
REPORT = ROOT / "data" / "curate_v3_200_report.txt"

LEANS = ["Left", "Lean Left", "Center", "Lean Right", "Right"]

# topic_top1 -> overarching macro-theme. Topics not listed (science_technology,
# sports, entertainment_culture, lifestyle_other) are excluded from the grid.
MACRO = {
    "immigration": "immigration_border",
    "foreign_policy": "foreign_defense",
    "elections_politics": "elections_governance",
    "economy_taxes": "economy",
    "business_economy_nonpolitical": "economy",
    "crime_justice": "crime_justice",
    "guns": "social_culture_rights",
    "abortion": "social_culture_rights",
    "lgbtq_gender": "social_culture_rights",
    "racial_justice": "social_culture_rights",
    "climate_environment": "climate_energy",
    "healthcare": "health_education",
    "health_medicine": "health_education",
    "education": "health_education",
}
THEMES = ["immigration_border", "foreign_defense", "elections_governance",
          "economy", "crime_justice", "social_culture_rights",
          "climate_energy", "health_education"]

WORD_MIN, WORD_MAX, WORD_CENTRE = 400, 1500, 900
PER_CELL = 5                      # 5 lean x 8 theme x 5 = 200
MAX_PER_DOMAIN_PER_LEAN = 5       # outlet cap within a lean's 40 (12.5%)


def main():
    if not ENRICHED.exists():
        sys.exit(f"missing {ENRICHED} — run analysis/enrich_articles.py first")
    df = pd.read_parquet(ENRICHED)
    df["words"] = df["text"].str.split().str.len()
    df["macro"] = df["topic_top1"].map(MACRO)
    df["uid"] = df["source_table"].astype(str) + "_" + df["article_id"].astype(str)
    assert df["uid"].is_unique, "uid collision — source_table+article_id not unique"

    elig = df[
        (df["political_flag"])
        & (df["words"] >= WORD_MIN) & (df["words"] <= WORD_MAX)
        & (df["macro"].notna())
        & (df["lean_5class"].isin(LEANS))
        & (df["lean_explanation"].notna())
    ].copy()

    # Deterministic ranking key: most-confident theme first, then closeness to
    # the word-band centre, then url for a stable final tiebreak.
    elig["centre_dist"] = (elig["words"] - WORD_CENTRE).abs()
    elig = elig.sort_values(
        ["topic_top1_score", "centre_dist", "url"],
        ascending=[False, True, True],
    )

    selected = []
    deficits = []
    for lean in LEANS:
        lean_domain_count: Counter = Counter()
        for theme in THEMES:
            cell = elig[(elig["lean_5class"] == lean) & (elig["macro"] == theme)]
            picked, cell_domains = [], set()
            # Pass 1: enforce both caps (lean cap + 1-per-domain-within-cell).
            for _, r in cell.iterrows():
                if len(picked) == PER_CELL:
                    break
                dom = r["source_domain"]
                if lean_domain_count[dom] >= MAX_PER_DOMAIN_PER_LEAN:
                    continue
                if dom in cell_domains:
                    continue
                picked.append(r); cell_domains.add(dom); lean_domain_count[dom] += 1
            # Pass 2: relax the within-cell diversity rule if short.
            if len(picked) < PER_CELL:
                have = {r["uid"] for r in picked}
                for _, r in cell.iterrows():
                    if len(picked) == PER_CELL:
                        break
                    if r["uid"] in have:
                        continue
                    if lean_domain_count[r["source_domain"]] >= MAX_PER_DOMAIN_PER_LEAN:
                        continue
                    picked.append(r); lean_domain_count[r["source_domain"]] += 1
            if len(picked) < PER_CELL:
                deficits.append((lean, theme, len(picked)))
            for r in picked:
                selected.append(r)

    sel = pd.DataFrame(selected)

    def rating_json(r):
        return json.dumps({"rating": float(r["lean_rating"]),
                           "explanation": r["lean_explanation"]})

    cleaned = sel["text"].map(clean_text)
    out = pd.DataFrame({
        "id": "article_" + sel["uid"].astype(str),
        "text": cleaned,
        "title": "",                              # metadata only; never in prompts (input principle)
        "source": sel["source_domain"],
        "topic": sel["topic_top1"],               # fine-grained topic
        "macro_theme": sel["macro"],              # overarching theme (stratum)
        "topic_score": sel["topic_top1_score"].round(4),
        "words": cleaned.str.split().str.len(),
        "labeled_lean": sel["lean_5class"],
        "lean_rating": sel["lean_rating"],
        "url": sel["url"],
        "created_at": sel["created_at"],
        "source_table": sel["source_table"],
        "political_flag": sel["political_flag"],
        "analysis_json": sel["detected_types_old_json"].fillna("[]"),
        "rating_json": sel.apply(rating_json, axis=1),
    })

    # Back up the legacy roster (never delete) before overwriting.
    if OUT_CSV.exists() and not LEGACY.exists():
        shutil.copy2(OUT_CSV, LEGACY)
    out.to_csv(OUT_CSV, index=False)

    # ---- Stratification report -------------------------------------------
    lines = []
    lines.append(f"N = {len(out)} (target 200)")
    lines.append(f"eligible pool = {len(elig)}")
    lines.append("")
    lines.append("lean x macro-theme matrix (selected):")
    ct = pd.crosstab(out["labeled_lean"], out["macro_theme"]).reindex(LEANS)[THEMES]
    lines.append(ct.fillna(0).astype(int).to_string())
    lines.append("")
    lines.append(f"per-lean totals: {out['labeled_lean'].value_counts().reindex(LEANS).to_dict()}")
    lines.append(f"per-theme totals: {out['macro_theme'].value_counts().reindex(THEMES).to_dict()}")
    lines.append("")
    lines.append(f"distinct source domains: {out['source'].nunique()}")
    lines.append(f"top domains: {Counter(out['source']).most_common(8)}")
    lines.append(f"max articles from one domain in a lean: "
                 f"{max(Counter(zip(out['labeled_lean'], out['source'])).values())}")
    lines.append("")
    lines.append(f"word length: min {out['words'].min()} med {int(out['words'].median())} "
                 f"max {out['words'].max()}")
    lines.append(f"lean_rating: min {out['lean_rating'].min():.1f} "
                 f"med {out['lean_rating'].median():.1f} max {out['lean_rating'].max():.1f}")
    lines.append(f"source_table split: {out['source_table'].value_counts().to_dict()}")
    if deficits:
        lines.append("")
        lines.append(f"UNFILLED CELLS (lean, theme, got): {deficits}")
    else:
        lines.append("")
        lines.append("all 40 cells filled to target (5 each).")

    report = "\n".join(lines)
    REPORT.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nwrote {OUT_CSV}  (legacy backed up to {LEGACY.name})")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
