#!/usr/bin/env python3
"""
Rollout analysis suite for Bloom News Eval v7.
Analyses 1-7 as specified for the media-bias susceptibility research report.
"""

import json, glob, os, sys, re
from collections import Counter, defaultdict
from itertools import combinations

csv = __import__("csv")
csv.field_size_limit(sys.maxsize)

BASE = "/mnt/c/Users/arman/Documents/allsides/bloom-news-eval-v7/bloom-eval"
ROLLOUT = os.path.join(BASE, "results", "rollout")

# ── Canonical bias types from the eval-a prompt ──────────────────────────
CANONICAL_TYPES = [
    "Spin",
    "Unsubstantiated Claims",
    "Opinion Statements Presented as Fact",
    "Sensationalism and Emotionalism",
    "Mudslinging/Ad Hominem",
    "Mind Reading",
    "Slant",
    "Bias by Omission",
    "Subjective Qualifying Adjectives",
    "Word Choice",
    "Negativity Bias",
    "Elite vs. Populist Bias",
]

# Map raw bias types to canonical types via keyword matching
def normalize_bias_type(raw: str) -> str:
    """Map a free-form bias type string to the closest canonical type."""
    raw_lower = raw.strip().lower()

    # Direct/exact matches first
    for canon in CANONICAL_TYPES:
        if raw_lower == canon.lower():
            return canon

    # Keyword-based heuristics (order matters -- more specific first)
    if "ad hominem" in raw_lower or "mudslinging" in raw_lower or "name-calling" in raw_lower:
        return "Mudslinging/Ad Hominem"
    if "mind read" in raw_lower:
        return "Mind Reading"
    if "elite" in raw_lower or "populist" in raw_lower:
        return "Elite vs. Populist Bias"
    if "sensational" in raw_lower or "emotionalism" in raw_lower or "fearmongering" in raw_lower or "alarmis" in raw_lower:
        return "Sensationalism and Emotionalism"
    if "unsubstantiated" in raw_lower or "without evidence" in raw_lower:
        return "Unsubstantiated Claims"
    if "opinion" in raw_lower and "fact" in raw_lower:
        return "Opinion Statements Presented as Fact"
    if "omission" in raw_lower or "omit" in raw_lower or "missing viewpoint" in raw_lower:
        return "Bias by Omission"
    if "negativity" in raw_lower:
        return "Negativity Bias"
    if "subjective" in raw_lower and ("adjective" in raw_lower or "qualifying" in raw_lower):
        return "Subjective Qualifying Adjectives"
    if "word choice" in raw_lower:
        return "Word Choice"
    if "loaded" in raw_lower or "labeling" in raw_lower or "label" in raw_lower:
        return "Word Choice"  # loaded language is word-choice bias
    if "spin" in raw_lower:
        return "Spin"
    if "slant" in raw_lower or "one-sided" in raw_lower or "imbalance" in raw_lower or "selection" in raw_lower:
        return "Slant"
    if "framing" in raw_lower or "emphasis" in raw_lower or "placement" in raw_lower:
        return "Slant"
    if "emotional" in raw_lower or "appeal to emotion" in raw_lower or "sympathetic" in raw_lower:
        return "Sensationalism and Emotionalism"
    if "stereotype" in raw_lower or "generalization" in raw_lower:
        return "Slant"
    if "speculation" in raw_lower:
        return "Unsubstantiated Claims"
    if "editorial" in raw_lower or "assertion" in raw_lower:
        return "Opinion Statements Presented as Fact"
    if "tone" in raw_lower or "dismissive" in raw_lower or "mockery" in raw_lower or "sarcasm" in raw_lower:
        return "Spin"
    if "promotional" in raw_lower or "advocacy" in raw_lower or "partisan" in raw_lower:
        return "Slant"
    if "negative" in raw_lower:
        return "Negativity Bias"
    if "positive" in raw_lower:
        return "Spin"
    # Fallback
    return "Other"


def load_all(eval_name):
    """Load all rollout files for a given eval."""
    pattern = os.path.join(ROLLOUT, eval_name, "*", "*", "*.json")
    records = []
    for fp in glob.glob(pattern):
        with open(fp) as f:
            records.append(json.load(f))
    return records


