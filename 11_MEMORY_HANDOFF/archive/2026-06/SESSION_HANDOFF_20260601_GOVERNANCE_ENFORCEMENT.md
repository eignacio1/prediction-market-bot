# Session Handoff — 2026-06-01 (Governance Enforcement + Registration Sprint)

**Trigger:** Context window approaching limit — operator-initiated handoff  
**Prior handoff:** SESSION_HANDOFF_20260601_ADR0006.md  
**Session type:** Governance + registration — no code changes; watchdog/enforcement infrastructure built

---

## What Happened This Session

This session had three blocks:

**Block 1 — Watchdog Rewrite:**  
Identified that ARE WE COMPROMISED? was functionally closed-loop — models could read documents and confirm clean without running a single command. The watchdog was rewritten from scratch:
- Adversarial mandate added: "your job is to find something wrong, not confirm clean"
- Q1–Q5: each now requires pasting command output; asserting clean without output is an explicit failure
- Q3: attribution note — count gate was caught by Earl, not a model; capability boundary explicit
- Q6 added: "What would you tell Earl if you had 60 seconds and something was quietly wrong?" — cannot be answered from documentation

**Block 2 — CLAUDE.md Created (was entirely missing):**  
Discovered that no CLAUDE.md existed in the project root. This was a critical governance gap — Claude Code reads CLAUDE.md at session start, but without it every session started without enforcement. Created `CLAUDE.md` with:
- Intent preamble: people who trust Earl, standard is safe/correct/no corners cut
- Holistic project overview (added this session): what the bot is, pipeline flow, execution bands, venue strategy, research record, gate structure, active risk register, what is NOT active, current bankroll
- Full mandatory session-start protocol (Steps 1–3)
- ARE WE COMPROMISED? Q1–Q6 with command outputs required
- Q2 stub baseline as of 2026-06-01 (5 known stubs)
- Q6 standing concern: has EXP-017 been run?
- Hard rules (non-negotiable)

**Block 3 — Enforcement Hook Created:**  
`UserPromptSubmit` hook created to fire before every model response:
- `.claude/settings.json` — hook configuration
- `.claude/hooks/governance_scan.sh` — Python stub scan + open gaps grep + hard limits snapshot + portfolio state
- Confirmed working: new terminal window test showed hook firing at session start

**Block 4 — CLAUDE.md Holistic Project Overview + Framing Correction:**  
Added "What This Project Is" section to CLAUDE.md. First version was too session-specific (bankroll, experiment tables, task IDs, 0/30 progress, specific known issue IDs) — all of which become stale. Revised to be a strategic, timeless document:
- Corrected framing: **this is a prediction markets bot, not an NBA bot.** NBA is the first sport. Architecture is sport-agnostic by design — C1/C2 are sport-specific; C4–C8 require no changes for new sports.
- Added "Adding a new sport" section — describes what the correct architectural response to expansion looks like (new C1, new C2, new C3 model, new market_mapper entry; nothing else should change)
- Added "The commercial validation gap" — names GG-004 as what to check; does not embed specific experiment results or progress numbers that will rot
- Gate structure described conceptually — no current-progress numbers (those live in MEMORY_BANK.md)
- Removed: bankroll, experiment results table, specific task IDs, risk register mirror, active portfolio state
- CLAUDE.md explicitly defers state to MEMORY_BANK.md — "CLAUDE.md does not track state"

**Block 5 — Registration Sprint (from terminal window convergence):**  
Two terminal windows (opened to test ARE WE COMPROMISED?) surfaced findings that were then registered:

