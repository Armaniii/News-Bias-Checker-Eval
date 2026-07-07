# Design brief: "Same verdicts, drifting stories" (main results figure)

Goal: one glance = the thesis. A neutrality instruction leaves two models'
decisions unchanged; the rationales of ONE model drift toward the center,
~2x harder against right-leaning sources.

Output: self-contained SVG, vector text, 1650x1150 viewBox (6.75in print),
white bg, publication restraint (no infographic styling).

## Layout: 2x2 matrix + footer
Columns = models: "Claude Sonnet 4.5" | "GPT-4.1".
Rows = channels: DECISIONS (top) | RATIONALES (bottom). Thin gray rules.

## Top row: slopegraphs (flat bands)
Two axes per panel: "no directive" -> "+ neutrality directive";
y = detections/article (0-20). ~80 thin lines (#94a3b8 @25%), thick mean
line (#334155). Render to match REAL distributions:
- Sonnet 4.5 (n=200): count deciles 0/5/7/11/14; delta deciles -2/0/0/+2/+4; mean +0.86
- GPT-4.1  (n=199): count deciles 1/4/7/10/13; delta deciles -2/-1/0/+2/+3; mean +0.51
Badges: Sonnet "D=+0.86 [0.57,1.15] . within +/-2.0 (TOST p<.001) . labels k=0.92";
GPT-4.1 "D=+0.51 [0.21,0.81] . within +/-2.0 (TOST p<.001) . labels k=0.88".
Row annotation: "The directive does not reach the decisions."

## Bottom row: dumbbells (scissors)
x = % rationales with directional substitution (0-25%). Two dumbbells per
panel (one per judge). Round dot = left-sub on Right sources; hollow
square = right-sub on Left sources.
REAL VALUES:
  Sonnet 4.5 | Judge A Sonnet 4.6 (teal #0f766e): 12.5% vs 4.3% (p=.006)
  Sonnet 4.5 | Judge B GPT-5 (amber #b45309):     22.2% vs 10.2% (p=.004)
  GPT-4.1    | Judge A: 2.1% vs 2.5%   | Judge B: 6.7% vs 6.1%  ("no asymmetry, p=.46")
Sonnet panel: shade dumbbell gaps 12% opacity; annotate "both judges
independently significant . pooled 1.9x, p=.0014"; inset: "mechanism: 3:1
additive - left-coded framing is added, not right-coded stripped".
Row annotation: "The rationales drift - in one model."

## Footer strip
"Inputs balanced across Left/Right strata - loaded-lexicon density d=0.10
(p=.55) . models' own baseline detections d=0.13 (p=.40) . expert ratings
imbalanced against the effect . N=200 articles, pre-registered"

## Hard rules
- NO red/blue for political direction (position/labels only); color only
  for judges (teal/amber, colorblind-safe).
- No 3D/shadows/icons/gradients. Helvetica/Arial, >=7pt at print width.
- All numbers above are real data - do not alter.
- Must survive grayscale: flat bands above; one open + one closed scissor below.

Acceptance: figure alone conveys (1) decisions unchanged, (2) one model's
rationales drift ~2x on right-leaning sources per two independent judges,
(3) other model shows nothing, (4) inputs balanced.
