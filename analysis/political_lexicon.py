"""
Paired political lexicon for direction-asymmetry analysis (NF-1).

Construction principles:
  1. **Paired terminology** — when LEFT and RIGHT framings of the same concept
     differ in vocabulary (e.g., "undocumented" vs "illegal alien"), include
     both as a matched pair. This preserves symmetry of construction.
  2. **Concept categories** — if a concept is owned by one side without a
     direct counterpart (e.g., "border wall" is owned by RIGHT; "systemic
     racism" by LEFT), it is included only on the relevant side. The
     COUNTS of unpaired concepts per side are then compared as a robustness
     check on lexicon balance.
  3. **Source provenance** — every entry is sourced from one of:
     (a) AllSides ideological-marker dictionary (rate-article-system.txt:19-46)
     (b) standard political-science vocabulary (Entman 2007, Iyengar 1991)
     (c) LiveJournal/AP style guide on contested terminology
  4. **Specificity** — patterns are *phrases*, not bare keywords, to avoid
     spurious matches (e.g., "free market" not "free", "border security"
     not "border").
  5. **Symmetry guarantee** — by construction the PAIRED list contains
     one LEFT and one RIGHT entry per row. The UNPAIRED lists are
     independently sourced; their lengths are reported in the analysis as
     a transparency note.

Lower-cased substring match is used by default. Matching is case-insensitive
and uses word-boundary expansion when a regex hint is included.
"""

from __future__ import annotations
import re
from typing import Tuple, List


# =============================================================================
# PAIRED — direct LEFT/RIGHT terminology pairs for the same concept
# Each entry: (left_phrase, right_phrase, concept_category)
# =============================================================================

PAIRED_TERMS: List[Tuple[str, str, str]] = [
    # Immigration terminology
    ("undocumented immigrant",   "illegal alien",          "immigration"),
    ("undocumented",             "illegal immigrant",      "immigration"),
    ("asylum seeker",            "border crosser",         "immigration"),
    ("dreamer",                  "illegal entrant",        "immigration"),
    ("sanctuary city",           "lawless city",           "immigration"),  # rare on RIGHT
    ("path to citizenship",      "amnesty",                "immigration"),
    # Abortion terminology
    ("pro-choice",               "pro-life",               "abortion"),
    ("abortion rights",          "right to life",          "abortion"),
    ("reproductive rights",      "unborn child",           "abortion"),
    ("reproductive freedom",     "protect the unborn",     "abortion"),
    # Firearms terminology
    ("gun control",              "gun rights",             "firearms"),
    ("gun violence",             "second amendment",       "firearms"),
    ("assault weapon",           "modern sporting rifle",   "firearms"),
    ("gun safety",               "right to bear arms",     "firearms"),
    # Tax terminology
    ("tax the rich",             "tax cuts",               "taxation"),
    ("tax the wealthy",          "tax relief",             "taxation"),
    ("fair share of taxes",      "tax burden",             "taxation"),
    # Climate terminology
    ("climate crisis",           "climate alarmism",       "climate"),
    ("climate emergency",        "climate skepticism",     "climate"),
    ("climate denier",           "climate realist",        "climate"),
    # Healthcare terminology
    ("medicare for all",         "socialized medicine",    "healthcare"),
    ("universal healthcare",     "government-run healthcare", "healthcare"),
    ("right to healthcare",      "free market healthcare",  "healthcare"),
    # Criminal justice terminology
    ("mass incarceration",       "tough on crime",         "criminal_justice"),
    ("police brutality",         "war on cops",            "criminal_justice"),
    ("criminal justice reform",  "law and order",          "criminal_justice"),
    ("defund the police",        "back the blue",          "criminal_justice"),
    # Economic terminology
    ("income inequality",        "wealth creators",        "economic"),
    ("living wage",              "free market wages",      "economic"),
    ("corporate greed",          "free enterprise",        "economic"),
    ("workers rights",           "right to work",          "economic"),
    # Identity / culture
    ("racial justice",           "color blind",            "race"),
    ("systemic racism",          "racial victimhood",      "race"),
    ("white privilege",          "white guilt",            "race"),
    ("anti-racist",              "race essentialist",      "race"),
    # Gender / sexuality
    ("gender identity",          "biological sex",         "gender"),
    ("transgender rights",       "gender ideology",        "gender"),
    ("lgbtq+ rights",            "traditional values",     "gender"),
    ("gender-affirming care",    "child gender confusion", "gender"),
    # Voting
    ("voting rights",            "election integrity",     "voting"),
    ("voter suppression",        "voter fraud",            "voting"),
    ("expanded voting access",   "voter id laws",          "voting"),
    # Education
    ("inclusive curriculum",     "parental rights in education", "education"),
    ("anti-racist education",    "critical race theory",   "education"),
    ("public school funding",    "school choice",          "education"),
]


# =============================================================================
# UNPAIRED LEFT — concepts owned predominantly by LEFT framing
# Sourced primarily from AllSides LEFT ideological markers
# =============================================================================

UNPAIRED_LEFT: List[str] = [
    # Social policy
    "social safety net", "safety net programs",
    "marginalized communities", "marginalized groups",
    "intersectionality", "intersectional",
    "diversity equity inclusion", "dei initiative",
    "affirmative action",
    # Economic
    "wealth inequality", "wage gap", "gender pay gap",
    "labor union", "union worker",
    "corporate accountability", "corporate malfeasance",
    # Climate / environment
    "fossil fuel", "renewable energy", "green new deal",
    "carbon emissions", "decarbonization",
    "environmental justice",
    # Civil rights
    "civil rights", "voting rights act",
    "police accountability",
    "school-to-prison pipeline",
    # Social
    "hate crime", "hate speech",
    "marriage equality",
    "menstrual equity",
    # Healthcare
    "medicaid expansion", "obamacare",
    "prescription drug prices",
    # Workers
    "minimum wage increase", "fight for fifteen",
    "essential worker",
    # Misc
    "misinformation", "disinformation",
    "white nationalism", "white supremacist",
    "extremist", "far-right extremism",
    "fascism", "fascist",
    "patriarchy",
]


