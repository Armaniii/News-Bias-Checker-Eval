"""
Stage 2: enrich curated articles with topic labels.

Approach: sentence-transformer cosine-similarity to topic prototypes.
Why: zero-shot NLI on CPU is impractically slow (~50 sec/article for
DistilBart-MNLI, hours for the larger DeBERTa). MiniLM-L6 sentence
transformer at 22M params runs at 100–300 articles/sec on CPU and is
empirically competitive for coarse topic classification.

For each article:
  1. Embed first 1024 chars (stays within MiniLM's 512-token context).
  2. Compute cosine similarity to mean embedding of each topic's
     prototype sentences.
  3. Assign top-1 topic and cache full ranking.

Reads:  data/articles_curated.parquet  (from curate_articles.py)
Writes: data/articles_enriched.parquet  (curated + topic columns)
"""

from __future__ import annotations
import json, pathlib, time
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
IN  = DATA / "articles_curated.parquet"
OUT = DATA / "articles_enriched.parquet"

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Topic taxonomy + prototype sentences. Each topic has 3-5 prototype phrases
# anchoring its embedding centroid. Adding more prototypes per topic is the
# primary tuning lever for accuracy.
TOPIC_PROTOTYPES = {
    # ============== POLITICAL ISSUES ==============
    "immigration": [
        "Immigration policy and border security at the United States southern border.",
        "Asylum seekers, refugees, and undocumented immigrants in U.S. policy debates.",
        "ICE deportation, sanctuary cities, and immigration enforcement.",
        "DACA, Dreamers, and pathway to citizenship legislation.",
    ],
    "abortion": [
        "Abortion rights, reproductive freedom, and pro-choice advocacy.",
        "Pro-life movement, abortion restrictions, and protecting the unborn.",
        "Roe v. Wade, Dobbs decision, and state abortion laws.",
        "Reproductive healthcare access and clinic regulations.",
    ],
    "guns": [
        "Gun control legislation, assault weapons bans, and firearm regulation.",
        "Second amendment rights, gun owners, and the right to bear arms.",
        "Mass shootings, school shootings, and gun violence prevention.",
        "Concealed carry, background checks, and red flag laws.",
    ],
    "climate_environment": [
        "Climate change, global warming, and carbon emissions.",
        "Renewable energy, fossil fuels, and the energy transition.",
        "Environmental protection, clean air and water regulations.",
        "Climate policy, the Paris Agreement, and environmental justice.",
    ],
    "healthcare": [
        "Healthcare reform, Medicare, Medicaid, and the Affordable Care Act.",
        "Drug prices, prescription medications, and pharmaceutical companies.",
        "Universal healthcare, single-payer systems, and Medicare for All.",
        "Hospital systems, health insurance, and patient access.",
    ],
    "economy_taxes": [
        "Tax policy, federal taxes, and tax cuts or increases.",
        "Inflation, economic growth, GDP, and the federal reserve.",
        "Job market, unemployment, wages, and labor statistics.",
        "Federal budget, government spending, and the national debt.",
    ],
    "racial_justice": [
        "Racial justice, civil rights, and systemic racism.",
        "Black Lives Matter, police reform, and racial equity.",
        "Affirmative action, diversity equity inclusion, and racial discrimination.",
        "Voting rights, racial gerrymandering, and minority political representation.",
    ],
    "foreign_policy": [
        "Foreign policy, international relations, and diplomatic affairs.",
        "Wars and conflicts in Ukraine, Russia, Israel, Gaza, or the Middle East.",
        "China relations, trade with foreign countries, and global geopolitics.",
        "U.S. military operations and defense policy abroad.",
    ],
    "lgbtq_gender": [
        "LGBTQ rights, transgender issues, and gender identity.",
        "Same-sex marriage, gay rights, and pride.",
        "Gender-affirming care, transgender athletes, and pronoun policies.",
        "Sexuality education, parental rights, and gender ideology.",
    ],
    "education": [
        "Public school education, curriculum, and school district policy.",
        "School choice, charter schools, and education vouchers.",
        "Critical race theory, parental rights in education, and book bans.",
        "Universities, higher education, college tuition, and student debt.",
    ],
    "crime_justice": [
        "Crime, criminal justice reform, and sentencing.",
        "Police brutality, police accountability, and law enforcement.",
        "Mass incarceration, prison reform, and parole policy.",
        "Defund the police, public safety, and crime statistics.",
    ],
    "elections_politics": [
        "U.S. elections, presidential campaigns, and voting.",
        "Congress, federal legislation, and political parties.",
        "State governor races, ballot initiatives, and election results.",
        "Political polling, voter turnout, and campaign finance.",
    ],
    # ============== NON-POLITICAL ==============
    "business_economy_nonpolitical": [
        "Stock market, corporate earnings, and business news.",
        "Tech companies, mergers, and acquisitions in the private sector.",
        "Consumer products, retail, and product launches.",
        "Banking, finance, and personal finance advice.",
    ],
    "sports": [
        "Sports games, scores, and athletic competitions.",
        "NFL, NBA, MLB, NHL teams, players, and leagues.",
        "Olympics, championships, and tournaments.",
        "Athlete trades, contracts, and locker room news.",
    ],
    "entertainment_culture": [
        "Movies, films, and the film industry.",
        "Music, albums, concerts, and musical artists.",
        "Television shows, streaming, and pop culture.",
        "Celebrity news, awards shows, and entertainment industry.",
    ],
    "science_technology": [
        "Scientific research, discoveries, and academic studies.",
        "Space exploration, NASA, and astronomy.",
        "Artificial intelligence, machine learning, and emerging technology.",
        "Biology, physics, chemistry, and laboratory science.",
    ],
    "health_medicine": [
        "Medical research, disease, and treatments.",
        "Public health, vaccines, and disease outbreaks.",
        "Mental health, wellness, and psychological wellbeing.",
        "Diet, nutrition, and lifestyle health advice.",
    ],
    "lifestyle_other": [
        "Travel, tourism, and vacation destinations.",
        "Food, cooking, recipes, and restaurants.",
        "Fashion, beauty, home, and personal lifestyle.",
        "Weather, local events, and community happenings.",
    ],
}

