# WARNING: mixed corpora in these rollout directories
eval-c/*/ (and eval-a, eval-b) contain BOTH the stated v3 corpus (200
articles, ids in ../articles_v3.csv, text-only prompts, 2026-07) AND ~100
legacy rollouts (2026-04, ids like article_backup7_* / v2 ids) whose prompts
included HEADLINE and SOURCE — i.e. outlet-label leakage. Files are left in
place because the judge caches were built against these paths, but EVERY
analysis MUST filter to articles_v3 ids. Canonical filtered analyses:
analysis/triage_router.py, analysis/four_family_analysis.py.
Panel finding: paper/notes/panel_review_p2.md (DA-C1 / R1-W1).
