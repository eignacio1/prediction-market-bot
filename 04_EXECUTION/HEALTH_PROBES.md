# Health probes by season - moved out of CLAUDE.md Step 4 (2026-11-11)

**Last reviewed:** 2026-11-11 (SW-9). Always-on health signals are printed every session by `.claude/hooks/governance_scan.sh`
(DEPLOY TRUTH, SILENT ARMS, RUNTIME / SURFACE BUDGET, LEDGER FIELD INTEGRITY, T4 MLB cycle-log recency). The probes below are the
hand-run ones, kept verbatim from CLAUDE.md with their incident reasoning. **MLB probes apply March to October only** (MLB is idle
until the 2027 season). From a cloud window with no ssh, use the box bridge (`04_EXECUTION/BOX_TASKS/`) instead.

```bash
ssh prediction-market-vps "echo '=== T1 MLB — last 3 runs ===' && grep -E 'players in live MLB|Bets placed today|PIPE-05 (SUMMARY|COMPLETE|ERROR)' /opt/prediction-market-bot/logs/paper_mlb_cron.log 2>/dev/null | tail -12 && echo '=== T4 MLB — systemd ===' && systemctl is-active t4-mlb && echo '=== T1 NBA — last run (off-season: expect 0 games) ===' && grep -E 'players in live|Bets placed|PIPE-0[3-7]|No .* markets available' /opt/prediction-market-bot/logs/paper_early_cron.log /opt/prediction-market-bot/logs/paper_late_cron.log 2>/dev/null | tail -6"
```

**What to look for:** Any run that shows `0 players in live MLB markets` during MLB season (March–October) is a signal failure — treat it as a Q6 concern and do not proceed without diagnosing it. Expected healthy output: ≥1 player matched per run when games are scheduled that day.

**GG-108 correction (2026-07-11):** the NBA command above previously targeted `logs/paper_cron.log`, a filename that no longer exists on the VPS — NBA's single-window cron was split into two windows at some point (`paper_early_cron.log` at 18:00 UTC, `paper_late_cron.log` at 01:30 UTC) and the reference here was never updated. A grep against a nonexistent file returns empty output, which is visually indistinguishable from "0 games today" — so this check had been a silent no-op for NBA specifically, catching nothing, for an unknown number of sessions. Corrected to grep both real files and to also match `No .* markets available` (the actual off-season log line) so a healthy dark day is visibly confirmed rather than merely absent of output. If this file ever grows a third window, update this command again — do not let it drift a second time.

**Semantic oracle checks (added Session 101):** These two lines surface silent pipeline failures immediately. Zero is healthy for both on a normal game day.

```bash
# T1 MLB: fires when games exist but 0 players matched → ticker/name pipeline dead
tail -500 /opt/prediction-market-bot/logs/paper_mlb_cron.log 2>/dev/null | grep -c "SemanticFloorViolation" || echo "0"
# T4 MLB: fires per-evaluation when staleness detected → ESPN or Kalshi data is stale
grep -c "CONTAMINATION_HALT" /opt/prediction-market-bot/logs/audit_mlb_t4.jsonl 2>/dev/null || echo "0"
# T4 MLB staleness, recency-windowed (see GG-085 below — do not threshold the raw payload.staleness_halts counter):
tail -500 /opt/prediction-market-bot/logs/audit_mlb_t4.jsonl 2>/dev/null | grep -c '"failed_checks": \["game_state_fresh"\]' || echo "0"
```

`SemanticFloorViolation` count > 0 in the last 500 log lines (recency-windowed like the staleness probe, GG-309; an all-time count reads a months-old hit as live) = T1 pipeline silence (investigate immediately). `CONTAMINATION_HALT` count > 0 in the audit JSONL is expected at game-end (market_active=False normal).

**Dashboard OOM-restart-loop probe (T-356/GG-118, added 2026-07-21):** GG-118 found `pmbot-web-dashboard.service` can OOM-crash-loop (`Restart=always`/`RestartSec=5`) while `systemctl is-active` reports `active` throughout, since the service re-enters the active state within ~5s of each restart — a plain `is-active` check would not have caught the ~2-day dark-dashboard incident that prompted GG-118's fix. This step had no probe at all for this service before now.