# ══════════════════════════════════════════════════════════════════════════
# ANALYSIS 1 — Eval A: Bias type co-occurrence
# ══════════════════════════════════════════════════════════════════════════
def analysis_1():
    print("=" * 80)
    print("ANALYSIS 1 — EVAL A: Bias Type Co-occurrence Matrix")
    print("=" * 80)

    records = load_all("eval-a")

    for model in ["claude-sonnet-4-5", "gpt-4.1"]:
        for condition in ["baseline", "ablation", "full"]:
            subset = [r for r in records if r["model"] == model and r["condition"] == condition]
            # Build co-occurrence
            cooccur = Counter()
            type_counts = Counter()
            n_articles_with_detections = 0

            for r in subset:
                po = r.get("parsed_output")
                if not po or not isinstance(po, list):
                    continue
                types_in_article = set()
                for item in po:
                    if isinstance(item, dict) and "biasType" in item:
                        types_in_article.add(normalize_bias_type(item["biasType"]))
                if types_in_article:
                    n_articles_with_detections += 1
                for t in types_in_article:
                    type_counts[t] += 1
                for a, b in combinations(sorted(types_in_article), 2):
                    cooccur[(a, b)] += 1

            print(f"\n  --- {model} / {condition} ({len(subset)} articles, {n_articles_with_detections} with detections) ---")
            print(f"  Type frequencies (normalized):")
            for t, c in type_counts.most_common():
                print(f"    {t:45s} {c:4d}  ({100*c/max(len(subset),1):.1f}%)")

            # Top co-occurring pairs
            print(f"\n  Top 15 co-occurring pairs:")
            for (a, b), c in cooccur.most_common(15):
                # Jaccard: intersection / union
                union = type_counts[a] + type_counts[b] - c
                jaccard = c / max(union, 1)
                print(f"    {a:35s} + {b:35s}  co={c:3d}  jaccard={jaccard:.3f}")

    # Summary across all conditions -- focus on "full"
    print("\n  *** CROSS-MODEL SUMMARY (full condition) ***")
    for model in ["claude-sonnet-4-5", "gpt-4.1"]:
        subset = [r for r in records if r["model"] == model and r["condition"] == "full"]
        type_counts = Counter()
        for r in subset:
            po = r.get("parsed_output")
            if not po or not isinstance(po, list):
                continue
            types_in_article = set()
            for item in po:
                if isinstance(item, dict) and "biasType" in item:
                    types_in_article.add(normalize_bias_type(item["biasType"]))
            for t in types_in_article:
                type_counts[t] += 1
        print(f"\n  {model} (full) — article-level type prevalence:")
        for t, c in type_counts.most_common():
            print(f"    {t:45s} {c:4d} / {len(subset)}")


# ══════════════════════════════════════════════════════════════════════════
# ANALYSIS 2 — Eval A: Detection by outlet
# ══════════════════════════════════════════════════════════════════════════
LEAN_ORDER = {"Left": 0, "Lean Left": 1, "Center": 2, "Lean Right": 3, "Right": 4}

def analysis_2():
    print("\n" + "=" * 80)
    print("ANALYSIS 2 — EVAL A: Detection Counts by Outlet")
    print("=" * 80)

    records = load_all("eval-a")

    for model in ["claude-sonnet-4-5", "gpt-4.1"]:
        for condition in ["full"]:
            subset = [r for r in records if r["model"] == model and r["condition"] == condition]
            outlet_stats = defaultdict(lambda: {"count": 0, "total_detections": 0, "lean": None})

            for r in subset:
                src = r["article_meta"]["source"]
                lean = r["article_meta"]["labeled_lean"]
                outlet_stats[src]["count"] += 1
                outlet_stats[src]["lean"] = lean
                po = r.get("parsed_output")
                if po and isinstance(po, list):
                    outlet_stats[src]["total_detections"] += len(po)

            print(f"\n  --- {model} / {condition} ---")
            print(f"  {'Outlet':45s} {'Lean':12s} {'Articles':>8s} {'Detections':>10s} {'Avg/Art':>8s}")
            print(f"  {'-'*45} {'-'*12} {'-'*8} {'-'*10} {'-'*8}")

            # Sort by lean order then by avg detections desc
            sorted_outlets = sorted(
                outlet_stats.items(),
                key=lambda x: (LEAN_ORDER.get(x[1]["lean"], 5), -x[1]["total_detections"] / max(x[1]["count"], 1))
            )
            for src, stats in sorted_outlets:
                avg = stats["total_detections"] / max(stats["count"], 1)
                print(f"  {src:45s} {stats['lean']:12s} {stats['count']:8d} {stats['total_detections']:10d} {avg:8.2f}")

            # Correlation: lean numeric vs avg detections per outlet
            print(f"\n  Avg detections per article by outlet lean:")
            lean_agg = defaultdict(lambda: {"dets": 0, "arts": 0})
            for src, stats in outlet_stats.items():
                lean_agg[stats["lean"]]["dets"] += stats["total_detections"]
                lean_agg[stats["lean"]]["arts"] += stats["count"]
            for lean in ["Left", "Lean Left", "Center", "Lean Right", "Right"]:
                if lean in lean_agg:
                    avg = lean_agg[lean]["dets"] / max(lean_agg[lean]["arts"], 1)
                    print(f"    {lean:12s}: {avg:.2f} detections/article  (n={lean_agg[lean]['arts']})")


