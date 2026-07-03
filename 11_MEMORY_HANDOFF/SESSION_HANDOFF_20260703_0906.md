# Session Handoff — 2026-07-03T09:06Z

**Trigger:** Operator-initiated (`/session-end`), clean cutover — T-225 fully closed out
**Last commit:** `2331264` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 2293/2293 passing (7 skipped, 1 pre-existing unrelated failure — `test_feature_csv_freshness`, environmental data-staleness, not a regression)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — `t4-mlb` systemd service `active`, confirmed clean restart (session `T4-MLB-F870F834`), all other MLB cron entries running normally
- **Paper bets:** MLB T1/T2/T3 49/30 resolved (G6 count+sign met — EXP-017 + DS sign-off still required for full G6) | MLB T4 13 closed (35 open) | NBA (DARK/FROZEN) 158/30 resolved, historical

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| T4 MLB's `already_fired_game` dedup guard changed from a permanent one-shot-per-ticker block to allow re-entry once the ticker's live state changes | The one-shot block was correct scaffolding for an unproven pipeline; the pipeline is now proven (kill switch drilled at 0.34ms, contamination guard verified, edge math confirmed responsive to real Kalshi price moves). Real backstops now exist (`max_single_event_exposure_usd`, drawdown kill switch, T4 band budget) to carry over-concentration risk instead of the blunt dedup proxy. The T4 alpha thesis is about a *repeated* phenomenon (market latency) — a permanent one-shot cap structurally prevents gathering enough evidence to prove or disprove it. CLAUDE.md Hard Rule 9's ~1,000-eval/game target is evidence-derived, not arbitrary. T-226 (venue coverage) was already resolved favorably, satisfying Earl's one caveat. | DECISION_LOG.md (2026-07-03, two entries: design ruling verbatim + technical implementation rationale) | DS (Earl Ignacio) |
| Re-entry keyed specifically on `(h_so_far, ab_remaining)` rather than a coarser "state changed" flag or a timer-based cooldown | These are the exact two live-state scalars driving `p_t4`'s Binomial computation — keying on them directly (rather than a proxy) ties re-entry eligibility to a real, provable movement in the edge signal itself. | DECISION_LOG.md (2026-07-03, implementation entry) | EL |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| Session-start protocol (docs debt scan, stub scan, governance gap review, operational health check, ARE WE COMPROMISED Q1-Q6) | ✅ Clean — no blocking issues found |
| T-225: surface dedup-policy decision to DS via AskUserQuestion | ✅ Earl ruled "allow re-entry per ticker" |
| `run_t4_mlb_live.py`: `already_fired_game` redesigned `set[str]` → `dict[str, tuple[int,int]]`, re-entry check, `_reconstruct_fired_ticker_states()` (renamed, restart-safe, `entered_at`-sorted) | ✅ Implemented |
| `paper_trader.py`: `open_position()` gained `h_so_far_at_entry`/`ab_remaining_at_entry` optional kwargs, persisted on position dict | ✅ Implemented |
| Verified `_resolve_pool()`/`settle_position()` are `position_id`-keyed, not ticker-keyed — re-entry is architecturally safe | ✅ Confirmed by code read |
| 11 new tests (6 reconstruct-state, 3 re-entry cycle behavior, 2 PaperTrader field persistence) | ✅ All green |
| Full suite run | ✅ 2293 passed / 7 skipped / 1 pre-existing unrelated (baseline 2282 + 11 new, zero regressions) |
| DECISION_LOG.md, TODO_NEXT.md (T-225 RESOLVED), GOVERNANCE_GAP_LOG.md (GG-076 RESOLVED) updated | ✅ Committed |
| Commit, push, VPS deploy + `t4-mlb` restart | ✅ Commit `2331264`, VPS fast-forwarded clean, service restarted and verified active |
| MEMORY_BANK.md, TODO_NEXT.md, PLAN.md session-end navigation artifacts updated | ✅ This turn |

---

## ONE THING PENDING

**Verify the MLB T4 open-position jump is actually the T-225 re-entry policy working as designed.** A live VPS portfolio read at this session's close showed MLB T4 at 35 open positions / 13 closed, up from the 3 open positions recorded in the S113 snapshot before this session's restart. This is directionally consistent with re-entry firing as intended, but has NOT been confirmed as the cause — it could also just be normal accumulation since S113 (several days have passed). Next session should pull `logs/t4_mlb_cycle_log.jsonl` or the audit JSONL (`audit_mlb_t4.jsonl`) and check whether multiple positions share a ticker with distinct `(h_so_far, ab_remaining)` values, which would be direct evidence of re-entry firing correctly. Infrastructure is ready — this is a read-only verification, no code changes needed.

---

## Current Paper Portfolio

(Live VPS read at session close, 2026-07-03 ~07:05 UTC)

- **MLB T1/T2/T3:** bankroll $1,075.88, 3 open, 49 closed, +$100.00 P&L, 0% drawdown. G6 count+sign met (≥30); EXP-017 + DS sign-off still required for full G6.
- **MLB T4 (T4M-PROJ, pool_isolated):** bankroll $1,000.00, 35 open, 13 closed, +$1.59 P&L. See "ONE THING PENDING" above.
- **NBA (DARK/FROZEN, historical):** bankroll $751.10, 0 open, 158 closed, -$248.90 P&L, 24.9% drawdown — adjudicated (GG-034/GG-037), not a live risk signal.

---

## Active Cron / Systemd on VPS (157.230.91.33)

```
PIPE-06pre  16:30 UTC daily  — MLB pregame context
PIPE-05     03:00 UTC daily  — T1 MLB paper bets
PIPE-05.5   19:30 UTC daily  — T2 MLB same-day lineup overlay
PIPE-06     */15 20-23 + */15 0-3 UTC — T3 MLB pre-game signal scan
t4-mlb (systemd, not cron) — T4 MLB live loop, 45-90s cycles while games are live, self-heals to next first pitch when idle
PIPE-05R    06:30 UTC daily  — T1 MLB resolve
PIPE-05FX   22:30 UTC daily  — MLB feature refresh
```

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (**30 resolved paper bets** + positive P&L + EXP-017 + DS sign-off — APR-0016/APR-0019)
3. `run_t4_mlb_live.py` is a live systemd-managed file — any deploy touching it requires `git pull` **and** `systemctl restart t4-mlb`, not just a pull (this session followed that correctly)
4. T-229 (Hard Rule 9 throughput arithmetic reconciliation) is now unblocked by T-225's resolution but is explicitly DS-owned, not a model call
5. NBA and MLB are separate bankroll pools — never conflate NBA's frozen -24.9% drawdown with live MLB risk

---

## ⚙️ DECISION AUDIT

**Step 1:** `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/` → clean, no matches.

**Step 2:**

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `run_t4_mlb_live.py` | N/A (code, not a decisions_logged-tracked doc) | 2 entries (design ruling + implementation rationale) | ✅ |
| `paper_trader.py` | N/A (code) | Covered by the same 2 entries above | ✅ |

Sprint is closed — no `decisions_logged: false` documents were created or modified this session.

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260703_0906.md, confirm 2293 tests, then verify the MLB T4 re-entry hypothesis (see ONE THING PENDING)"
```
