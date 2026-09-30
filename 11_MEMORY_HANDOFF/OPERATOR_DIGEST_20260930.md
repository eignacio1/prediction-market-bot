# Operator Digest — 2026-09-30

- Ledger saves are now crash-safe: a crash mid-save can no longer leave a half-written ledger.
- Every bet currently rewrites the whole ledger file. Fine at today's volume, too slow for a burst of hundreds of bets. A fix is proposed (not approved, not built).
- New rule added: every bet must name its model. The live bot doesn't yet, so this is held back until it is updated. Nothing was deployed or changed in production.
- Still zero real money at risk.