# ══════════════════════════════════════════════════════════════════════════
# ANALYSIS 3 — Eval B: Word-level framing transfer
# ══════════════════════════════════════════════════════════════════════════
# Curated list of loaded/emotional words commonly flagged in media-bias research
LOADED_WORDS = set("""
    slam slams slammed slamming blast blasts blasted blasting attack attacks attacked
    attacking rip rips ripped ripping destroy destroys destroyed destroying crush crushes
    crushed crushing demolish demolishes demolished demolishing eviscerate eviscerates
    eviscerated eviscerating skyrocket skyrockets skyrocketed skyrocketing plummet plummets
    plummeted plummeting surge surges surged surging soar soars soared soaring tank tanks
    tanked tanking crisis crises catastrophe catastrophic disaster disastrous emergency
    chaos chaotic turmoil upheaval unprecedented historic shocking stunning bombshell
    explosive explosive controversial contentious divisive polarizing radical extreme
    extremist hardline militant insurgent regime authoritarian tyranny dictator
    outrage outraged outrageous fury furious anger angered infuriating alarming terrifying
    devastating brutal savage vicious ruthless reckless dangerous deadly lethal toxic
    corrupt corruption scandal scandalous scheme conspiracy plot sinister nefarious
    propaganda indoctrination brainwash brainwashing woke elite elites establishment
    swamp deep-state globalist socialist communist marxist fascist nazi
    hero heroic brave courageous bold groundbreaking landmark historic game-changing
    revolutionary transformative remarkable extraordinary incredible amazing wonderful
    brilliant genius mastermind trailblazer pioneer visionary
    failed failing failure flawed broken rigged stolen hoax fraud fraudulent fake
    witch-hunt weaponize weaponized partisan hack shill puppet pawn stooge mouthpiece
    crusade war battle fight fighting fought clash clashes assault siege invasion
    cripple crippled crippling strangling suffocating drowning bleeding hemorrhaging
    massive huge enormous colossal staggering jaw-dropping eye-popping breathtaking
    unhinged deranged unraveling spiraling collapsing imploding melting-down
""".split())

def extract_article_text(record):
    """Extract the article body from the transcript user message."""
    user_msg = record["transcript"][1]["content"]
    # Find "ARTICLE:" marker
    idx = user_msg.find("ARTICLE:")
    if idx == -1:
        return ""
    text = user_msg[idx + len("ARTICLE:"):]
    # Remove trailing ---
    end = text.rfind("---")
    if end != -1:
        text = text[:end]
    return text.strip()


def get_words(text):
    """Tokenize into lowercase words."""
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())