| Artifact | Change |
|----------|--------|
| `10_INFRA_OPERATIONS/KNOWN_ISSUES.md` | KI-011 escalated MEDIUM→HIGH (injury blindness = largest fake alpha); KI-017 NEW (mip=0.50 vs Kalshi prices); KI-018 NEW (zombie daily loss); KI-019 NEW (Polymarket tag) |
| `03_DECISIONS/GOVERNANCE_GAP_LOG.md` | GG-004 NEW OPEN (EV benchmark gap survived all 16 experiments + all gate reviews) |
| `03_DECISIONS/OPEN_QUESTIONS.md` | OQ-023 NEW: "Does the model beat actual Kalshi market prices?" Gate: G6 |
| `05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/EXP-017_ev-vs-market-price.md` | NEW: full experiment design; edge = model_p - kalshi_mid_price; injury control run required; success criteria |
| `04_EXECUTION/TODO_NEXT.md` | T-105/106/107/108 registered; T-108 marked complete |
| `src/prediction_market_bot/c4_risk_engine/risk.py` | `max_daily_loss_usd` comment updated with KI-018 reference |
| `CLAUDE.md` | Q2 stub baseline (5 known stubs) + Q6 standing concern (EXP-017) |
| `11_MEMORY_HANDOFF/MEMORY_BANK.md` | Active risks section updated; session-start protocol now canonical |

---

## Critical Attribution Record

**The count gate failure (GG-001/ADR-0006) was caught by Earl, not by a model.** The model executed the fix. This distinction is now explicit in MEMORY_BANK.md Q3 and CLAUDE.md capability boundary statement. Do not imply model discovery in any artifact.

The capability boundary: models can verify, hunt, and surface. The operator makes architectural judgments. This session established that explicitly.

---

## Intent Statement (Read Before Any Work)

Earl is building this bot for friends who trust him. They are not engineers. They cannot audit what they've been given. The standard is safe, correct, no corners cut. The purpose of every governance artifact — CLAUDE.md, ARE WE COMPROMISED?, hooks, GOVERNANCE_GAP_LOG — is to hold that standard when Earl isn't looking.

**The "big issue" identified this session:** Intent misalignment. Models complete tasks. Earl is building something he wants to win. The gap is that models optimize for task completion, not for the bot being good at its job. Every session should ask: does this work make the bot better at placing profitable bets? Not just: did I complete what was requested.

---

## Test Results

No code changes this session. Test count unchanged: **548/548 passing.**

---

## Current System State

**Phase:** 6/7 ACTIVE  
**Tests:** 548/548 passing  
**Capital:** NO live capital — paper trading only  
**VPS:** 157.230.91.33 — cron running; PIPE-03 operational  
**Kill switch:** COLD — 0.00% realized drawdown  
**G6 progress:** 0/30 resolved bets  
**ADRs accepted:** 6 (ADR-0001/002/003/004/006/007)

**Portfolio (2026-06-01):**

| # | Player | Direction | Size | Game date |
|---|--------|-----------|------|-----------|
| 1 | De'Aaron Fox | YES | $56.55 | 2026-05-30 (pending resolution) |
| 2 | Shai Gilgeous-Alexander | NO | $7.18 | 2026-05-30 (pending resolution) |
| 3 | De'Aaron Fox | YES | $56.12 | 2026-05-30 (pending resolution) |
| 4 | Shai Gilgeous-Alexander | NO | $42.00 | 2026-05-30 (pending resolution) |
| 5 | De'Aaron Fox | YES | $41.39 | 2026-05-30 (pending resolution) |
| 6 | Shai Gilgeous-Alexander | NO | $34.58 | 2026-05-30 (pending resolution) |
| 7 | Karl-Anthony Towns | YES | $29.28 | 2026-06-03 (Finals G1) |
| 8 | OG Anunoby | NO | $38.43 | 2026-06-03 (Finals G1) |
| 9 | Jalen Brunson | NO | $11.05 | 2026-06-03 (Finals G1) |

Bankroll: $683.41 | Realized PnL: $0.00 | Drawdown: 0.00%  
SAS/OKC positions (1–6): pending nba_api resolution lag — should resolve 1–3 days after 2026-05-30  
Finals G1 positions (7–9): game Jun 3; confirm PIPE-03 fires on schedule

