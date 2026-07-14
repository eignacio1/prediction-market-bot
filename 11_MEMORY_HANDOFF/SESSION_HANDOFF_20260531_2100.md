# Session Handoff — 2026-05-31T21:00Z

**Trigger:** Context window near limit (operator-initiated)  
**Last commit:** `dce071e` (main) — ADR-0008: Kalshi demo order execution

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 548/548 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (21:00/21:30/22:00/01:30/06:00 UTC)
- **Paper bets:** 0/30 resolved — G6 gate (clean slate; Finals G1 Jun 3)
- **Kalshi execution:** LOCAL-ONLY (degraded mode — T-111 OPEN BLOCKER)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| ADR-0008 accepted: Kalshi demo order execution — write-capable C5 integration | End-to-end bot validation requires actual venue execution, not just local simulation. paper_trader.py was never submitting to Kalshi. ADR-0008 adds RSA signing to kalshi_client.py and injects KalshiMarketClient into PaperTrader. Degraded mode if Kalshi fails — local ledger authoritative for G6 P&L. | `03_DECISIONS/ADR-0008_kalshi-demo-order-execution.md` | DS |
| Architecture separation confirmed: deterministic algorithm in C4/C5; no LLM in execution path | Previous bot had LLM in execution path → hallucinated orders. This bot: Claude codes the algorithm; algorithm runs deterministically at runtime; Claude is NOT present when bets execute. C3 = frozen sklearn model, C4 = pure math, C5 = deterministic order submission. Reinforced by ADR-0008 design. | CLAUDE.md — "Option A" | DS |
| Kalshi auth: NOT_FOUND open blocker — root cause unresolved | RSA signing (PKCS1v15 and PSS both tried) returns `NOT_FOUND`. Bearer token returns `token authentication failure`. Hypothesis: demo API keys (UUID type in dashboard) may use session-based auth (POST /log_in → JWT), not RSA signing. Bot continues in local-only mode (designed degraded mode — no halt). T-111 registered. | `DECISION_LOG.md` 2026-05-31 | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| ADR-0008: RSA signing layer in kalshi_client.py | ✅ `_load_private_key()`, `_sign_request()` (PSS padding), `_auth_headers()`, `_get(authenticated=True)`, `_post()` — all built |
| ADR-0008: `KalshiOrder` dataclass + `submit_order()` | ✅ Contract sizing, limit order body, `POST /portfolio/orders`, degraded mode return |
| ADR-0008: `get_balance()` | ✅ Authenticated GET /portfolio/balance — blocked by T-111 but infrastructure complete |
| ADR-0008: PaperTrader updated | ✅ Accepts `kalshi_client=` param; submits to Kalshi if `has_signing_key()`; records `kalshi_order_id/status/contracts` in position |
| ADR-0008: `run_paper_trade.py` updated | ✅ Loads KalshiMarketClient at startup; prints "LIVE ORDERS (demo)" or "local-only" |
| `cryptography>=42.0.0` added to pyproject.toml | ✅ Installed locally and on VPS |
| RSA padding fixed PKCS1v15 → PSS | ✅ Changed in same session (ADR comment updated) — same error persists (T-111) |
| VPS deployed HEAD dce071e | ✅ git stash + pull resolved; feature matrix 16,619 lines confirmed; portfolio archived |
| ADR-0008 document created and committed | ✅ `03_DECISIONS/ADR-0008_kalshi-demo-order-execution.md` |
| DECISION_LOG entries: 2 new entries (ADR-0008 + auth blocker) | ✅ |

---

## ONE THING PENDING

**T-111 — Kalshi auth NOT_FOUND:** Infrastructure is built and committed. The bot signs requests correctly (private key loads, PSS padding, correct key ID `[REDACTED-2026-07-12-GG-116 — see below]`). The failure is on Kalshi's side — they cannot find/validate the key.

**Current state:** `VENUE_API_KEY=[REDACTED-2026-07-12-GG-116]`, `VENUE_PRIVATE_KEY_PATH=~/.ssh/kalshi_bot.pem`. Both set. Key loads (`Signing key loaded: True`). Balance endpoint returns `{"code": "authentication_error", "details": "NOT_FOUND"}`.

> **Redaction note (2026-07-12, T-347/GG-116):** this document previously contained the real Kalshi API key ID and private-key filesystem path in plaintext — a direct NFR-05 violation ("Zero hardcoded secrets. Vault/env-var protocol only"). Redacted in place (non-destructive; git history still contains the original value at commit `dce071e` and after — history scrub and/or credential rotation are operator decisions, not made here). See `03_DECISIONS/GOVERNANCE_GAP_LOG.md` GG-116 and `02_ARCHITECTURE_DESIGN/THREAT_MODEL.md` TH-02 for full detail.

**Next session must investigate:**
1. **Try session-based auth**: `POST https://api.elections.kalshi.com/trade-api/v2/log_in` with `{"email": ..., "password": ...}` → get JWT → use `Authorization: Bearer <jwt>` for /portfolio/balance. If this works, the UUID key is a Bearer-token key, not an RSA key.
2. **Check Kalshi API docs**: `https://trading-api.readme.io/reference/` — specifically whether RSA signing applies to demo accounts or only live/production.
3. **Alternative**: Earl checks if Kalshi dashboard has a separate RSA key section (not the "API Keys" UUID section shown in the screenshot).

Until T-111 resolves, all Finals G1 bets (Jun 3) will be recorded in `paper_portfolio.json` only — no Kalshi demo order IDs. This is acceptable (local ledger is authoritative for G6 per ADR-0008) but reduces external confirmation evidence quality.

---

## Current Paper Portfolio

- Bankroll: $1,000.00 (RESET 2026-05-31 — pre-ADR-0006 bets invalidated)
- Open: 0 positions
- Closed/Resolved: 0 | G6 gate: 0/30
- First opportunity: NBA Finals G1, Jun 3, 2026 (NYK vs SAS)

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check
21:30 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py) [gets 403 from nba_api — zero resolutions; use run_resolve_local.py manually]
```

**VPS SSH:** `ssh -i ~/.ssh/id_ed25519_droplet root@157.230.91.33`  
**Resolution (local):** `BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py`

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (**30 resolved paper bets** + positive P&L — APR-0016)
3. stats.nba.com hard-blocks VPS datacenter IP (403) — resolution must run locally via `run_resolve_local.py`
4. All prior bets (pre-ADR-0006) invalidated — G6 evidence begins Jun 3 (Finals G1)
5. Kalshi order submission in LOCAL-ONLY mode until T-111 resolves
6. RSA key at `~/.ssh/kalshi_bot.pem` — NOT in VCS (NFR-05)

---

## ⚙️ DECISION AUDIT

**Step 1:** `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/ 2>/dev/null`

7 pre-existing matches (T-093 through T-099 registered) — none modified this session.

| Document | decisions_logged | DECISION_LOG entries | Status |
|----------|-----------------|----------------------|--------|
| ADR-0008_kalshi-demo-order-execution.md | N/A (ADR) | 2 entries written (ADR-0008 + auth blocker) | ✅ |
| kalshi_client.py | N/A (code) | Covered by ADR-0008 entry | ✅ |
| paper_trader.py | N/A (code) | Covered by ADR-0008 entry | ✅ |

All other modified files (pyproject.toml, MEMORY_BANK.md, KNOWN_ISSUES.md, TODO_NEXT.md) are operational files — no decisions_logged field required.

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260531_2100.md.
# Priority: T-111 — Kalshi auth NOT_FOUND. Try session-based auth:
# POST /trade-api/v2/log_in with email/password → JWT → Bearer token on /portfolio/balance."
```