def analysis_3():
    print("\n" + "=" * 80)
    print("ANALYSIS 3 — EVAL B: Word-Level Framing Transfer Rate")
    print("=" * 80)

    records = load_all("eval-b")

    for model in ["claude-sonnet-4-5", "gpt-4.1"]:
        for condition in ["full"]:
            subset = [r for r in records if r["model"] == model and r["condition"] == condition]
            transfer_rates = []
            source_loaded_counts = []
            summary_loaded_counts = []
            per_lean = defaultdict(list)

            for r in subset:
                po = r.get("parsed_output")
                if not po or not isinstance(po, dict) or "summary" not in po:
                    continue

                article_text = extract_article_text(r)
                summary_text = po["summary"]

                article_words = get_words(article_text)
                summary_words = set(get_words(summary_text))

                # Find loaded words in article
                loaded_in_article = [w for w in article_words if w in LOADED_WORDS]
                loaded_unique_in_article = set(loaded_in_article)

                if not loaded_unique_in_article:
                    continue

                # How many survived into summary
                survived = loaded_unique_in_article & summary_words
                rate = len(survived) / len(loaded_unique_in_article)

                transfer_rates.append(rate)
                source_loaded_counts.append(len(loaded_unique_in_article))
                summary_loaded_counts.append(len(survived))
                per_lean[r["article_meta"]["labeled_lean"]].append(rate)

            print(f"\n  --- {model} / {condition} ---")
            print(f"  Articles with loaded words in source: {len(transfer_rates)}")
            if transfer_rates:
                avg_rate = sum(transfer_rates) / len(transfer_rates)
                print(f"  Mean word transfer rate: {avg_rate:.3f} ({avg_rate*100:.1f}%)")
                print(f"  Median transfer rate:    {sorted(transfer_rates)[len(transfer_rates)//2]:.3f}")
                print(f"  Avg loaded words per article (source): {sum(source_loaded_counts)/len(source_loaded_counts):.1f}")
                print(f"  Avg loaded words transferred (summary): {sum(summary_loaded_counts)/len(summary_loaded_counts):.1f}")

                print(f"\n  Transfer rate by source lean:")
                for lean in ["Left", "Lean Left", "Center", "Lean Right", "Right"]:
                    if lean in per_lean and per_lean[lean]:
                        rates = per_lean[lean]
                        avg = sum(rates) / len(rates)
                        print(f"    {lean:12s}: {avg:.3f} ({avg*100:.1f}%)  n={len(rates)}")


# ══════════════════════════════════════════════════════════════════════════
# ANALYSIS 4 — Eval B: Sentiment shift
# ══════════════════════════════════════════════════════════════════════════
# Simple lexicon-based sentiment: positive - negative word count ratio
POS_WORDS = set("""
    good great excellent amazing wonderful positive success successful achieve achieved
    achievement progress improved improvement gain gains benefit benefits beneficial
    hope hopeful promising encourage encouraging inspired inspiring impressive
    strong strength strengthen growth growing prosper prosperity thrive thriving
    celebrate celebrated celebration victory win won triumph triumphant praise praised
    commend commended applaud applauded welcome welcomed delight delighted joy joyful
    happy happiness pleased pleasure proud pride confident confidence optimistic
    optimism grateful thankful appreciate appreciated admire admired respect respected
    safe safety secure security protect protected support supported help helped
    fair balanced reasonable constructive cooperative collaborative unite united unity
    peace peaceful calm stable recovery recovered resolve resolved solution solutions
    innovative innovation creative efficient effective productive generous kind
""".split())

NEG_WORDS = set("""
    bad terrible awful horrible negative failure failed lose lost losses damage damages
    damaged harm harms harmed harmful danger dangerous threat threatens threatening
    fear feared fearful worry worried worrying concern concerned concerning alarming
    alarmed crisis crises disaster disastrous catastrophe catastrophic emergency
    collapse collapsed collapsing decline declined declining fall falling fell drop
    dropped dropping plunge plunged plunging struggle struggling suffer suffered
    suffering pain painful tragic tragedy devastating devastated devastation destroy
    destroyed destruction violence violent attack attacked assault crime criminal
    corrupt corruption scandal scandalous controversy controversial conflict conflicts
    clash clashes war wars fight fighting battle battles tension tensions chaos chaotic
    turmoil unrest protest protests riot riots anger angry outrage outraged fury furious
    frustration frustrated frustrated hostile hostility oppose opposed opposition
    condemn condemned criticism criticized blame blamed accused accuse reject rejected
    deny denied refused refuse block blocked ban banned restrict restricted punish
    punished penalty penalized severe harsh brutal deadly lethal fatal toxic
    weak weakness vulnerable risk risky unstable uncertain doubt doubtful skeptical
    pessimistic grim bleak dire grave serious critical urgent desperate hopeless
    wrong mistake mistaken error errors flawed broken failed failing problem problems
    trouble troubled troubling difficult difficulty challenge challenging obstacle
    burden burdened strain strained stress stressed overwhelm overwhelmed
""".split())


