# SESSION HANDOFF — 2026-06-11 00:40 UTC (SESSION 45 CLOSE)

**Session:** 45 (2026-06-10, G4 night)
**Closed:** 00:40 UTC Jun 11 — NBA Finals G4 (NYK@SAS, ESPN 401859966) tipping ~00:40 UTC, system live and unattended
**Commits this session:** `b6cedd0`, `7019cc8`, `424698a`, `79d0263`, `b16aa73` + session-close commit — all deployed to VPS (`/opt/prediction-market-bot`)
**Tests:** 817/817

---

## ⚡ NEXT SESSION = POST-G4 INSTITUTIONAL SPRINT

Operator directive (verbatim intent): sprint immediately once game ends through **all post-game resolves / assessments / corrections / deployments**, then the project queue. Run session-start protocol first (mandatory, no exceptions), then execute Phases A→D without waiting for prompts.

### Phase A — Verify the auto resolution chain (first ~15 min)

1. **GHA resolve ran?** `gh run list --workflow=post_game_resolve.yml --limit 2` — scheduled 05:30 UTC. If failed/skipped: Mac fallback cron `post_game_g4_resolve.sh` (16:00 PT Jun 10 = 23:00 UTC entry `0 23 10 6 *` — **G4-date-specific; does NOT cover G5**). If both failed, run resolve manually on VPS.
2. **T1 settled:** VPS `logs/paper_portfolio.json` — 33 G4 positions resolved, new bankroll/cumulative P&L. Pre-G4 baseline: bankroll $876.83 settled / $119.14 after deploy, cumulative P&L −$123.17, 82 resolved.
3. **T4 settled:** `logs/paper_portfolio_t4.json` — pool was $1,539.42 pre-G4. **First night ever with EXIT_MECHANICS_ACTIVE=True** — count exit events (feeds T-152, needs n≥50 cumulative).
4. **Late cron behaved?** 01:30 UTC PIPE-03: must have skipped the 33 open tickers (idempotency) and NOT kill-switched (b6cedd0 + 424698a both deployed pre-cron). Check `logs/audit.jsonl` for ERROR/KILL signatures.
5. **T-139 order-failure rate:** G4 manual run was 0/33 failures (15 resting/18 executed). Check late-cron orders too. G6 Tier 1 gate: ≤5%. G3 had 18/20 503s — G4 is the first post-backoff-fix data (T-138).

### Phase B — Assessments (the night's evidence harvest)

6. **MC postmortem (mandatory):** predicted EV +$152.08, P(profit) 95.3%, P(trip 20% kill) 1.07% (`/tmp/g4/mc_portfolio.py`, N=100k seed 42 — note /tmp may be wiped; methodology in DECISION_LOG SESSION 45 PART 2). Compare to actual. G3's MC missed by $337. Log to MC track record (MONTE_CARLO_PROTOCOL.md).
7. **EXP-018 rerun → Hypothesis C DS RULING (deferral expires now):** rerun at larger n with G4 data; Earl rules Hypothesis C. Deferral logged 2026-06-10 (DECISION_LOG SESSION 45 PART 2).
8. **EXP-017 Part B update (GG-004 — the commercial question):** add G4 resolved bets. Pre-G4: DIRECTIONAL_POSITIVE, n=66, power insufficient. **All P&L reporting now carries "unhaircut paper fills" caveat (GG-022).**
9. **T-152 exit-event empirics:** EXP-019B empirical vs analytic (79.9% correct exits, 0 false) — ±20% tolerance gates ADR-0019 Tier 2.
10. **EXP-019C spread logs → T-153 EXPANDED:** G4 spread data is the input for the fill-realism haircut on ALL G6-facing P&L (GG-022). Start the haircut model if data sufficient.
11. **LL-014 calibration entry:** was G4 the first night with NO new critical bug? Record the answer either way — we have never had a clean night (G1: GG-012 era; G3: Bug H/MC miss; G4 pre-tip: stale-kill).
12. **Drawdown headroom check:** pre-G4 realized P&L −$123.17 → 20% system kill trips if G4 net loss ≥ $76.83. If tripped: it worked as designed — verify halt behavior, then assess.

### Phase C — Corrections + deployments (same-session discipline)

Whatever A/B surfaces: fix → test (`.venv311/bin/pytest tests/`) → commit → push → **VPS deploy without asking** (`ssh root@157.230.91.33 'cd /opt/prediction-market-bot && git pull --ff-only'`). Per LL-014: any shared-state bug → audit EVERY consumer of the field before declaring fixed.

### Phase D — G5 prep + project queue

13. **Series status:** check whether G5 exists (operator expects ≤2 days left in window). If G5 (likely ~Jun 12/13): run `/pregame`; LL-013 cohort coverage check; confirm GHA daily resolve covers it (Mac cron does NOT — G4-date-specific); confirm T4 23:00 UTC cron will launch with current code (no manual restart needed — cron picks up deployed HEAD).
14. **Priority queue** (TODO_NEXT, reordered SESSION 45): T-157 stop-criterion draft (HIGH, ratify cold pre-regular-season) → T-153 haircut (HIGH) → T-158 dark-period plan (HIGH, due ≤1wk after Finals end) → T-156 ADR-0012 amendment + accumulation tests (MED) → T-159 state-machine invariant tests + schema owner (MED) → T-160 root-folder hygiene (LOW).

---

## Strategic Decisions This Session (all in DECISION_LOG already)

| # | Decision | Where logged |
|---|----------|--------------|
| 1 | Fix T1 stale-kill + manual recovery run pre-tip (operator choice) | SESSION 45 entry 1 |
| 2 | Daily-loss semantics gross→net (ADR-0012 amendment registered as T-156) | SESSION 45 PART 2 |
| 3 | Hypothesis C ruling deferred to post-G4 rerun (DS: Earl) | SESSION 45 PART 2 |
| 4 | PDTP assessment ratified as project posture; GG-021/GG-022/LL-014/T-157..T-160 registered; priority queue reordered | SESSION 45 PART 3 |

## G6 Gate Position (per APR-0017, as amended by APR-0019 — NOT the old 30-bet APR-0016 standard)

- T1 resolved: **82** (floor ≥66 ✅) + 33 open G4; T4 resolved: 1,115 (floor ≥50 ✅) — **bet count is NOT the binding constraint** (Invariant 11)
- Game nights: 4 after G4 resolves (G1/G2/G3/G4) — floor is ≥5 → **G5 matters for the slope regression df**
- **Binding blockers:** GG-004 (EXP-017B power), positive cumulative P&L (currently −$123.17, unhaircut), GG-022 haircut, DS sign-off (ADR-0005)

## System State at Close

- **VPS HEAD:** `b16aa73` (+ session-close commit to follow) | T1: 33 open, daily_loss $0.00 | T4: PID 372067, exits ACTIVE, polling | Dashboard: tmux `pmbot-dash` attached in Terminal
- **Known watch items:** T4 process dies at timeout 18000s (~05:00 UTC — after game ends, fine); local `.claude/tmp` had a transient ENOSPC tonight (caused a 3-min T4 outage during restart — re-verify disk before long ssh commands)

## One Thing Pending

**Verify the G4 resolution chain ran, then harvest the evidence (Phase A→B) — Hypothesis C ruling is the first DS decision of the session.**

## Resume Command

```
Session open. Post-G4 sprint — run the session-start protocol, then execute SESSION_HANDOFF_20260611_0040.md Phases A–D.
```
