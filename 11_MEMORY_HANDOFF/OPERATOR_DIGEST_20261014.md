# Operator Digest — 2026-10-14 (W72.3, PLUMBING)

- The server now tells you the truth about deploys. A failed deploy, a stuck restart, or stale running code raises an alarm. It shows in the session scan and the dashboard, and the daily health check reports it.
- The old health check was red for the wrong reasons. I rewrote it for today's setup. It only goes red on a real fault.
- I checked the trade ledger and the data. I found no corruption and no look-ahead. Tests prove that the MLB and NFL quarterback features never see the game they predict.
- Two small data-quality gaps are logged and unfixed. GG-690: 3,495 older MLB rows have no market type, so the cell-level checks skip them. GG-691: the ledger check wrongly flags 16 cancelled bets.
- Nothing needs your decision. Next up: fix GG-690 and GG-691, then the Wave 72 punch list.

### W72.2 — Ledger safety (STANDARD, PLUMBING)
Paper ledgers now write atomically; an unreadable ledger is quarantined and the bot halts rather than starting from empty. `/vps` is retired (read-only `/deploy-audit` replaces it). Box `.env` is mode 600, backup deleted, key confirmed DEMO by a read-only GET. Follow-ups #250 (fast tests, healthcheck) and #251 (GG-680, other state writers) merged. GG-660/662/663/664/672 closed: t4-mlb restarted 02:53Z onto the new code and was read back. No pillar moved.
