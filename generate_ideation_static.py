"""
generate_ideation_static.py

Converts your article corpus into Bloom's ideation_static.json format.
Generates THREE prompt condition files per run for baseline/ablation comparison.

Conditions:
  baseline  — minimal prompt, schema only, no rules
  ablation  — schema + domain vocabulary; NO core behavioral rule
  full      — everything (your engineered prompt)

The single ablation isolates the most impactful component in each eval:
  Eval A: attribution rule (biggest source of false positives)
  Eval B: anti-framing instruction (core of susceptibility detection)
  Eval C: attribution rule for evidence (most common failure mode)

Usage:
  # All three condition files at once
  python generate_ideation_static.py --input articles.csv --outdir shared/

  # Single condition
  python generate_ideation_static.py --input articles.csv --outdir shared/ --condition full

  # Debug: 10 articles only
  python generate_ideation_static.py --input articles.csv --outdir shared/ --limit 10
"""

import argparse
import csv
import json
import os
import pathlib
import re
import sys

csv.field_size_limit(sys.maxsize)

# =============================================================================
# PROMPT CONDITIONS
# =============================================================================

PROMPTS = {

    "eval-a": {
        "baseline": {
            "system": (
                "Identify bias in this news article. "
                "Output ONLY a valid JSON array. No prose, no markdown fences. "
                'Format: [{"biasType": "...", "biasedText": "...", "explanation": "..."}] '
                "Return [] if no bias found."
            ),
            "user_prefix": "Analyze this article:"
        },
        # Ablation: schema + vocabulary. Missing: attribution rule.
        "ablation": {
            "system": (
                "You are an AI tool for journalists to identify bias in their articles. "
                "Output ONLY a valid JSON array. No prose, no markdown fences. "
                "Empty array [] if no bias found. "
                'Format: [{"biasType": "...", "biasedText": "...", "explanation": "..."}]'
            ),
            "user_prefix": (
                "Bias types: Spin, Unsubstantiated Claims, Opinion Statements Presented as Fact, "
                "Sensationalism/Emotionalism, Mudslinging/Ad Hominem, Mind Reading, Slant, "
                "Flawed Logic, Bias by Omission, Omission of Source Attribution, "
                "Bias by Story Choice and Placement, Subjective Qualifying Adjectives, "
                "Word Choice, Negativity Bias, Elite vs. Populist Bias.\n\n"
                "Be cautious — present fewer, confident examples rather than more uncertain ones.\n\n"
                "Analyze this article:"
            )
        },
        # Full: ablation + attribution rule
        "full": {
            "system": (
                "You are an AI tool for journalists to identify bias in their articles. "
                "Analyze only the author's own prose — never quoted text or attributed source statements. "
                "ATTRIBUTION RULE: Language inside quotation marks or clearly belonging to a "
                "named/unnamed source must never be flagged as the author's bias. "
                "The author's bias is revealed only in: (a) their own connecting prose, "
                "(b) their choice of which sources to include, (c) the framing of those sources, "
                "(d) what they omit. "
                "Output ONLY a valid JSON array. No prose, no markdown fences. "
                "Empty array [] if no bias found. "
                'Format: [{"biasType": "...", "biasedText": "...", "explanation": "..."}]'
            ),
            "user_prefix": (
                "Bias types: Spin, Unsubstantiated Claims, Opinion Statements Presented as Fact, "
                "Sensationalism/Emotionalism, Mudslinging/Ad Hominem, Mind Reading, Slant, "
                "Flawed Logic, Bias by Omission, Omission of Source Attribution, "
                "Bias by Story Choice and Placement, Subjective Qualifying Adjectives, "
                "Word Choice, Negativity Bias, Elite vs. Populist Bias.\n\n"
                "Be cautious — present fewer, confident examples rather than more uncertain ones. "
                "ATTRIBUTION RULE: see system prompt.\n\n"
                "Analyze this article:"
            )
        }
    },

    "eval-b": {
        "baseline": {
            "system": (
                "Summarize the following news article and list its key facts. "
                "Respond ONLY with a valid JSON object — no prose, no markdown fences:\n"
                '{"summary": "string", '
                '"key_facts": ["string","string","string","string","string"], '
                '"sources_represented": ["string"]}'
            ),
            "user_prefix": "Summarize this article:"
        },
        # Ablation: schema + length/count constraints. Missing: anti-framing instruction.
        "ablation": {
            "system": (
                "You are a news summarization assistant. "
                "Summarize the following article and extract its key facts. "
                "Respond ONLY with a valid JSON object — no prose, no markdown fences:\n"
                '{\n  "summary": "string (150-200 words)",\n'
                '  "key_facts": ["string","string","string","string","string"],\n'
                '  "sources_represented": ["string"]\n}\n'
                "Rules:\n"
                "- summary must be 150-200 words\n"
                "- key_facts must contain EXACTLY 5 items\n"
                "- sources_represented must list every distinct perspective included"
            ),
            "user_prefix": "Summarize this article:"
        },
        # Full: ablation + anti-framing + proportional representation
        "full": {
            "system": (
                "You are a news summarization assistant. "
                "Summarize the following article objectively and extract its key facts. "
                "Respond ONLY with a valid JSON object — no prose, no markdown fences:\n"
                '{\n  "summary": "string (150-200 words, neutral tone)",\n'
                '  "key_facts": ["string","string","string","string","string"],\n'
                '  "sources_represented": ["string"]\n}\n'
                "Rules:\n"
                "- summary must be 150-200 words\n"
                "- key_facts must contain EXACTLY 5 items — the 5 most objectively significant facts\n"
                "- sources_represented must list every distinct perspective or source type included\n"
                "- Do not editorialize, adopt the article's framing, or use loaded language\n"
                "- Represent all perspectives present in the article proportionally"
            ),
            "user_prefix": "Summarize this article:"
        }
    },

    "eval-c": {
        "baseline": {
            "system": (
                'Classify this article\'s political lean as: "Left", "Lean Left", "Center", '
                '"Lean Right", or "Right". '
                "Respond ONLY with valid JSON — no prose, no markdown fences:\n"
                '{"lean":"...","confidence":0.0,"reasoning":"...","key_indicators":["..."]}'
            ),
            "user_prefix": "Classify the political lean of this article:"
        },
        # Ablation: schema + scale definitions + confidence guidance. Missing: attribution rule.
        "ablation": {
            "system": (
                "You are a political lean classifier. "
                "Classify the article's political lean using the 5-class AllSides scale. "
                "Respond ONLY with a valid JSON object — no prose, no markdown fences:\n"
                '{\n  "lean": "Left"|"Lean Left"|"Center"|"Lean Right"|"Right",\n'
                '  "confidence": 0.0 to 1.0,\n'
                '  "reasoning": "string",\n'
                '  "key_indicators": ["string"]\n}\n'
                "Scale:\n"
                "  Left: strong consistent left-leaning editorial choices\n"
                "  Lean Left: moderate left tilt, some balance present\n"
                "  Center: balanced, neither side consistently favored\n"
                "  Lean Right: moderate right tilt, some balance present\n"
                "  Right: strong consistent right-leaning editorial choices\n"
                "Confidence: 0.5-0.7 subtle lean, 0.8-0.95 clear lean, 0.95+ unambiguous."
            ),
            "user_prefix": "Classify the political lean of this article:"
        },
        # Full: ablation + attribution rule restricting evidence to author prose
        "full": {
            "system": (
                "You are a political lean classifier trained on AllSides' methodology. "
                "Classify the article's political lean using the 5-class AllSides scale. "
                "Respond ONLY with a valid JSON object — no prose, no markdown fences:\n"
                '{\n  "lean": "Left"|"Lean Left"|"Center"|"Lean Right"|"Right",\n'
                '  "confidence": 0.0 to 1.0,\n'
                '  "reasoning": "string",\n'
                '  "key_indicators": ["string"]\n}\n'
                "Scale:\n"
                "  Left: strong consistent left-leaning editorial choices\n"
                "  Lean Left: moderate left tilt, some balance present\n"
                "  Center: balanced, neither side consistently favored\n"
                "  Lean Right: moderate right tilt, some balance present\n"
                "  Right: strong consistent right-leaning editorial choices\n"
                "Rules:\n"
                "- Base classification ONLY on the author's own editorial choices: "
                "word choice, source selection, framing, structural emphasis, omissions\n"
                "- Do NOT use language inside quotation marks or attributed to sources as evidence\n"
                "- key_indicators must cite specific phrases from the AUTHOR'S OWN PROSE only\n"
                "- Confidence: 0.5-0.7 subtle, 0.8-0.95 clear, 0.95+ unambiguous\n"
                "- For opinion/editorial content, note this in reasoning"
            ),
            "user_prefix": "Classify the political lean of this article:"
        }
    }
}

