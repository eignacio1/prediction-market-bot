# SESSION HANDOFF — W96.2 (20261030T1645Z)

Status: PARTIAL | B-002 (frozen ride evidence reproduced): NOT DONE, 0 of 13 cells classified; settlement cache complete | branch session/w96-2-close | PRs #383 and #386 merged, CI green (read) | one-line result: the box run cannot finish a full-archive reproduction inside the 900 s task limit, and the NFL regen is missing its pinned input | MEASURE MOVED: PROOF, none. Cells re-run 0 -> 0 of 13; nfl_board_v2 JSONs regenerated 0 -> 0 of 3. Settlement cache 3,573 -> 5,907 of 5,907 events (source: `repro.py fetch` rounds sf1..sf4, `results/*w96_2_sf*.md`).

Stage per factor: none (no factor built).

What happened (details in `12_EXPLORATORY/frozen_evidence_check/results_W96_2.md`):
- Settle fetch finished in four bridge rounds.
- `frozen_repro_window` first returned exit 255 (link dropped, output lost). #386 added a 30 s stderr heartbeat; the retry stayed up and was killed at the 900 s limit, exit 124, no output. `frozen_repro_full` was therefore not attempted.
- `nfl_board_v2_regen_read` (new read-only task, #383) failed with FileNotFoundError: `exp_output/NFL_EVENTS/raw/schedules/schedules_20261020T001136Z.parquet` is not on the box or in this checkout. GG-1471's premise (inputs live on the box) was wrong.
- Part B: no frozen test's look changes from this block, because no number was reproduced or contradicted; EXP-045's pin cannot be verified until its parquet is found. Paragraphs are in the results file.
- Deploy: #383 and #386 deployed by the box timer; `logs/vps_deploy.log`: "t4-mlb restart decision: not_needed", t4-mlb active; only pmbot-web-dashboard restarted.

B-002 state for the window: OPEN, blocked on GG-1520 (run length) and GG-1521 (missing parquet). Suggested next block: a resumable per-series reproduction (one series per task, cached derived rows) or a one-time prefilter file of the target series' pre-start two-sided rows; locate or re-fetch the schedules parquet and compare its sha256 to c57e424c without editing the pin. `ROLLING_BACKLOG.json` not edited.

Operator decisions: none.

```
task_id: T-1520
vision_pillar: PROOF
gap_measure: P1 precursor, frozen ride cells re-run on the full archive (of 13) and nfl_board_v2 JSONs regenerated (of 3)
gap_delta: cells 0 -> 0; JSONs 0 -> 0; settlement cache 3,573 -> 5,907 events (box fetch results 2026-10-30T15:40Z..16:10Z)
pattern_sweep: fixed repro.py subset() writing through a pre-existing symlink (safe_out resolves it outside the fence): checked the other safe_out(...).symlink_to / link-creating callers in 12_EXPLORATORY/frozen_evidence_check, none other found; added a stderr heartbeat only to repro.py run, other long box tasks (frozen_settle_fetch*) already print per round
surface_delta: one read-only box task nfl_board_v2_regen_read added (allowlisted, no cron, no service); no running component added
```