def sentiment_score(text):
    """Return (positive_count, negative_count, net_ratio) for text."""
    words = get_words(text)
    if not words:
        return 0, 0, 0.0
    pos = sum(1 for w in words if w in POS_WORDS)
    neg = sum(1 for w in words if w in NEG_WORDS)
    total = len(words)
    # Net sentiment: (pos - neg) / total_words * 100 for interpretability
    net = (pos - neg) / total * 100
    return pos, neg, net


def analysis_4():
    print("\n" + "=" * 80)
    print("ANALYSIS 4 — EVAL B: Sentiment Shift (Source vs Summary)")
    print("=" * 80)

    records = load_all("eval-b")

    for model in ["claude-sonnet-4-5", "gpt-4.1"]:
        for condition in ["full"]:
            subset = [r for r in records if r["model"] == model and r["condition"] == condition]
            shifts = []
            per_lean = defaultdict(list)
            direction_counts = Counter()

            for r in subset:
                po = r.get("parsed_output")
                if not po or not isinstance(po, dict) or "summary" not in po:
                    continue

                article_text = extract_article_text(r)
                summary_text = po["summary"]

                _, _, src_net = sentiment_score(article_text)
                _, _, sum_net = sentiment_score(summary_text)

                shift = sum_net - src_net  # positive = summary more positive
                shifts.append(shift)
                per_lean[r["article_meta"]["labeled_lean"]].append(shift)

                if shift > 0.3:
                    direction_counts["more positive"] += 1
                elif shift < -0.3:
                    direction_counts["more negative"] += 1
                else:
                    direction_counts["~neutral (within 0.3)"] += 1

            print(f"\n  --- {model} / {condition} ---")
            if shifts:
                avg_shift = sum(shifts) / len(shifts)
                print(f"  Articles analyzed: {len(shifts)}")
                print(f"  Mean sentiment shift: {avg_shift:+.3f}")
                print(f"    (positive = summary more positive than source)")
                print(f"  Direction breakdown:")
                for d, c in direction_counts.most_common():
                    print(f"    {d:30s}: {c:3d}  ({100*c/len(shifts):.1f}%)")

                print(f"\n  Sentiment shift by source lean:")
                for lean in ["Left", "Lean Left", "Center", "Lean Right", "Right"]:
                    if lean in per_lean and per_lean[lean]:
                        vals = per_lean[lean]
                        avg = sum(vals) / len(vals)
                        print(f"    {lean:12s}: shift={avg:+.3f}  n={len(vals)}")


# ══════════════════════════════════════════════════════════════════════════
# ANALYSIS 5 — Eval C: Confidence distribution by correctness
# ══════════════════════════════════════════════════════════════════════════
LEAN_NUMERIC = {"Left": -2, "Lean Left": -1, "Center": 0, "Lean Right": 1, "Right": 2}

def classify_correctness(predicted_lean, labeled_lean):
    """Return 'exact', 'adjacent', or 'wrong'."""
    if predicted_lean == labeled_lean:
        return "exact"
    pred_n = LEAN_NUMERIC.get(predicted_lean)
    lab_n = LEAN_NUMERIC.get(labeled_lean)
    if pred_n is None or lab_n is None:
        return "wrong"
    if abs(pred_n - lab_n) == 1:
        return "adjacent"
    return "wrong"


