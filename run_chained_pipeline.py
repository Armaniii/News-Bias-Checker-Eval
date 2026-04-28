"""
run_chained_pipeline.py

Option B runner: chains your two AI calls in sequence the same way your
production pipeline does, then feeds the combined context into Bloom's
judgment stage for quality evaluation.

Pipeline:
    Article
      │
      ▼ Call 1 (analysis-system + analysis-user + article)
    Bias Analysis JSON array
      │
      ▼ Call 2 (score-system + article + bias array)
    Rating JSON {rating, explanation}
      │
      ▼ Bloom Judgment (evaluates both outputs together)
    Quality scores per custom dimension

Usage:
    pip install anthropic openai
    python run_chained_pipeline.py \
        --ideation bloom-data/ideation_static.json \
        --model claude    # or: --model gpt4o
        --output bloom-results/chained/
"""

import argparse
import json
import os
import pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Paste your exact prompts here ────────────────────────────────────────────

ANALYSIS_SYSTEM = """You are an AI tool for journalists to identify bias in their articles. Analyze the article and return biased phrases, their bias types, and explanations. IMPORTANT ignore everything that quotes other people, only use what author is saying.
CRITICAL ATTRIBUTION RULE: When the author reproduces a quoted source's statement at length (e.g., a full statement, a press release, an email), the language in that statement belongs ENTIRELY to the source, not the author. Do not flag language from extended reproduced statements as the author's bias, even when the language is extreme. The author's bias is revealed only in: (a) their own connecting prose, (b) their choice of which sources to include, (c) the framing of those sources, and (d) what they choose to omit.
Output ONLY a valid JSON array. No preamble, no explanation outside the JSON, no markdown fences. If no bias is found, output an empty array: []
Format:
[{"biasType": "Type of media bias", "biasedText": "Example from the article", "explanation": "explanation"}]"""

ANALYSIS_USER_PREFIX = """Types of media bias:
- Spin, Unsubstantiated claims, Opinion Statements Presented as Fact,
  Sensationalism and Emotionalism, Mudslinging/Ad Hominem, Mind reading,
  Slant, Bias by Omission, Subjective Qualifying Adjectives, Word Choice,
  Negativity Bias, Elite vs. Populist Bias.
Exclude quotes from analysis. Be cautious and humble. Present fewer, confident examples.
CRITICAL ATTRIBUTION RULE: see system prompt.
Analyze this article:"""

SCORE_SYSTEM = """You are a senior editorial analyst conducting bias reviews for AllSides, a nonpartisan media-literacy organization. You will receive a bias analysis JSON array produced by an earlier AI call and the original news article. Your task is to score the quality of that bias analysis on a 1-10 scale across four dimensions.

Scoring dimensions:
1. accuracy_of_bias_identification (1-10): Are the flagged phrases genuinely biased? Does the analysis correctly categorize the bias type for each instance?
2. completeness (1-10): Does the analysis catch the major instances of bias in the article without overlooking significant examples?
3. false_positive_rate (1-10): A high score means few or no false positives. Penalize analyses that flag neutral, factual, or properly attributed language as biased.
4. attribution_rule_compliance (1-10): Does the analysis correctly respect the attribution rule? Quoted speech, press releases, and extended reproduced statements from sources must NOT be flagged as author bias. A high score means the analysis never misattributes a source's language to the author.

Scoring guidelines:
- Compare each flagged item against the original article text.
- Consider whether the bias type label is appropriate for the flagged text.
- Check that direct quotes and reproduced source statements were excluded.
- Award a 10 only when the dimension is handled flawlessly.
- Award a 1 when the dimension is handled extremely poorly or not at all.

Output ONLY a valid JSON object. No preamble, no explanation outside the JSON, no markdown fences.
Format: {"accuracy_of_bias_identification": <number>, "completeness": <number>, "false_positive_rate": <number>, "attribution_rule_compliance": <number>, "overall_score": <number>, "reasoning": "<brief explanation of scores>"}"""

SCORE_USER_PREFIX = ""  # Your score-user prompt (empty string if the system carries it all)

# ─────────────────────────────────────────────────────────────────────────────


def call_anthropic(system: str, user: str, model="claude-sonnet-4-20250514") -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model=model,
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": user}]
    )
    return msg.content[0].text


def call_openai(system: str, user: str, model="gpt-4o") -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.chat.completions.create(
        model=model,
        max_tokens=2000,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
    )
    return resp.choices[0].message.content