```bash
ssh prediction-market-vps "systemctl show pmbot-web-dashboard.service -p NRestarts,ActiveState,SubState && echo '--- oom-kills, last 24h ---' && journalctl -u pmbot-web-dashboard.service --since '-24 hour' | grep -c oom-kill"
```

**What to look for:** `NRestarts` > 0 or any `oom-kill` count > 0 means the service has crash-looped recently — treat it as a Q6 concern even if `ActiveState=active`/`SubState=running` looks healthy, since that pair is exactly what a mid-loop snapshot shows. Healthy baseline: `NRestarts=0`, 0 oom-kills.

**Alarm condition (corrected 2026-07-05, GG-085 — the prior wording here was itself wrong and never caught anything):** do not grep for `payload.staleness_halts > 0`. That field is a **per-`session_id` cumulative counter** (confirmed via direct inspection of `audit_mlb_t4.jsonl`: it appears only on `CONTAMINATION_HALT` events where `failed_checks` includes `game_state_fresh`, alongside a matching `total_halts`, and only resets when the `t4-mlb` process restarts and a new `session_id` begins) — it is not a per-cycle boolean and does not reset when data freshness recovers. A long-running session that hit even one transient staleness event hours ago will show `staleness_halts > 0` in every subsequent record for the rest of that session's life, even while currently healthy — the documented heuristic would have alarmed permanently after the first true positive and never told you anything new. The real signal is whether a `game_state_fresh` failure occurred **recently** (last few poll cycles), which the `tail -500` command above checks directly by counting fresh occurrences of the failed-check string rather than reading the cumulative counter. Non-zero on that recency-windowed count = ESPN or Kalshi data is stale right now; investigate immediately. A positive `payload.staleness_halts` value alone, with zero recent `game_state_fresh` occurrences, means the session merely has staleness history, not a live problem.

**T4 MLB cycle-log write-recency probe (GG-163/T-429, added 2026-08-07):** every check above this line inspects `systemctl is-active`, T1's own log content, or `audit_mlb_t4.jsonl`'s staleness-halt signal — none of them ever check whether T4's own `t4_mlb_cycle_log.jsonl` is actually still being written. GG-163 was a live demonstration of exactly this blind spot: ESPN's edge began 403-ing T4's game-ID discovery request at 2026-08-04 23:41 UTC, the discovery failure meant the process never reached the evaluation code path that writes cycle-log rows, and `systemctl is-active t4-mlb` reported `active` continuously throughout — the outage ran 43.5h+, spanning a full game night with T1 confirming 21-35 players matched in live MLB markets that same day, before a session doing unrelated work happened to notice the stale file by hand. This probe makes that check structural instead of incidental:

```bash
ssh prediction-market-vps "LAST_TS=\$(tail -1 /opt/prediction-market-bot/logs/t4_mlb_cycle_log.jsonl 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin).get(\"ts\",\"\"))' 2>/dev/null); if [ -z \"\$LAST_TS\" ]; then echo 'T4_CYCLE_LOG: NO ROWS FOUND'; else AGE_S=\$(( \$(date -u +%s) - \$(date -u -d \"\$LAST_TS\" +%s) )); echo \"T4_CYCLE_LOG: last_row=\$LAST_TS age_hours=\$(( AGE_S / 3600 ))\"; fi"
```

**What to look for:** cross-reference `age_hours` against the T1 command above (does today's date fall in MLB season, and did T1 report ≥1 player matched — i.e. were games actually live?). `age_hours` in the high single digits or more while games were live in that window is a signal failure — investigate immediately, and do not let `systemctl is-active`/`ActiveState=active` talk you out of it; GG-163 is direct proof that pairing can be healthy-looking and completely blind at the same time. Idle age spanning an off-day, off-season, or a pregame stretch with no live batter state is expected and not itself a concern — T4 only writes a cycle-log row when there is a live batter state to evaluate.
