"""
Stage 1: curate 10,000 articles from PROD.db (articles + backup7) for the
expanded study. Selection optimizes for:

  1. Lean balance — equal coverage of all 5 AllSides classes (≈2K each).
  2. Detected-bias-density mix — low / moderate / high cells per lean class.
     Source: existing `analysis` field (GPT-4o detected bias instances).
     Treated as a SOFT signal only (used for stratification, not as ground
     truth — the prior pipeline used GPT-4o which is a precursor to the
     models we're evaluating).
  3. Outlet diversity — cap any single source domain at 10% per lean cell
     to avoid outlet contamination in downstream comparisons.
  4. Quality filters — content present, 500–30K chars (skip stubs and
     mega-articles), valid lean rating.
  5. Recency mix — half from `articles` (recent), half from `backup7`
     (historical). Tests temporal robustness without committing to either.
  6. URL deduplication — drop near-duplicates between the two tables
     (kept-most-recent rule).

Output: data/articles_curated.parquet with these columns
  article_id, source_table, url, source_domain, text, text_chars,
  lean_rating, lean_5class, lean_3class, lean_explanation,
  detected_count_old, detected_types_old (JSON list),
  created_at
"""

from __future__ import annotations
import argparse, json, pathlib, re, sqlite3, sys, time
from collections import defaultdict, Counter
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
DB = ROOT / "PROD.db"
OUT = DATA / "articles_curated.parquet"


def smart_parse(s):
    if not isinstance(s, str): return None
    try: return json.loads(s.replace('\\"', '"'))
    except Exception: return None


def smart_parse_text(s):
    """Parse a possibly-JSON-encoded text string."""
    if not isinstance(s, str): return s
    try:
        return json.loads(s) if s.startswith('"') else s
    except Exception:
        return s


def rating_to_5class(r: float) -> str:
    if r <= -3: return "Left"
    if r <= -1: return "Lean Left"
    if r < 1:   return "Center"
    if r < 3:   return "Lean Right"
    return "Right"


def label_to_3class(l5: str) -> str:
    if l5 in ("Left", "Lean Left"): return "LEFT"
    if l5 in ("Right", "Lean Right"): return "RIGHT"
    return "CENTER"


def extract_domain(url: str) -> str:
    """Robust domain extraction from possibly-escaped URL strings."""
    if not isinstance(url, str): return "unknown"
    u = url.strip().lower()
    if u.startswith('"') and u.endswith('"'): u = u[1:-1]
    u = u.replace("\\/", "/")
    m = re.search(r"https?://([^/]+)", u)
    if not m: return "unknown"
    host = m.group(1)
    if host.startswith("www."): host = host[4:]
    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def load_inventory() -> pd.DataFrame:
    """Read all candidates from both tables, parse fields, return DataFrame."""
    print("Reading PROD.db.articles ...")
    conn = sqlite3.connect(DB)
    rows_a = conn.execute(
        'SELECT id, url, article_org, full, analysis, "created at" '
        'FROM articles WHERE article_org IS NOT NULL '
        'AND LENGTH(article_org) > 100'
    ).fetchall()
    print(f"  articles: {len(rows_a):,}")

    print("Reading PROD.db.backup7 ...")
    rows_b = conn.execute(
        'SELECT id, url, article_org, full, analysis, "created at" '
        'FROM backup7 WHERE article_org IS NOT NULL '
        'AND LENGTH(article_org) > 100'
    ).fetchall()
    print(f"  backup7: {len(rows_b):,}")
    conn.close()

    inv = []
    for source_tag, batch in [("articles", rows_a), ("backup7", rows_b)]:
        for aid, url, art, full, analysis, created in batch:
            full_obj = smart_parse(full) or {}
            rating = full_obj.get("rating")
            try: rating = float(rating) if rating is not None else None
            except (TypeError, ValueError): rating = None
            if rating is None:
                continue  # require lean

            text = smart_parse_text(art) or ""
            if not isinstance(text, str): text = str(text)
            n_chars = len(text)
            if n_chars < 500 or n_chars > 30000:
                continue  # quality filter

            # Soft signal: existing GPT-4o bias detections
            an_obj = smart_parse(analysis)
            det_count = 0
            det_types = []
            if isinstance(an_obj, list):
                det_count = len(an_obj)
                det_types = [d.get("biasType", "") for d in an_obj
                             if isinstance(d, dict)][:10]
            elif isinstance(an_obj, dict) and "detections" in an_obj:
                dets = an_obj["detections"] or []
                det_count = len(dets)
                det_types = [d.get("biasType", "") for d in dets
                             if isinstance(d, dict)][:10]

            l5 = rating_to_5class(rating)
            inv.append({
                "article_id": int(aid),
                "source_table": source_tag,
                "url": (url or "").strip().lower().replace('\\/', '/').strip('"'),
                "source_domain": extract_domain(url),
                "text": text,
                "text_chars": n_chars,
                "lean_rating": rating,
                "lean_5class": l5,
                "lean_3class": label_to_3class(l5),
                "lean_explanation": (full_obj.get("explanation") or "")[:600],
                "detected_count_old": det_count,
                "detected_types_old_json": json.dumps(det_types),
                "created_at": created,
            })

    df = pd.DataFrame(inv)
    print(f"\nInventory after filters: {len(df):,}")
    # Dedup by URL — keep more recent (articles preferred over backup7,
    # then most recent created_at within each URL).
    df["_table_pref"] = df["source_table"].map({"articles": 0, "backup7": 1})
    df = df.sort_values(["_table_pref", "created_at"], ascending=[True, False])
    df = df.drop_duplicates(subset="url", keep="first").drop(columns="_table_pref")
    print(f"After URL deduplication: {len(df):,}")
    return df


