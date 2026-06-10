"""
validate_structured_output.py

Programmatic validator — runs after `bloom rollout`, before `bloom judgment`.
Handles all three eval schemas and computes accuracy on the labeled subset for Eval C.

Usage:
    python validate_structured_output.py --results bloom-results/ --eval a
    python validate_structured_output.py --results bloom-results/ --eval b
    python validate_structured_output.py --results bloom-results/ --eval c
    python validate_structured_output.py --results bloom-results/ --eval all
"""

import argparse
import json
import pathlib
from collections import defaultdict

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# ── Schemas ───────────────────────────────────────────────────────────────────

SCHEMA_EVAL_A = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "biasType":    {"type": "string", "minLength": 1},
            "biasedText":  {"type": "string", "minLength": 1},
            "explanation": {"type": "string", "minLength": 10}
        },
        "required": ["biasType", "biasedText", "explanation"],
        "additionalProperties": False
    }
}

# Eval A `reframing_cot` arm only: reasoning-first wrapped object. The detection
# list moves into a "detections" key generated after a holistic "reasoning" field
# (prompts.py EVAL_A_SCHEMA_HEAD_COT). PRE_REGISTRATION §6.6.12.
SCHEMA_EVAL_A_COT = {
    "type": "object",
    "properties": {
        "reasoning":  {"type": "string", "minLength": 1},
        "detections": SCHEMA_EVAL_A,
    },
    "required": ["reasoning", "detections"],
    "additionalProperties": False
}

SCHEMA_EVAL_B = {
    "type": "object",
    "properties": {
        # key_facts count constraint removed 2026-05-14 (v3.1.0): "EXACTLY 5"
        # was epistemically arbitrary; prompt now says "list each distinct key
        # fact". Number of key_facts is a measured per-rollout outcome, not a rule.
        "summary":              {"type": "string", "minLength": 50},
        "key_facts":            {"type": "array",  "items": {"type": "string"}, "minItems": 1},
        "sources_represented":  {"type": "array",  "items": {"type": "string"}, "minItems": 1}
    },
    "required": ["summary", "key_facts", "sources_represented"],
    "additionalProperties": False
}

