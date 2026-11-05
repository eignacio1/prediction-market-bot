<!-- session-meta
task_id: W102.4
tier: STANDARD
timestamp: 2026-11-05T07:00:00Z
commit: 7ec2349
one_line_summary: W102.4 quant lane - ADOPT gain split (placement ~1c, selection ~18c), multiplicity ledger with Holm/BH/alpha-spending, proof-calendar age panel on /visual.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PROOF
gap_measure: P2 verdict quality (ADOPT split; ledger N of N); calendar age visible
gap_delta: ADOPT +0.190 split into placement ~0.01 and selection ~0.18 with game-clustered 90% intervals; verdicts counted N of N in MULTIPLICITY_LEDGER.md; calendar age now on /visual (red > 1 day)
pattern_sweep: n/a (no defect fixed)
surface_delta: 0 (no cron, no service; one read-only panel module)
-->

# SESSION HANDOFF - W102.4 (quant lane)
Common rules first line: "# Wave 102 common rules". PR #427 merged green (7ec2349). No pre-registered rule, alpha or verdict changed.

**A. ADOPT decomposition** (`12_EXPLORATORY/quant_w102/adopt_decomposition.md`, `src/prediction_market_bot/quant/fill_decomposition.py`, 5 known-answer tests). Of the ~19c gain, about 1c is placement (paying less for the same contract) and about 18c is selection (which contracts get filled). Strata = (ticker, held side); intervals are game-clustered bootstrap. Caveat: the log's side/price differs from the cache's on some rows; I used the cache, the same source as the existing report, and it reproduced +0.190.

**B. Multiplicity ledger** (`12_EXPLORATORY/quant_w102/MULTIPLICITY_LEDGER.md`, `quant/multiplicity.py`, 5 tests). The ADOPT (a) criterion survives daily-look and Holm adjustment. The EXP-037 GAME_TOTAL T1/T2 RULED_OUT word would not survive a family-wise view (Holm-adjusted p 0.23 and 0.35); T1/T2/T3 share games, so they are one finding counted twice.

**C. Calendar age** (`scripts/proof_calendar_age.py`, `/visual` panel, 5 tests). Shows generated-at and age in days; red past 1 day; missing or unparseable file shows an error, never blank or green.

**Recommendation to the window (operator decides):** describe the NFL shadow ADOPT as a selection effect, not a placement win; review the EXP-037 GAME_TOTAL RULED_OUT wording against the family-wise view; count T1/T2/T3 as one finding.
