<!-- session-meta
task_id: W130.3
tier: STANDARD
timestamp: 2026-11-26T03:00:00Z
commit: see PR
one_line_summary: W130.3: demo combo fills settled (n=2), EXP-COMBOORD-001 pre-registered, accept rule gets an edge threshold, daily demo RFQ line added paused to the existing install approval
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: EXECUTION E1/E2 on combos; BREADTH B4
gap_measure: combo demo fills settled; B4 parlay families logging
gap_delta: E1/E2 combos 2 unsettled -> 2 settled (+0.45, -0.45 gross, n=2, no verdict); B4 0 -> 1 once the install is approved
pattern_sweep: grep "accept_side\|MAX_ACCEPTS_PER_RUN" in src scripts tests: caller and tests updated; no other consumer
surface_delta: +1 paused cron line (combo RFQ, demo) in the existing install block; +1 registry entry (paused); no other surface
directive_conflicts: none
-->
# Session handoff W130.3 — combos priced per leaf, quoted through RFQ in demo, on a schedule
**Last reviewed:** 2026-11-26. COMMON RULES first line quoted: "# Wave 130 common rules".

**Part A (settled, `12_EXPLORATORY/combo_orders/RESULT_W130_3.md`).** Fill 1, 4-leg, NO @0.55, engine P(yes) 0.349, settled NO, +0.45. Fill 2, 7-leg, YES @0.45, engine 0.605, settled NO, −0.45. n = 2, no verdict. Quote rate is not measurable (3 of 12 RFQ records survive; 3 of 3 quoted in 3.9–9.1 s). The demo maker quoted 0.45/0.55 whatever the legs, so these fills do not estimate production cost. Two further combos are still unsettled.
**Defect found and fixed.** `accept_side` had no edge threshold and accepted a negative-edge one-sided YES (HTTP 400). Now: engine edge after fee ≥ 0.03, skip reasons counted per run (`skips`). Same-player cross-stat and teammate-points combos are excluded from orders.
**Part B.** `12_EXPLORATORY/combo_orders/PREREG.md` (EXP-COMBOORD-001), committed before any order-placing change: leaf rule, 0.03 margin, 1 contract, kelly 0, caps with derivations (accepts 3→6/run: 400 fills / 6 a day = 67 runs, inside the season), E1/E2/E3, judged n 400 from ≥ 40 game-days, hold-out 40% of game-days, judged look ~2027-02-10, modal outcome interval spans zero.
**Part C.** One daily line (`17 18 * * *`, `scripts/combo_rfq_demo.py`, demo host and BOT_ENV=paper only, flock) added to `deploy/cron.nba_combo_shadow`, paused registry entry, and it **folds into `nba_combo_shadow_install`** (now installs shadow + RFQ lines, same budget gate, same uninstall block; readback prints the RFQ ledgers). Not installed.

operator decisions:
> NEEDS APPROVAL BY NAME: `nba_combo_shadow_install` (now also installs the daily demo RFQ line). Demo only, 1 contract, kelly 0, max demo loss $6 a day. Approving starts B4 logging and the E1 fill count.

Open items for the window: CLAUDE.md RIGHT NOW window-maintained lines are 8 days old (RED in the scan). Part A settlement of the 2 remaining combos at the next box read.