---

## ARE WE COMPROMISED? — State at Session Close

1. **Hard limits calibrated to current system?** YES — exposure-based limits unchanged; count gate deleted (ADR-0006); KI-018 documented (zombie daily loss at current bankroll)
2. **Stubs current?** 5 known stubs — run_exp001.py:681 (LOW), run_t2_sameday.py:112/130 (LOW now/HIGH at T2 activation), venue_adapter.py:158 (design comment), venue_adapter.py:251 KI-019 MEDIUM. No new stubs added this session.
3. **Architecture coherent?** YES — no architectural changes this session
4. **Interface evolution?** No interface changes this session
5. **Decision traceability?** All thresholds traceable; KI-018 comment added to risk.py
6. **What am I worried about?** EXP-017 is still not run. Until it is, every EV figure in this project is against a coin flip, not an informed market. The bot could be profitable against random and unprofitable against Kalshi. This is the highest-priority research action and it's blocked on operator action (check Kalshi API for historical prices endpoint).

---

## Open Governance Gaps

| ID | Status | What it is |
|----|--------|-----------|
| GG-004 | OPEN | EV benchmark gap — EXP-017 required; blocks G6 confidence |

---

## Next Session Priority Queue

| Priority | Task | Notes |
|----------|------|-------|
| 1 | Monitor SAS/OKC resolution (1–6) | `cat /opt/prediction-market-bot/logs/paper_portfolio.json \| python3 -c "import json,sys; d=json.load(sys.stdin); [print(p['player_name'], p['status']) for p in d['open_positions']]"` |
| 2 | **T-105 — Operator action: check Kalshi API historical prices** | `GET /trade-api/v2/markets` with date filters; needed to unblock EXP-017 (GG-004 blocker) |
| 3 | Finals G1 (Jun 3) — confirm PIPE-03 fires; KAT YES / OG NO / Brunson NO | Check cron ran; verify positions in portfolio |
| 4 | T-106 — Fix stale T2 activation gate | FEATURE_VERSION 1.3.0 falsified by EXP-012; gate must be rewritten; DS sign-off required |
| 5 | T-107 — Confirm Polymarket NBA tag before T-077 activates | KI-019; wrong tag = silent empty return |
| 6 | T-091 — C7 paper P&L monitoring alert | KI-012; WARNING -$50, L2 -$100; DS threshold sign-off |
| 7 | T-104 — File bug report for broken context window flags | github.com/anthropics/claude-code/issues |
| 8 | T-077 — Polymarket KYC (operator action) | polymarket.com → KYC → API key → .env |

---

## How to Open This Project in a New Terminal

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets" && claude
```

Or use alias `pmbot` if configured. Opening from the project directory ensures CLAUDE.md is loaded and the UserPromptSubmit hook fires before the first response.

---

## Strategic Decisions This Session

| Decision | Rationale | Reference |
|----------|-----------|-----------|
| ARE WE COMPROMISED? rewritten to require command output, adversarial mandate | Closed-loop self-confirmation was the root failure — models reading docs and asserting clean without evidence. Adversarial + command-required addresses both vectors. | MEMORY_BANK.md ARE WE COMPROMISED? section |
| CLAUDE.md created as mandatory session-start enforcement | Model-level governance gap — without CLAUDE.md, every session started cold with no context, no mandate, and no protocol. Hook as backup. | CLAUDE.md (created 2026-06-01) |
| Holistic project overview added to CLAUDE.md | A model opening this project cold has no idea what it is, how the pipeline works, or what state it's in. The governance protocol is meaningless if the model doesn't understand the system it's governing. | CLAUDE.md "What This Project Is" section |
| KI-017/GG-004 registered as G6 blocker | EXP-017 is now required before G6 confidence can be claimed — not because paper bets aren't accumulating, but because the commercial benchmark has never been tested against real prices. | KI-017, GG-004, OQ-023, EXP-017 |
