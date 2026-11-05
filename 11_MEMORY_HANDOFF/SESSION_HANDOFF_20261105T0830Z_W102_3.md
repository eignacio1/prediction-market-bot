# Session handoff - W102.3 flex (2026-11-05)

Rules read first: `# Wave 102 common rules`.

vision_pillar: EXECUTION
gap_measure: B-026 picks sheet distinct picks/night; E1 demo-order refusals (counted on existing logs)
gap_delta: 2026-11-03 slate 259 raw -> 127 distinct picks (30 market groups, 11 NHL games); refusals 2,259 since 10-16 (all 10-16..10-29, none since), balance now logged on every refusal (PR #426)
pattern_sweep: GG-1690 de-dup applied in the one builder (`picks_sheet.build`); the refusal-balance logging was added to the shadow path, the only order path that logged refusals without balance; `lookup_fill` consumers swept: only `demo_fill_forward_report.py` (GG-1770).
surface_delta: 0 (no live component added; 1 log-field addition, 0 new cron/service)

## Done
- Part A: PR #422 (GG-1690) rebased x3, CI green, merged. Sheet rebuild on the box has not been read yet, so picks before/after on the live sheet and `n_rows_before_dedupe` are not confirmed; offline on the 11-03 slate: 259 -> 127.
- Part B: `12_EXPLORATORY/picks_sheet_w102/last_settled_night.md` (+ collector, analysis).
- Part C: `12_EXPLORATORY/demo_balance_w102/RESULT.md`; PR #426 (balance on every shadow refusal) rebased on main, 97 tests pass, CI running at handoff.

## Found, registered, not fixed
- **GG-1771 (HIGH)**: `submit_order` sends the NO price in the wrong frame; NO orders are mirror-priced (fill cost ~ price_yes instead of 1 - price_yes). Probable driver of the adverse-selection pattern in the fill data. Needs a fix block plus a before/after cut of every NO-side fill statistic.
- **GG-1770 (MEDIUM)**: `lookup_fill` ignores `action=sell`, inverting won/lost for NO fills in the fill report.

## For the next window / operator
- Demo cash ~ $1,006 at ~$380/day: refusals likely return near 11-08. Top-up is plumbing (no real money). Cancelling control-arm orders would change a pre-registered arm: operator question.
- After #426 merges: read `deploy_truth_read` / `logs/vps_deploy.log`; the t4-mlb restart decision is NOT recorded (no merge deploy read yet). Box installs not run by this terminal.
- Not run: the 102.3 addendum (B-043 branch cleanup, done by W102.5). CLAUDE.md Step 1-4 and Q1-Q7 outputs were not shown in this session.
- GG numbers 1770/1771 were taken without a claimed range (claim row said TBD); check for collisions.
