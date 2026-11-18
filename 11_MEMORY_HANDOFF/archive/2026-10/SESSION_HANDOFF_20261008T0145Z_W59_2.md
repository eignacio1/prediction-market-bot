<!-- session-meta
task_id: W59.2
tier: STANDARD
timestamp: 2026-10-08T02:00:00Z
commit: d69c6ea
one_line_summary: W59.2 done: first-look projection from real schedules (NFL 2026-11-02), release mechanics, one settled-row schema, 1,229/1,229 Kalshi settlement agree; GG-510..515 registered
gg_touched: GG-499, GG-487, GG-510, GG-511, GG-512, GG-513, GG-514, GG-515
adr_touched: none
plan_deliverable_moved: no
-->

# SESSION HANDOFF — W59.2 calibration correctness (2026-10-08 UTC)

**Status: COMPLETE. Nothing left undone in the block.**

| Part | Result |
|---|---|
| A Projection | Rebuilt from real schedules; NFL first look 2026-11-02; NHL n=2,500 not reachable this season; MLB none (2027 schedule unpublished). Verified in real Chromium, before/after screenshots in `RESULTS_SUMMARIES/W59_2_screenshots/`. PR #178 |
| B Release mechanics | Earliest-60 frozen in write-once sha256 manifests; 59 emits nothing, 60 emits verdict, 61 changes nothing; synthetic REPORT in real format. PR #178 |
| C Settled-row truth | `settled_schema.py` is the one reader (NFL/MLB `y`, NHL `outcome`+ledger join). Live Terminal settled count fixed. Raw ledgers untouched; no `settled/` back-fill. PR #181 |
| D Kalshi cross-check | 1,229/1,229 NFL+MLB markets agree (1,100 + 129), 0 void, 0 outcomes changed. NHL not in scope. PR #182 |
| E | CI green and merged for all PRs. VPS at 0aeb81c; t4-mlb NOT restarted (active since 2026-10-07 06:13 UTC; no T4 changes). Dashboard restarted 01:38:30 UTC. |

**Gaps registered (not fixed):** GG-510 ordering key undefined (EXP-037); GG-511 NHL seed unspecified / engine deviation; GG-512 MLB no `p_clim`; GG-513 NBA not in engine; GG-514 NHL n unreachable + NFL date on one slate; GG-515 phone overflow in the calibration header.

**Operator decisions needed:** ratify the ordering key before the NFL look (~2026-11-02) and a NHL seed; decide whether EXP-036's n=2,500 stands given it cannot be reached this season; MLB climatology baseline yes/no.

**Next:** re-run `scripts/calibration_engine.py` weekly to refresh the NFL date.