def run_chained(scenario: dict, caller, model_label: str) -> dict:
    """Run both calls for a single article scenario and return the combined result."""
    scenario_id = scenario["scenario_id"]
    article_text = scenario["user_message"]  # already formatted with prefix

    # ── Call 1: Bias Analysis ─────────────────────────────────────────────
    try:
        analysis_raw = caller(ANALYSIS_SYSTEM, article_text)
        analysis_json = json.loads(analysis_raw.strip())
    except (json.JSONDecodeError, Exception) as e:
        analysis_json = []
        analysis_raw = f"ERROR: {e}"

    # ── Call 2: Bias Scoring (with Call 1 output in context) ──────────────
    # Build the combined user message for Call 2 that mirrors your production pipeline
    score_user = f"""{SCORE_USER_PREFIX}

BIAS ANALYSIS FROM CALL 1:
{json.dumps(analysis_json, indent=2)}

ARTICLE TO RATE:
{article_text}"""

    try:
        rating_raw = caller(SCORE_SYSTEM, score_user)
        # Strip markdown fences if present
        clean = rating_raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:-1])
        rating_json = json.loads(clean)
    except (json.JSONDecodeError, Exception) as e:
        rating_json = {"rating": None, "explanation": f"PARSE ERROR: {e}"}
        rating_raw = f"ERROR: {e}"

    return {
        "scenario_id": scenario_id,
        "model": model_label,
        "tags": scenario.get("tags", []),
        "ground_truth_lean": scenario.get("ground_truth_lean"),

        # Full transcript for Bloom's viewer and judgment stage
        "transcript": [
            {"role": "system",    "content": ANALYSIS_SYSTEM},
            {"role": "user",      "content": article_text},
            {"role": "assistant", "content": analysis_raw},
            {"role": "user",      "content": score_user},
            {"role": "assistant", "content": rating_raw},
        ],

        # Parsed outputs for quick analysis
        "analysis_output":  analysis_json,
        "rating_output":    rating_json,
        "rating_value":     rating_json.get("overall_score"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ideation", default="bloom-data/ideation_static.json")
    parser.add_argument("--model", choices=["claude", "gpt4o"], default="claude")
    parser.add_argument("--output", default="bloom-results/chained/")
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    with open(args.ideation, encoding="utf-8") as f:
        scenarios = json.load(f)
    if args.limit:
        scenarios = scenarios[:args.limit]

    if args.model == "claude":
        model_id = "claude-sonnet-4-20250514"
        caller = lambda sys, usr: call_anthropic(sys, usr, model_id)
        model_label = "claude-sonnet-4"
    else:
        model_id = "gpt-4o"
        caller = lambda sys, usr: call_openai(sys, usr, model_id)
        model_label = "gpt-4o"

    pathlib.Path(args.output).mkdir(parents=True, exist_ok=True)
    results = []

    print(f"Running {len(scenarios)} scenarios with {model_label} ({args.workers} workers)...")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_chained, s, caller, model_label): s for s in scenarios}
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            results.append(result)
            print(f"  [{i+1}/{len(scenarios)}] {result['scenario_id']} → rating: {result['rating_value']}")

    # Save full results
    out_path = pathlib.Path(args.output) / f"results_{model_label}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Save summary CSV for quick analysis
    import csv
    csv_path = pathlib.Path(args.output) / f"summary_{model_label}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["scenario_id", "model", "rating_value", "ground_truth_lean", "tags"])
        writer.writeheader()
        for r in results:
            writer.writerow({
                "scenario_id": r["scenario_id"],
                "model": r["model"],
                "rating_value": r["rating_value"],
                "ground_truth_lean": r.get("ground_truth_lean", ""),
                "tags": "|".join(r.get("tags", []))
            })

    print(f"\n✓ Results saved to {out_path}")
    print(f"✓ Summary CSV saved to {csv_path}")
    ratings = [r["rating_value"] for r in results if r["rating_value"] is not None]
    if ratings:
        print(f"\nRating stats for {model_label}:")
        print(f"  Mean:  {sum(ratings)/len(ratings):.2f}")
        print(f"  Min:   {min(ratings):.1f}")
        print(f"  Max:   {max(ratings):.1f}")
        print(f"  Left (<0): {sum(1 for r in ratings if r < 0)} articles")
        print(f"  Neutral:   {sum(1 for r in ratings if r == 0)} articles")
        print(f"  Right (>0): {sum(1 for r in ratings if r > 0)} articles")


if __name__ == "__main__":
    main()