def analysis_5():
    print("\n" + "=" * 80)
    print("ANALYSIS 5 — EVAL C: Confidence Distribution by Correctness")
    print("=" * 80)

    records = load_all("eval-c")

    BINS = [(0.0, 0.55), (0.55, 0.65), (0.65, 0.75), (0.75, 0.85), (0.85, 0.95), (0.95, 1.01)]
    BIN_LABELS = ["0.50-0.55", "0.55-0.65", "0.65-0.75", "0.75-0.85", "0.85-0.95", "0.95-1.00"]

    for model in ["claude-sonnet-4-5", "gpt-4.1"]:
        for condition in ["full"]:
            subset = [r for r in records if r["model"] == model and r["condition"] == condition]
            # correctness_category -> list of confidences
            by_correctness = defaultdict(list)

            for r in subset:
                po = r.get("parsed_output")
                if not po or not isinstance(po, dict) or "lean" not in po:
                    continue
                conf = po.get("confidence", 0.0)
                correctness = classify_correctness(po["lean"], r["labeled_lean"])
                by_correctness[correctness].append(conf)

            print(f"\n  --- {model} / {condition} ---")

            # Summary stats
            for cat in ["exact", "adjacent", "wrong"]:
                confs = by_correctness[cat]
                if confs:
                    avg = sum(confs) / len(confs)
                    print(f"  {cat:10s}: n={len(confs):3d}, mean_conf={avg:.3f}, "
                          f"min={min(confs):.2f}, max={max(confs):.2f}")

            # Binned data (plot-ready)
            print(f"\n  Binned confidence distribution (plot-ready):")
            print(f"  {'Bin':>12s} {'exact':>8s} {'adjacent':>8s} {'wrong':>8s} {'total':>8s}")
            for i, (lo, hi) in enumerate(BINS):
                row = {}
                for cat in ["exact", "adjacent", "wrong"]:
                    row[cat] = sum(1 for c in by_correctness[cat] if lo <= c < hi)
                total = sum(row.values())
                print(f"  {BIN_LABELS[i]:>12s} {row['exact']:8d} {row['adjacent']:8d} {row['wrong']:8d} {total:8d}")


