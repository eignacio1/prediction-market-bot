# ADR-0008: Kalshi Demo Order Execution — Write-Capable Venue Integration

**Status:** ACCEPTED — 2026-05-31  
**Decision makers:** DS (Earl Ignacio)  
**Supersedes:** Extends ADR-0003 (adds write capability; read-only scope in ADR-0003 remains for market data)  
**Superseded by:** —  
**Related:** ADR-0003 (venue protocol), ADR-0004 (model governance), APR-0016 (G6 evidence gate)

---

## Context

The system was built through G5 with paper trading implemented as a local-only ledger (`paper_portfolio.json`). Orders were never submitted to any venue. The commercial validation goal (G6) requires 30 resolved paper bets, but those bets must be externally verifiable — not just internally asserted. Submitting orders to Kalshi's demo environment provides:

1. External confirmation that the bot's forecast → sizing → order chain works end-to-end
2. Real Kalshi demo account balance as a secondary validation of P&L (in addition to local ledger)
3. Operational readiness evidence: the same code path used in paper trading will be used in live trading, just with a different account key

The missing infrastructure was RSA request signing. Kalshi's v2 API requires RSA-SHA256 signed requests for all authenticated endpoints (portfolio balance, order submission). This was identified as KI-020 on 2026-05-31.

---

## Decision

**Add write-capable Kalshi integration to the execution layer, scoped to demo account during paper trading phase.**

Specifically:

1. **RSA signing layer** added to `KalshiMarketClient` — `_auth_headers()`, `_sign_request()`, `_load_private_key()` utilities. Signing uses RSA-PSS (PS256) with SHA-256 and MAX_LENGTH salt over `timestamp_ms + METHOD + path`. PKCS1v15 is rejected by Kalshi v2.

2. **New public methods** on `KalshiMarketClient`:
   - `get_balance()` — fetches portfolio balance via `GET /portfolio/balance`
   - `submit_order()` — submits limit order via `POST /portfolio/orders`; returns `KalshiOrder` dataclass

3. **`PaperTrader` updated** — accepts optional `kalshi_client` parameter. If client has a loaded RSA key, every `open_position()` call submits a real order to Kalshi. If Kalshi order fails, position is still recorded locally (degraded mode — local ledger remains authoritative).

4. **`run_paper_trade.py` updated** — loads `KalshiMarketClient.from_env()` at startup. Prints mode: `"LIVE ORDERS (demo)"` if RSA key is loaded, `"local-only"` if not.

5. **Order sizing**: `contracts = floor(size_usd / price_per_contract)`. Minimum 1 contract. Limit orders at mid-price.

---

## Environment variables required

| Variable | Purpose | Required for |
|----------|---------|--------------|
| `VENUE_API_KEY` | Kalshi API key ID (already in `.env`) | All Kalshi auth |
| `VENUE_PRIVATE_KEY_PATH` | Absolute path to RSA private key `.pem` | Order submission |

`VENUE_PRIVATE_KEY_PATH` must point to a file **outside VCS** (NFR-05). The private key must be uploaded to the Kalshi dashboard (Settings → API Keys) to activate.

---

## Governance constraints

- **ENV guard preserved**: `BOT_ENV=paper` still required. Live order submission path not yet wired.
- **Local ledger is authoritative**: `paper_portfolio.json` is the G6 evidence source. Kalshi demo balance is a confirmation, not a replacement.
- **Degraded mode**: if Kalshi order fails, local position is recorded and `kalshi_order_status = "failed: <reason>"`. The bot does not halt. This is intentional — the kill switch governs risk, not venue connectivity.
- **Demo account only**: `VENUE_API_KEY` must be the demo account key. Live account key must NOT be used until G6 is formally cleared (ADR-0005 signed, APR-0016 satisfied).
- **RSA key never in VCS**: enforced by `.gitignore` pattern `*.pem`. NFR-05 compliance.
- **Cryptography package**: `pip install cryptography` required on both local and VPS environments.

---

## Rollback

If Kalshi demo order submission causes unexpected behavior:
1. Remove or unset `VENUE_PRIVATE_KEY_PATH` from `.env`
2. Bot reverts to local-only mode automatically — no code change required
3. All prior paper positions remain valid in `paper_portfolio.json`

---

## G6 implications

Paper bets placed after this ADR have two-level confirmation:
- Local `paper_portfolio.json` (existing G6 evidence)
- Kalshi demo order ID recorded in each position (new external confirmation)

This does NOT change the G6 gate criteria (30 resolved bets, positive P&L, ADR-0005). It strengthens the evidence quality.
