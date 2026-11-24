# SESSION HANDOFF W125.1 - placement as a decision (closed)
vision_pillar: EXECUTION E2 / E3 (net per filled bet with fee actually charged; adverse selection) - measured, descriptive, no cell supported
gap_measure: fill model live on the box (3,214 post-epoch arm orders, 0 unknown fill status); best cell 11 settled-filled games vs the 20 bar
surface_delta: +1 read-only box task (placement_fill_read), +1 default-off switch value (ARM_PLACEMENT_POLICY=rules), +1 frozen empty config/placement_rules.json; no cron, no service
pattern_sweep: swept src/ for real-money constants in demo caps (MAX_DAILY_LOSS_PCT, _HARD_LIMITS): arm path clean, ride_orders.py 500/150 left -> GG-2008; model_records consumers (tests/test_placement_join.py) pass
directive_conflicts: none

## Landed
- #554 (124.3 H-EXEC-4 prereg, PREREG untouched) merged. #560 (Part A + Part B + GG-2008 + gap index) merged, CI green.
- Part A: placement/fill_model.py, scripts/placement_fill_read.py (read-only), allowlist entry. Result: box result 20261124T0544Z.
- Part B: place_rules + ARM_PLACEMENT_POLICY=rules; default `current` = today. W119.3 table wins first. Rules file empty (needs >=20 games and a reason).
- Part C: skip counts per reason in RESULT.md; arm path reads no real-money constant; RIDE board 500/150 registered as GG-2008 (orders OFF).
- RESULT: 12_EXPLORATORY/placement/RESULT.md. HYPOTHESIS_DOCTRINE H-EXEC-1/2/3/4 rows updated.

## Findings the window should know
- Team totals fill 5 of 538 at the resting touch (all RIDE). Cross or skip is the direction; unsupported (cells 2-16 games).
- Caps removed 13,237 orders since 11-12; day stake pinned at the $50 base cap 11-14..16. Raised caps no longer bind.
- Box deploys lag a merge by a few minutes; first box read after merge failed with file missing, the fourth worked.

## Not done / open
- Deploy truth showed t4-mlb on box HEAD c2bcbf9e; no t4-mlb decision needed from this block.
- Activation proposal (RESULT.md): keep switch OFF until a supported cell exists; revisit at the 12-01 H-EXEC-4 look.
- GG-2007 (router ERROR skips) overlaps `unrouted` 11,913; not re-derived.