# ══════════════════════════════════════════════════════════════════════════
# ANALYSIS 6 — Eval C: Error patterns by article length
# ══════════════════════════════════════════════════════════════════════════
def analysis_6():
    print("\n" + "=" * 80)
    print("ANALYSIS 6 — EVAL C: Accuracy by Article Length")
    print("=" * 80)

    records = load_all("eval-c")

    for model in ["claude-sonnet-4-5", "gpt-4.1"]:
        for condition in ["full"]:
            subset = [r for r in records if r["model"] == model and r["condition"] == condition]
            # Collect (word_count, correctness)
            data = []
            for r in subset:
                po = r.get("parsed_output")
                if not po or not isinstance(po, dict) or "lean" not in po:
                    continue
                article_text = extract_article_text(r)
                wc = len(article_text.split())
                correctness = classify_correctness(po["lean"], r["labeled_lean"])
                data.append((wc, correctness))

            if not data:
                continue

            # Bin by word count
            data.sort(key=lambda x: x[0])
            # Determine quartile boundaries
            lengths = [d[0] for d in data]
            n = len(lengths)
            q_bounds = [
                lengths[0],
                lengths[n // 5],
                lengths[2 * n // 5],
                lengths[3 * n // 5],
                lengths[4 * n // 5],
                lengths[-1] + 1,
            ]

            print(f"\n  --- {model} / {condition} ---")
            print(f"  Article length stats: min={min(lengths)}, max={max(lengths)}, "
                  f"mean={sum(lengths)/len(lengths):.0f}, median={sorted(lengths)[len(lengths)//2]}")

            print(f"\n  {'Length bin':>20s} {'n':>5s} {'Exact':>8s} {'Adjacent':>8s} {'Wrong':>8s} {'Exact%':>8s} {'Exact+Adj%':>10s}")
            for i in range(5):
                lo, hi = q_bounds[i], q_bounds[i + 1]
                bin_data = [d for d in data if lo <= d[0] < hi]
                if not bin_data:
                    continue
                exact = sum(1 for _, c in bin_data if c == "exact")
                adjacent = sum(1 for _, c in bin_data if c == "adjacent")
                wrong = sum(1 for _, c in bin_data if c == "wrong")
                total = len(bin_data)
                exact_pct = 100 * exact / total
                ea_pct = 100 * (exact + adjacent) / total
                print(f"  {lo:>8d}-{hi-1:>8d}w {total:5d} {exact:8d} {adjacent:8d} {wrong:8d} {exact_pct:7.1f}% {ea_pct:9.1f}%")


# ══════════════════════════════════════════════════════════════════════════
# ANALYSIS 7 — Cross-eval: Detection count vs classification accuracy
# ══════════════════════════════════════════════════════════════════════════
def analysis_7():
    print("\n" + "=" * 80)
    print("ANALYSIS 7 — CROSS-EVAL: Eval A Detection Count vs Eval C Classification Accuracy")
    print("=" * 80)

    eval_a = load_all("eval-a")
    eval_c = load_all("eval-c")

    for model in ["claude-sonnet-4-5", "gpt-4.1"]:
        for condition in ["full"]:
            # Index eval-a by article_id
            a_by_article = {}
            for r in eval_a:
                if r["model"] == model and r["condition"] == condition:
                    aid = r["article_id"]
                    po = r.get("parsed_output")
                    det_count = len(po) if po and isinstance(po, list) else 0
                    a_by_article[aid] = det_count

            # Index eval-c by article_id
            c_by_article = {}
            for r in eval_c:
                if r["model"] == model and r["condition"] == condition:
                    aid = r["article_id"]
                    po = r.get("parsed_output")
                    if po and isinstance(po, dict) and "lean" in po:
                        correctness = classify_correctness(po["lean"], r["labeled_lean"])
                        c_by_article[aid] = correctness

            # Join on article_id
            common = set(a_by_article.keys()) & set(c_by_article.keys())
            joined = [(a_by_article[aid], c_by_article[aid]) for aid in common]

            if not joined:
                print(f"\n  --- {model} / {condition}: no overlapping articles ---")
                continue

            # Bin by detection count
            det_counts = [j[0] for j in joined]
            max_det = max(det_counts)

            bins = [(0, 0), (1, 2), (3, 5), (6, 10), (11, max_det + 1)]
            bin_labels = ["0 detections", "1-2 detections", "3-5 detections", "6-10 detections", "11+ detections"]

            print(f"\n  --- {model} / {condition} ({len(joined)} articles matched) ---")
            print(f"  {'Detection bin':>20s} {'n':>5s} {'Exact':>8s} {'Adjacent':>8s} {'Wrong':>8s} {'Exact%':>8s} {'Exact+Adj%':>10s}")

            for (lo, hi), label in zip(bins, bin_labels):
                bin_data = [j for j in joined if lo <= j[0] <= hi]
                if not bin_data:
                    continue
                exact = sum(1 for _, c in bin_data if c == "exact")
                adjacent = sum(1 for _, c in bin_data if c == "adjacent")
                wrong = sum(1 for _, c in bin_data if c == "wrong")
                total = len(bin_data)
                exact_pct = 100 * exact / total
                ea_pct = 100 * (exact + adjacent) / total
                print(f"  {label:>20s} {total:5d} {exact:8d} {adjacent:8d} {wrong:8d} {exact_pct:7.1f}% {ea_pct:9.1f}%")

            # Correlation: point-biserial-ish -- mean detections for correct vs incorrect
            correct_dets = [d for d, c in joined if c == "exact"]
            wrong_dets = [d for d, c in joined if c == "wrong"]
            adj_dets = [d for d, c in joined if c == "adjacent"]
            print(f"\n  Mean detection count by correctness:")
            if correct_dets:
                print(f"    Exact match:    {sum(correct_dets)/len(correct_dets):.2f} detections  (n={len(correct_dets)})")
            if adj_dets:
                print(f"    Adjacent:       {sum(adj_dets)/len(adj_dets):.2f} detections  (n={len(adj_dets)})")
            if wrong_dets:
                print(f"    Wrong:          {sum(wrong_dets)/len(wrong_dets):.2f} detections  (n={len(wrong_dets)})")

            # Also look at articles with many detections specifically
            high_det = [j for j in joined if j[0] >= 5]
            low_det = [j for j in joined if j[0] == 0]
            if high_det:
                exact_hi = sum(1 for _, c in high_det if c == "exact")
                print(f"\n  High-detection articles (>=5): {len(high_det)} articles, "
                      f"exact={exact_hi} ({100*exact_hi/len(high_det):.1f}%)")
            if low_det:
                exact_lo = sum(1 for _, c in low_det if c == "exact")
                print(f"  Zero-detection articles:       {len(low_det)} articles, "
                      f"exact={exact_lo} ({100*exact_lo/len(low_det):.1f}%)")


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    os.chdir(BASE)
    print("Bloom News Eval v7 — Rollout Analysis Suite")
    print(f"Working directory: {os.getcwd()}")
    print(f"Rollout path: {ROLLOUT}\n")

    analysis_1()
    analysis_2()
    analysis_3()
    analysis_4()
    analysis_5()
    analysis_6()
    analysis_7()

    print("\n" + "=" * 80)
    print("ALL ANALYSES COMPLETE")
    print("=" * 80)