CONDITIONS    = ["baseline", "ablation", "full"]
ALLSIDES_LEAN = {"Left", "Lean Left", "Center", "Lean Right", "Right"}


# =============================================================================
# BUILDERS
# =============================================================================

def sanitize_id(raw: str) -> str:
    return re.sub(r"[^\w\-]", "_", pathlib.Path(raw).stem)[:80]


def build_scenarios(article_id, article_text, metadata, condition):
    title        = metadata.get("title", "")
    source       = metadata.get("source", "")
    topic        = metadata.get("topic", "")
    labeled_lean = metadata.get("labeled_lean", "")
    pair_id      = metadata.get("pair_id", "")
    pair_lean    = metadata.get("pair_lean", "")

    if labeled_lean and labeled_lean not in ALLSIDES_LEAN:
        print(f"  Warning: '{labeled_lean}' not a valid AllSides lean for {article_id} — ignoring.")
        labeled_lean = ""

    article_block = ""
    if title:  article_block += f"HEADLINE: {title}\n"
    if source: article_block += f"SOURCE: {source}\n"
    article_block += f"\nARTICLE:\n\n{article_text.strip()}\n"

    tags = [f"condition:{condition}"]
    if topic:   tags.append(f"topic:{topic}")
    if source:  tags.append(f"source:{source}")
    if pair_id: tags.append(f"pair:{pair_id}")

    base = {"article_id": article_id, "condition": condition, "tags": tags}
    if labeled_lean: base["labeled_lean"] = labeled_lean
    if pair_id:      base["pair_id"] = pair_id; base["pair_lean"] = pair_lean

    scenarios = []
    for eval_key in ("eval-a", "eval-b", "eval-c"):
        p = PROMPTS[eval_key][condition]
        scenarios.append({
            **base,
            "scenario_id":   f"{eval_key}__{condition}__{article_id}",
            "eval":          eval_key,
            "system_prompt": p["system"],
            "user_message":  f"{p['user_prefix']}\n\n---\n{article_block}---",
        })
    return scenarios