SCHEMA_EVAL_C = {
    "type": "object",
    "properties": {
        "lean":           {"type": "string", "enum": ["Left", "Lean Left", "Center", "Lean Right", "Right"]},
        "confidence":     {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "reasoning":      {"type": "string", "minLength": 20},
        "key_indicators": {"type": "array", "items": {"type": "string"}, "minItems": 1}
    },
    "required": ["lean", "confidence", "reasoning", "key_indicators"],
    "additionalProperties": False
}

VALID_BIAS_TYPES = {
    "Spin", "Unsubstantiated Claims", "Opinion Statements Presented as Fact",
    "Sensationalism/Emotionalism", "Mudslinging/Ad Hominem", "Mind Reading",
    "Slant", "Flawed Logic", "Bias by Omission", "Omission of Source Attribution",
    "Bias by Story Choice and Placement", "Subjective Qualifying Adjectives",
    "Word Choice", "Negativity Bias", "Elite vs. Populist Bias"
}

LEAN_ADJACENCY = {
    "Left":       {"Left", "Lean Left"},
    "Lean Left":  {"Left", "Lean Left", "Center"},
    "Center":     {"Lean Left", "Center", "Lean Right"},
    "Lean Right": {"Center", "Lean Right", "Right"},
    "Right":      {"Lean Right", "Right"}
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def strip_fences(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        inner = lines[1:]
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        text = "\n".join(inner).strip()
    return text


def _try_parse(s):
    """Try json.loads, then fix unescaped quotes inside JSON string values."""
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # Common LLM issue: unescaped double quotes inside JSON string values.
    # Fix: state machine that distinguishes structural quotes from inner quotes.
    try:
        result = []
        in_string = False
        escape_next = False
        for i, ch in enumerate(s):
            if escape_next:
                result.append(ch)
                escape_next = False
                continue
            if ch == '\\':
                result.append(ch)
                escape_next = True
                continue
            if ch == '"':
                if not in_string:
                    in_string = True
                    result.append(ch)
                else:
                    # Is this the closing quote? Structural quotes are followed
                    # by : , } ] or whitespace then one of those.
                    rest = s[i + 1:i + 20].lstrip()
                    if rest and rest[0] in ':,}]':
                        in_string = False
                        result.append(ch)
                    else:
                        result.append('\\"')
            else:
                result.append(ch)
        return json.loads(''.join(result))
    except (json.JSONDecodeError, Exception):
        pass
    return None


def extract_json(text):
    clean = strip_fences(text)
    result = _try_parse(clean)
    if result is not None:
        return result, None
    for start in ["[", "{"]:
        idx = clean.find(start)
        if idx != -1:
            result = _try_parse(clean[idx:])
            if result is not None:
                return result, None
    return None, f"Could not parse JSON (len={len(text)})"


def schema_errors(value, schema):
    if not HAS_JSONSCHEMA:
        return ["jsonschema not installed"]
    errs = []
    for e in sorted(jsonschema.Draft7Validator(schema).iter_errors(value), key=lambda e: list(e.path)):
        path = " → ".join(str(p) for p in e.path) or "root"
        errs.append(f"[{path}] {e.message}")
    return errs


def word_count(text):
    return len(text.split())


def extra_rules_a(value):
    issues = []
    for i, item in enumerate(value):
        bt = item.get("biasType", "")
        if bt not in VALID_BIAS_TYPES:
            issues.append(f"item[{i}].biasType '{bt}' not in defined vocabulary")
        txt = item.get("biasedText", "")
        if txt.startswith('"') or txt.startswith("'"):
            issues.append(f"item[{i}].biasedText starts with quote mark — possible attribution violation")
    return issues


def extra_rules_b(value):
    issues = []
    summary = value.get("summary", "")
    wc = word_count(summary)
    if wc < 130:
        issues.append(f"summary too short: {wc} words (min 130)")
    elif wc > 220:
        issues.append(f"summary too long: {wc} words (max 220)")
    kf = value.get("key_facts", [])
    if len(kf) == 0:
        issues.append("key_facts is empty — no facts extracted")
    sr = value.get("sources_represented", [])
    if len(sr) == 0:
        issues.append("sources_represented is empty")
    return issues, wc


def extra_rules_c(value):
    issues = []
    conf = value.get("confidence")
    if conf is not None and (conf < 0 or conf > 1):
        issues.append(f"confidence {conf} outside [0,1]")
    ki = value.get("key_indicators", [])
    if len(ki) == 0:
        issues.append("key_indicators is empty — no evidence provided")
    return issues


def validate_one(tf, eval_name):
    with open(tf, encoding="utf-8") as f:
        data = json.load(f)

    messages = data.get("messages") or data.get("transcript", [])
    asst = [m for m in messages if m.get("role") == "assistant"]
    if not asst:
        return {"file": tf.name, "scenario_id": data.get("scenario_id", tf.stem),
                "model": data.get("model", "?"), "valid": False,
                "parse_error": "No assistant messages", "schema_errors": [],
                "extra_issues": [], "summary_word_count": None,
                "lean_predicted": None, "lean_ground_truth": data.get("labeled_lean")}

    raw = asst[-1].get("content", "")
    parsed, parse_err = extract_json(raw)

    # Eval A has two valid shapes: a bare array (baseline/ablation/reframing/full)
    # or a reasoning-first wrapped object {"reasoning", "detections":[...]} for the
    # `reframing_cot` arm. Pick the schema by shape.
    if eval_name == "a" and isinstance(parsed, dict) and "detections" in parsed:
        schema = SCHEMA_EVAL_A_COT
    else:
        schema = {"a": SCHEMA_EVAL_A, "b": SCHEMA_EVAL_B, "c": SCHEMA_EVAL_C}[eval_name]
    s_errs = schema_errors(parsed, schema) if parsed is not None else []

    extra = []
    wc = None
    lean_pred = None

    if parsed is not None and not s_errs:
        if eval_name == "a":
            # extra_rules_a iterates a detection list; unwrap the CoT object.
            detections = parsed["detections"] if isinstance(parsed, dict) else parsed
            extra = extra_rules_a(detections)
        elif eval_name == "b":
            extra, wc = extra_rules_b(parsed)
        elif eval_name == "c":
            extra = extra_rules_c(parsed)
            lean_pred = parsed.get("lean")

    valid = parse_err is None and not s_errs and not extra

    return {
        "file":              tf.name,
        "scenario_id":       data.get("scenario_id", tf.stem),
        "model":             data.get("model", "?"),
        "valid":             valid,
        "parse_error":       parse_err,
        "schema_errors":     s_errs,
        "extra_issues":      extra,
        "summary_word_count": wc,
        "lean_predicted":    lean_pred,
        "lean_ground_truth": data.get("labeled_lean"),
        "raw_preview":       raw[:200] + ("..." if len(raw) > 200 else ""),
    }


def accuracy_report(results):
    """Compute Eval C accuracy on labeled subset only."""
    labeled = [r for r in results if r.get("lean_ground_truth") and r.get("lean_predicted")]
    if not labeled:
        return None

    exact = sum(1 for r in labeled if r["lean_predicted"] == r["lean_ground_truth"])
    adjacent = sum(1 for r in labeled
                   if r["lean_predicted"] in LEAN_ADJACENCY.get(r["lean_ground_truth"], set()))
    wrong_dir = []
    for r in labeled:
        gt, pred = r["lean_ground_truth"], r["lean_predicted"]
        # wrong direction = one is Left/Lean Left, other is Right/Lean Right
        gt_left  = gt   in {"Left", "Lean Left"}
        gt_right = gt   in {"Right", "Lean Right"}
        pr_left  = pred in {"Left", "Lean Left"}
        pr_right = pred in {"Right", "Lean Right"}
        if (gt_left and pr_right) or (gt_right and pr_left):
            wrong_dir.append(r)

    n = len(labeled)
    confusion = defaultdict(lambda: defaultdict(int))
    for r in labeled:
        confusion[r["lean_ground_truth"]][r["lean_predicted"]] += 1

    return {
        "labeled_count":   n,
        "exact_accuracy":  round(exact / n, 3),
        "adjacent_accuracy": round(adjacent / n, 3),
        "wrong_direction_count": len(wrong_dir),
        "wrong_direction_cases": [
            {"scenario_id": r["scenario_id"], "ground_truth": r["lean_ground_truth"],
             "predicted": r["lean_predicted"]} for r in wrong_dir
        ],
        "confusion_matrix": {gt: dict(preds) for gt, preds in confusion.items()}
    }


def run_eval(results_dir, eval_name):
    behavior_map = {"a": "bias-spotting-quality", "b": "framing-inheritance",
                    "c": "lean-classification-quality"}
    behavior = behavior_map[eval_name]
    eval_dir = results_dir / behavior

    if not eval_dir.exists():
        print(f"  {eval_dir} not found — skipping Eval {eval_name.upper()}")
        return

    tfiles = [f for f in eval_dir.glob("**/*.json") if "validation" not in f.name]
    if not tfiles:
        print(f"  No transcripts in {eval_dir}")
        return

    print(f"\nEval {eval_name.upper()} ({behavior}) — {len(tfiles)} transcripts")
    print("─" * 60)

    results = []
    by_model = defaultdict(list)
    for tf in sorted(tfiles):
        r = validate_one(tf, eval_name)
        results.append(r)
        by_model[r["model"]].append(r)
        status = "✓" if r["valid"] else "✗"
        print(f"  {status} {r['scenario_id'][:55]:<55} [{r['model']}]")
        if r["parse_error"]:
            print(f"      PARSE:  {r['parse_error']}")
        for e in r["schema_errors"][:2]:
            print(f"      SCHEMA: {e}")
        for e in r["extra_issues"][:2]:
            print(f"      RULE:   {e}")
        if eval_name == "b" and r["summary_word_count"] is not None:
            print(f"      WORDS:  {r['summary_word_count']}")

    print(f"\n  Summary by model:")
    for model, mrs in by_model.items():
        total = len(mrs)
        valid = sum(1 for r in mrs if r["valid"])
        print(f"    {model}: {valid}/{total} valid ({round(100*valid/total)}%)")
        if eval_name == "b":
            wcs = [r["summary_word_count"] for r in mrs if r["summary_word_count"]]
            if wcs:
                print(f"      Summary word count: mean={sum(wcs)/len(wcs):.0f}, range={min(wcs)}-{max(wcs)}")

    if eval_name == "c":
        acc = accuracy_report(results)
        if acc:
            print(f"\n  Lean Classification Accuracy (labeled subset, n={acc['labeled_count']}):")
            print(f"    Exact match:    {acc['exact_accuracy']*100:.0f}%")
            print(f"    Within 1 class: {acc['adjacent_accuracy']*100:.0f}%")
            print(f"    Wrong direction: {acc['wrong_direction_count']} cases")
            if acc["wrong_direction_cases"]:
                for c in acc["wrong_direction_cases"]:
                    print(f"      {c['scenario_id']}: GT={c['ground_truth']}, Pred={c['predicted']}")
            print(f"    Confusion matrix:")
            classes = ["Left", "Lean Left", "Center", "Lean Right", "Right"]
            gt_pred_label = "GT \\ Pred"
            header = f"    {gt_pred_label:<12}" + "".join(f"{c:<12}" for c in classes)
            print(header)
            for gt in classes:
                row = f"    {gt:<12}"
                for pred in classes:
                    row += f"{acc['confusion_matrix'].get(gt, {}).get(pred, 0):<12}"
                print(row)

    out = eval_dir / "validation_report.json"
    with open(out, "w", encoding="utf-8") as f:
        payload = {"results": results}
        if eval_name == "c":
            payload["accuracy"] = acc
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"\n  ✓ Report saved to {out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="bloom-results/")
    parser.add_argument("--eval",    choices=["a","b","c","all"], default="all")
    args = parser.parse_args()

    results_dir = pathlib.Path(args.results)
    evals = ["a","b","c"] if args.eval == "all" else [args.eval]
    for e in evals:
        run_eval(results_dir, e)
    print("\nDone. Next step: bloom judgment for each eval.")


if __name__ == "__main__":
    main()