# =============================================================================
# UNPAIRED RIGHT — concepts owned predominantly by RIGHT framing
# Sourced primarily from AllSides RIGHT ideological markers
# =============================================================================

UNPAIRED_RIGHT: List[str] = [
    # Government / sovereignty
    "limited government", "small government",
    "fiscal responsibility", "balanced budget",
    "federal overreach", "government overreach",
    "states rights",
    "deep state", "swamp", "drain the swamp",
    # Border / immigration
    "border security", "border wall",
    "illegal immigration", "illegal crossings",
    "remain in mexico",
    # Crime / order
    "violent crime", "crime wave",
    "rule of law",
    # Culture
    "religious liberty", "religious freedom",
    "traditional family", "family values",
    "judeo-christian",
    "patriotic", "american values",
    "constitutional rights", "constitutional originalism",
    "founding fathers",
    # Anti-progressive frames
    "woke", "wokeness", "woke ideology",
    "cancel culture",
    "political correctness",
    "virtue signaling",
    "radical left", "far-left",
    "socialist", "socialism", "marxist", "communism",
    "indoctrinate", "indoctrination",
    "groomer", "grooming",
    # Economic frames
    "free market", "free enterprise",
    "deregulation",
    "personal responsibility",
    # Military / foreign policy
    "strong military", "peace through strength",
    "america first",
    # Misc
    "antifa",
    "abolish ice", "abolish the police",  # framings RIGHT uses to attack LEFT positions
    "indoctrination in schools",
]


# Build the search engine — sorted by phrase length descending so longer
# phrases match before shorter substrings of them.
def _build_patterns() -> Tuple[List[Tuple[str, str, str]], dict]:
    """Returns ([(phrase, side, category), ...], counts)."""
    patterns = []
    for left, right, cat in PAIRED_TERMS:
        patterns.append((left.lower(),  "left",  f"paired_{cat}"))
        patterns.append((right.lower(), "right", f"paired_{cat}"))
    for term in UNPAIRED_LEFT:
        patterns.append((term.lower(), "left", "unpaired_left"))
    for term in UNPAIRED_RIGHT:
        patterns.append((term.lower(), "right", "unpaired_right"))
    # Sort by length descending so longer phrases match first
    patterns.sort(key=lambda x: -len(x[0]))
    counts = {
        "paired": len(PAIRED_TERMS),
        "unpaired_left": len(UNPAIRED_LEFT),
        "unpaired_right": len(UNPAIRED_RIGHT),
        "total_left_phrases": len(PAIRED_TERMS) + len(UNPAIRED_LEFT),
        "total_right_phrases": len(PAIRED_TERMS) + len(UNPAIRED_RIGHT),
    }
    return patterns, counts


_PATTERNS, LEXICON_COUNTS = _build_patterns()


def classify_text(text: str) -> dict:
    """
    Classify a text snippet as left-coded, right-coded, both, or neither.

    Returns:
      {
        "left_hits":  list of (phrase, category) matched,
        "right_hits": list of (phrase, category) matched,
        "is_left":    bool — any left match,
        "is_right":   bool — any right match,
        "direction":  "left" | "right" | "both" | "neither",
      }
    """
    if not isinstance(text, str) or not text:
        return {"left_hits": [], "right_hits": [], "is_left": False,
                "is_right": False, "direction": "neither"}
    t = text.lower()
    left_hits, right_hits = [], []
    for phrase, side, cat in _PATTERNS:
        # Use word-boundary regex for short phrases to avoid spurious substring matches
        if len(phrase) < 8:
            if not re.search(r"\b" + re.escape(phrase) + r"\b", t):
                continue
        else:
            if phrase not in t:
                continue
        if side == "left":
            left_hits.append((phrase, cat))
        else:
            right_hits.append((phrase, cat))
    is_l, is_r = bool(left_hits), bool(right_hits)
    if is_l and is_r:
        d = "both"
    elif is_l:
        d = "left"
    elif is_r:
        d = "right"
    else:
        d = "neither"
    return {"left_hits": left_hits, "right_hits": right_hits,
            "is_left": is_l, "is_right": is_r, "direction": d}


def lexicon_summary() -> str:
    """Human-readable summary for inclusion in reports."""
    c = LEXICON_COUNTS
    return (f"Paired terminology pairs: {c['paired']} "
            f"({c['paired']} LEFT + {c['paired']} RIGHT). "
            f"Unpaired LEFT phrases: {c['unpaired_left']}. "
            f"Unpaired RIGHT phrases: {c['unpaired_right']}. "
            f"Total LEFT match patterns: {c['total_left_phrases']}; "
            f"total RIGHT match patterns: {c['total_right_phrases']}.")


if __name__ == "__main__":
    print(lexicon_summary())
    samples = [
        "the systemic racism in our institutions",
        "the illegal alien crisis at the border",
        "tax the wealthy and protect medicare for all",
        "limited government and personal responsibility",
        "the senator made a statement on Tuesday",  # neither
        "concerns about climate change and gun control versus border security",  # both
    ]
    for s in samples:
        r = classify_text(s)
        print(f"  [{r['direction']:8}] {s}")
        if r["left_hits"]:  print(f"          LEFT:  {r['left_hits']}")
        if r["right_hits"]: print(f"          RIGHT: {r['right_hits']}")