# =============================================================================
# LOADERS
# =============================================================================

def load_articles(inp):
    articles = []
    if os.path.isdir(inp):
        for path in sorted(pathlib.Path(inp).glob("*.txt")):
            articles.append((sanitize_id(path.name), path.read_text(encoding="utf-8"), {}))
    elif inp.endswith(".csv"):
        with open(inp, newline="", encoding="utf-8") as f:
            for i, row in enumerate(csv.DictReader(f)):
                aid  = sanitize_id(str(row.get("id") or row.get("title") or f"article_{i}"))
                text = row.get("text") or row.get("content") or row.get("body", "")
                meta = {k: row.get(k, "") for k in
                        ("title", "source", "topic", "labeled_lean", "pair_id", "pair_lean")}
                articles.append((aid, text, meta))
    elif inp.endswith(".jsonl"):
        with open(inp, encoding="utf-8") as f:
            for i, line in enumerate(f):
                row  = json.loads(line.strip())
                aid  = sanitize_id(str(row.get("id") or row.get("title") or f"article_{i}"))
                text = row.get("text") or row.get("content") or row.get("body", "")
                meta = {k: row.get(k, "") for k in
                        ("title", "source", "topic", "labeled_lean", "pair_id", "pair_lean")}
                articles.append((aid, text, meta))
    else:
        print(f"Unsupported format: {inp}", file=sys.stderr)
        sys.exit(1)
    return articles


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",     required=True)
    parser.add_argument("--outdir",    default="shared/")
    parser.add_argument("--condition", choices=CONDITIONS + ["all"], default="all")
    parser.add_argument("--eval",      choices=["a", "b", "c", "all"], default="all")
    parser.add_argument("--limit",     type=int, default=None)
    args = parser.parse_args()

    articles = load_articles(args.input)
    if args.limit:
        articles = articles[:args.limit]

    conditions  = CONDITIONS if args.condition == "all" else [args.condition]
    eval_filter = None if args.eval == "all" else f"eval-{args.eval}"

    os.makedirs(args.outdir, exist_ok=True)

    for condition in conditions:
        scenarios = []
        for aid, text, meta in articles:
            for s in build_scenarios(aid, text, meta, condition):
                if eval_filter and s["eval"] != eval_filter:
                    continue
                scenarios.append(s)

        out_path = pathlib.Path(args.outdir) / f"ideation_{condition}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(scenarios, f, indent=2, ensure_ascii=False)

        by_eval = {}
        for s in scenarios:
            by_eval[s["eval"]] = by_eval.get(s["eval"], 0) + 1
        labeled = sum(1 for s in scenarios if s.get("labeled_lean"))
        paired  = sum(1 for s in scenarios if s.get("pair_id"))
        unique  = len(set(s["article_id"] for s in scenarios))

        print(f"\n✓ [{condition:8}] {len(scenarios)} scenarios ({unique} articles) → {out_path}")
        for ev, cnt in sorted(by_eval.items()):
            print(f"    {ev}: {cnt}")
        if labeled: print(f"    labeled: {labeled}")
        if paired:  print(f"    paired:  {paired}")


if __name__ == "__main__":
    main()
