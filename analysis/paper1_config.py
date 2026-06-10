"""
paper1_config.py — single source of truth for Paper-1 (Path-B) analysis config.

Centralizes the constants that were previously hardcoded/scattered across the
analysis pipeline (conditions, judge names, paths, strata, the BH-FDR family),
so the analysis layer cannot drift from the pre-registration / prompts.py.

See: PRE_REGISTRATION.md §6.6.10 (8-test family), §6.7 (Path B), §1.1 (judges).
"""

from __future__ import annotations
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"
ROLLOUT = RESULTS / "rollout"

# --- Models (Path-B canonical, PRE_REGISTRATION §1.1) ----------------------
TARGETS = ["claude-sonnet-4-5", "gpt-4.1"]
JUDGES = ["claude-sonnet-4-6", "gpt-5"]          # cross-family Stage-1 pair
JUDGE_FAMILY = {"claude-sonnet-4-6": "anthropic", "gpt-5": "openai"}

# --- Conditions (mirror prompts.PROMPTS; do not hardcode elsewhere) ---------
# Imported lazily to avoid a hard dependency when only constants are needed.
def conditions(eval_letter: str) -> list[str]:
    import sys
    sys.path.insert(0, str(ROOT))
    from prompts import PROMPTS
    return list(PROMPTS[f"eval-{eval_letter}"].keys())

# The directive contrast that load-bears H27/H27b/H28/H29.
ARM_TREATMENT = "reframing"
ARM_CONTROL = "ablation"
ARM_COT = "reframing_cot"          # descriptive generation-order arm (D-HCoT)

# --- Strata -----------------------------------------------------------------
LEANS_5 = ["Left", "Lean Left", "Center", "Lean Right", "Right"]
LEAN_3 = {"Left": "Left", "Lean Left": "Left", "Center": "Center",
          "Lean Right": "Right", "Right": "Right"}
THEMES = ["immigration_border", "foreign_defense", "elections_governance",
          "economy", "crime_justice", "social_culture_rights",
          "climate_energy", "health_education"]

# --- Corpora (source text by stage) ----------------------------------------
STAGE1_CORPUS = ROOT / "articles_v2.csv"     # existing v1+v2 rollouts (N=100)
STAGE2_CORPUS = ROOT / "articles_v3.csv"     # new N=200 grid

# Cap source text injected into judge prompts (token control). Judges compare
# output framing to the source; ~4000 chars (~600 words) is enough context.
SOURCE_TEXT_MAXCHARS = 4000

# --- BH-FDR family (PRE_REGISTRATION §6.6.10) -------------------------------
# Confirmatory (directional) + Equivalence. Family size = 8.
BH_FAMILY = {
    "H22": "VAR_inheriting ~ condition x source_lean (Eval A)",
    "H23": "VAR interaction: reframing x RIGHT vs reframing x LEFT",
    "H25": "FDC_schema ~ source_lean (Eval C)",
    "H26": "directional RD on Eval C reasoning, stratified by source_lean",
    "H27": "VAR_inheriting ~ arm (reframing vs ablation), Eval A",
    "H27b": "FDC_schema ~ arm (reframing vs ablation), Eval C",
    "H28": "TOST on Eval A detection count (reframing vs ablation), |d|<2.0",
    "H29": "bootstrap kappa on Eval C lean (reframing vs ablation) >= 0.85",
}
DESCRIPTIVE = {
    "H30": "joint decision-rationalization dissociation (scope-boundary report)",
    "H31": "CFI/VAR/FDC mutual correlation within cells",
    "H32": "CCDR matrix (CFI-cluster vs EP, LCA); ceiling-caveated",
    "D-HCoT-A": "reframing_cot vs reframing on VAR + detection count (Eval A)",
    "D-HCoT-C": "reframing_cot vs reframing on FDC + lean labels (Eval C)",
}

FDC_SCALE_MIN, FDC_SCALE_MAX, FDC_MIDPOINT = 1, 7, 4   # matches prompts.py
H28_EQUIV_BOUND = 2.0          # |Δ| detections/article (SESOI; re-derive post-Stage1)
H29_KAPPA_FLOOR = 0.85
BH_Q = 0.05