def stratified_sample(df: pd.DataFrame, n_target: int = 10_000,
                      outlet_cap_frac: float = 0.10,
                      seed: int = 42) -> pd.DataFrame:
    """Stratify by lean × density tier × source_table; cap outlet dominance."""
    rng = pd.Series(range(len(df))).sample(frac=1, random_state=seed).index

    # Density tier from old detection count
    def density_tier(c):
        if c == 0: return "zero"
        if c < 3:  return "low"
        if c < 6:  return "moderate"
        return "high"
    df = df.copy()
    df["density_tier"] = df["detected_count_old"].apply(density_tier)

    # Target per (lean × density × source_table) cell
    leans = ["Left", "Lean Left", "Center", "Lean Right", "Right"]
    tiers = ["zero", "low", "moderate", "high"]
    sources = ["articles", "backup7"]

    n_cells = len(leans) * len(tiers) * len(sources)  # 40
    per_cell_target = max(1, n_target // n_cells)     # 250

    # First pass: take up to per_cell_target from each cell with outlet cap
    selected_idx = []
    leftover_pools = []
    for lean in leans:
        for tier in tiers:
            for src in sources:
                pool = df[(df.lean_5class == lean) &
                          (df.density_tier == tier) &
                          (df.source_table == src)].copy()
                if pool.empty:
                    continue
                pool = pool.sample(frac=1, random_state=seed)  # shuffle
                # Outlet diversity cap within cell
                domain_caps = max(1, int(per_cell_target * outlet_cap_frac))
                domain_counts = defaultdict(int)
                taken_ids = []
                for idx, row in pool.iterrows():
                    if len(taken_ids) >= per_cell_target:
                        break
                    d = row["source_domain"]
                    if domain_counts[d] >= domain_caps:
                        continue
                    taken_ids.append(idx)
                    domain_counts[d] += 1
                selected_idx.extend(taken_ids)
                leftover = pool.drop(taken_ids)
                leftover_pools.append(leftover)

    # Top up to N target from leftover pools, preserving lean balance
    if len(selected_idx) < n_target:
        leftover = pd.concat(leftover_pools, ignore_index=False) if leftover_pools \
                   else pd.DataFrame()
        if not leftover.empty:
            need = n_target - len(selected_idx)
            # Prefer under-represented lean classes
            counts = df.loc[selected_idx, "lean_5class"].value_counts().to_dict()
            leftover["_priority"] = leftover["lean_5class"].apply(
                lambda l: -counts.get(l, 0))
            leftover = leftover.sort_values(
                ["_priority"], kind="stable",
            ).head(need * 3)
            # Re-apply outlet caps globally
            global_caps = max(1, int(n_target * 0.05))
            global_counts = (df.loc[selected_idx, "source_domain"]
                             .value_counts().to_dict())
            extra = []
            for idx, row in leftover.iterrows():
                if len(extra) >= need: break
                d = row["source_domain"]
                if global_counts.get(d, 0) >= global_caps:
                    continue
                extra.append(idx)
                global_counts[d] = global_counts.get(d, 0) + 1
            selected_idx.extend(extra)

    out = df.loc[selected_idx].drop(columns=["density_tier"], errors="ignore")
    out = out.reset_index(drop=True)
    print(f"\nFinal selection: {len(out):,}")
    print(f"\nLean distribution:")
    print(out.lean_5class.value_counts().reindex(leans).fillna(0).astype(int).to_string())
    print(f"\nSource table distribution:")
    print(out.source_table.value_counts().to_string())
    print(f"\nDensity tier × lean (count):")
    out["_tier"] = out["detected_count_old"].apply(
        lambda c: "zero" if c == 0 else "low" if c < 3 else "moderate" if c < 6 else "high")
    print(pd.crosstab(out["_tier"], out["lean_5class"]).reindex(
        index=tiers, columns=leans, fill_value=0).to_string())
    out = out.drop(columns="_tier")
    print(f"\nTop 10 outlets:")
    print(out.source_domain.value_counts().head(10).to_string())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10_000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=== curate_articles.py ===")
    t0 = time.time()
    inv = load_inventory()
    print(f"\nInventory took {time.time()-t0:.1f}s")
    sample = stratified_sample(inv, n_target=args.n, seed=args.seed)
    sample.to_parquet(OUT, index=False)
    print(f"\nWrote {len(sample):,} curated articles to {OUT}")
    print(f"Total elapsed: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
