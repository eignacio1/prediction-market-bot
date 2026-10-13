# SESSION HANDOFF W69.1 (replaces earlier BLOCKED version)

Status: PARTIAL | branch session/20261012T235158Z-w69-1-forward-readback | PR #234 merged (squash), CI on PR green; main-branch run 38327393913 has 6 failures in other sessions' files (NBA-minutes exploratory isolation x2, governance-scan hook tests x4: #233/#235), none touch this PR.
Result: box activated and read back; first forward-test numbers collected; GG-587 closed on read-back; GG-586 merged but not live-read-back.
vision_pillar: EXECUTION | gap_measure: forward-test E1/E2/E3 readable per book/sport/arm from the box | gap_delta: treatment-arm numbers now exist for paper/MLB, shadow/MLB, shadow/NFL; control arm for shadow cells exists in code; turn-off no longer dirties the tree.
MEASURE MOVED: yes (first on-box numbers). Order behaviour changed only for shadow control arm (demo, switches currently OFF).

## What happened
- Crontab fixed (NHL staked runner + demo_fill.env loading on NHL/NBA lines, 11:25 report line); backup /root/crontab.bak.w69_1.
- My manual report run tripped ADR-0072 turn-off (cancel_fail_rate 1.0 on a 10-minute-old UTC day). Cause: cancel returns 404 on already-terminal orders and the report counts that as failure (GG-596). Both switches are now OFF through the untracked override on the VPS; tracked demo_fill.env restored clean.
- GG-586/587 implemented, tested (72 related tests), merged, deployed (VPS HEAD f9ab37de).

## Operator decisions needed
1. Re-arm the demo switches? Delete /opt/prediction-market-bot/deploy/demo_fill.override.env on the VPS. Recommended only after GG-596 is fixed, otherwise the report re-trips and turns them off again on the next 11:25 run.
2. GG-596 (classify 404 as already_terminal) is the next undone part; GG-586/570/571 stay OPEN until a live read-back with switches on.
3. Six failing tests on main from #233/#235 belong to those sessions.

## Not done
Governance-scan line and /project panel comparison with report numbers.
