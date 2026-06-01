# Next Session Handoff Prompt

**Paste this entire block into the next terminal window to resume.**

---

You are resuming work on the Prediction Market Trading Bot (Compass OS governance framework). This is a solo-operator paper trading system targeting NBA player prop markets on Kalshi/Polymarket. Read the following before doing anything else.

## Step 1 — Read these files immediately (in order)

1. `11_MEMORY_HANDOFF/MEMORY_BANK.md` — 10 anti-context-erosion invariants; these are LAWS
2. `11_MEMORY_HANDOFF/SESSION_HANDOFF_20260530.md` — full state at last session end

Do NOT proceed past Step 1 until both are read.

## Step 2 — Governance scan

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/ 2>/dev/null
```

Report what you find. Pre-existing debt: T-093–T-099 (low priority, known). Flag any NEW debt.

## Step 3 — Confirm build integrity

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
python3 -m pytest tests/ -q
```

Expected: **550 passed**.

## Step 4 — Check paper portfolio and tonight's resolution

```bash
ssh -i ~/.ssh/id_ed25519_droplet root@157.230.91.33 "cat /opt/prediction-market-bot/logs/paper_portfolio.json"
```

**CRITICAL:** Before doing anything else, check whether PIPE-03R (06:00 UTC) resolved the 6 open positions from the SAS vs OKC game (2026-05-30). Look at `closed_positions` count and `bankroll_usd`. If positions resolved and bankroll > $800, drawdown < 20% and PIPE-03 can resume. If bankroll stays at ~$762, drawdown is still 23.78% and PIPE-03 will continue to kill-switch.

## Step 5 — First task

Read `04_EXECUTION/TODO_NEXT.md` → highest priority executable task. Priority order:

1. **T-100 (BLOCKER)** — Fix Bug H: drawdown includes open stakes, not realized losses. Fix is ~3 lines. Requires DS sign-off first (Class A kill switch change). Discuss with operator before deploying.
2. **T-101 (HIGH)** — Fix Bug G: idempotency check failure (3× duplicate positions). Add startup logging to `run_paper_trade.py` to show resolved portfolio path and open_positions count. Diagnose on VPS.
3. **T-070 (BLOCKED by KI-015)** — Paper bet accumulation (0/30). Blocked until Bug H fixed or positions resolve favorably.
4. **T-077** — Polymarket KYC (**operator action required:** go to polymarket.com → KYC → API key → set `POLYMARKET_API_KEY` in `.env` → run `RUNBOOK_polymarket-activation.md`)
5. **T-091** — C7 P&L monitoring alert (WARNING at -$50; L2 at -$100; requires DS threshold sign-off first)

---

## Key invariants (do not lose these)

1. **arb/ folder = REFERENCE ONLY** — gate is APR-0010 (not signed). No arb code from that folder is active.
2. **No real capital until G6** (ADR-0005 + DS sign-off). Paper trading only.
3. **ADRs are immutable.** Superseding ADR required for any change.
4. **G6 threshold = 30 resolved paper bets with positive P&L** (APR-0016). NOT 50.
5. **FEATURE_VERSION = 1.2.0** — NOT 1.3.0. v1.3.0 was built but HYP-006 FALSIFIED it (EXP-012; delta_vs_v12 = -7e-06). F-039/F-040 dropped. TeamStatsStore is reference-only.
6. **T1 is the only ACTIVE execution band.** T2/T3 are SKELETON (signals logged; bets do not execute). T4/T5 BLOCKED Phase 8+.
7. **band_status is machine-enforced** — `BAND_REGISTRY.validate()` runs at both PIPE-02 and PIPE-03 startup.
8. **T-072 model refresh is REQUIRED before 2026-27 paper trading** (KI-013; model will be 5+ months stale at season open).
9. **Kill switch ≤60s** (NFR-03). Hard limits: $500/bet, $1,000/day, 20% drawdown trigger.
10. **No task block starts without `/checkpoint` for the block just completed** (MEMORY_BANK invariant #10).
11. **$270.76 bankroll in MEMORY.md = OLD Kalshi NBA Trading System — not this project.** This project's bankroll is $762.16 (from $1,000) with 6 open positions.
12. **Bug H fix is Class A (kill switch behavior)** — do not deploy without DS sign-off even though the fix is trivial.

---

## Current system state (as of 2026-05-30)

| Field | Value |
|-------|-------|
| Phase | 6/7 ACTIVE |
| VPS | 157.230.91.33 — cron running |
| Tests | 550/550 passing |
| Paper bets | 0 resolved / 6 open (Fox YES ×3 + SGA NO ×3, game 2026-05-30) |
| Bankroll | $762.16 (initial $1,000) — $237.84 in open stakes |
| Drawdown | 23.78% (all open stakes) — exceeds 20% kill switch → PIPE-03 halted |
| Experiments | 16/16 complete |
| Hypotheses | 9/9 resolved (5 confirmed, 4 falsified) |
| Capital | NO live capital — paper only |
| Model | v1-28483b21; Brier 0.2461; EV +$0.0958/bet |
| FEATURE_VERSION | 1.2.0 (78 features: 31 quant + 47 qual) |
| Next milestone | Fix KI-015 (Bug H) → resume paper bets → G6 (30 bets + positive P&L) |

**VPS cron schedule:**
```
21:30 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (KILL_SWITCH until KI-015 resolved)
01:30 UTC  — PIPE-03 late (KILL_SWITCH until KI-015 resolved)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py) — will attempt to resolve today's 6 positions
```

**Connectivity:** Any non-work network passes Kalshi WAF. Work wifi blocks outbound (strict security policy).

---

## What was completed last session (2026-05-30)

- T3 CT scan completed — 3 consecutive clean scans (prior session carry-forward)
- Bugs C, D, F + feature vector ordering (PIPE-02, PIPE-03) — all 5 fixes deployed to VPS
- 550/550 tests passing
- KI-014 (idempotency failure) and KI-015 (drawdown includes open stakes) newly discovered and registered
- T-100 and T-101 registered in TODO_NEXT.md
- All handoff docs updated (SESSION_HANDOFF_20260530, MEMORY_BANK, KNOWN_ISSUES, CHANGELOG, TODO_NEXT, NEXT_SESSION_PROMPT, auto-memory)

**Bugs C/D/F/ordering are DONE. Bugs G/H are OPEN.**