POLITICAL_TOPICS = {
    "immigration", "abortion", "guns", "climate_environment", "healthcare",
    "economy_taxes", "racial_justice", "foreign_policy", "lgbtq_gender",
    "education", "crime_justice", "elections_politics",
}


def build_topic_centroids(model):
    """Returns (topic_names, centroid_matrix [T x D])."""
    print(f"Embedding topic prototypes ...")
    names, all_protos = [], []
    spans = []
    for name, protos in TOPIC_PROTOTYPES.items():
        names.append(name)
        spans.append((len(all_protos), len(all_protos) + len(protos)))
        all_protos.extend(protos)
    embeddings = model.encode(all_protos, convert_to_numpy=True,
                              normalize_embeddings=True, show_progress_bar=False)
    centroids = np.zeros((len(names), embeddings.shape[1]), dtype=np.float32)
    for i, (lo, hi) in enumerate(spans):
        c = embeddings[lo:hi].mean(axis=0)
        c = c / (np.linalg.norm(c) + 1e-9)
        centroids[i] = c
    print(f"  {len(names)} topic centroids built (dim={embeddings.shape[1]})")
    return names, centroids


def main():
    print("=== enrich_articles.py (sentence-transformer prototype matching) ===")
    if not IN.exists():
        raise SystemExit(f"Missing input: {IN}. Run curate_articles.py first.")
    df = pd.read_parquet(IN)
    print(f"Loaded {len(df):,} curated articles from {IN}")

    print(f"Loading embedding model: {EMBED_MODEL}")
    t0 = time.time()
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBED_MODEL, device="cpu")
    print(f"  loaded in {time.time()-t0:.1f}s")

    topic_names, centroids = build_topic_centroids(model)

    # Use first 1024 chars (~256 tokens) — fits inside MiniLM's 512-token window
    # comfortably and captures lead-bias which is where most stance information
    # is concentrated.
    print(f"\nEmbedding {len(df):,} articles ...")
    texts = df["text"].fillna("").str.slice(0, 1024).tolist()
    t0 = time.time()
    article_embs = model.encode(
        texts, batch_size=64, convert_to_numpy=True,
        normalize_embeddings=True, show_progress_bar=True,
    )
    elapsed = time.time() - t0
    rate = len(texts) / elapsed if elapsed > 0 else 0
    print(f"  embedded in {elapsed:.1f}s ({rate:.0f} articles/s)")

    print(f"\nComputing cosine similarity to topic centroids ...")
    sims = article_embs @ centroids.T  # [N x T], normalized → cosine
    top1_idx = sims.argmax(axis=1)
    top1_score = sims[np.arange(len(df)), top1_idx]

    # Top-3
    top3_idx = np.argsort(-sims, axis=1)[:, :3]
    top3_scores = -np.sort(-sims, axis=1)[:, :3]
    top3_json = [
        json.dumps([(topic_names[top3_idx[i, j]], float(top3_scores[i, j]))
                    for j in range(3)])
        for i in range(len(df))
    ]

    df = df.copy()
    df["topic_top1"] = [topic_names[i] for i in top1_idx]
    df["topic_top1_score"] = top1_score.astype(float)
    df["topic_top3_json"] = top3_json
    df["political_flag"] = df["topic_top1"].isin(POLITICAL_TOPICS)

    df.to_parquet(OUT, index=False)
    print(f"\nWrote {len(df):,} enriched rows to {OUT}\n")

    # Quick summary
    print("=== Topic distribution ===")
    print(df["topic_top1"].value_counts().to_string())
    print(f"\nPolitical articles: {df['political_flag'].sum():,} "
          f"({df['political_flag'].mean()*100:.1f}%)")

    print("\n=== Topic × lean (political only) ===")
    pol = df[df.political_flag]
    print(pd.crosstab(pol["topic_top1"], pol["lean_5class"]).reindex(
        columns=["Left", "Lean Left", "Center", "Lean Right", "Right"],
        fill_value=0).to_string())


if __name__ == "__main__":
    main()
