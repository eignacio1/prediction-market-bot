# Operator Digest — 2026-08-15

- T-452 (auto): T-452: session-end.md now has a hard budget (<=10% ctx/<=10min), DECISION_LOG no-Edit rule, truncation path; GG-182 registered.

---

## T-451/GG-181 — T4 MLB was silently dead for ~15 hours; it's fixed and confirmed live.

The bot's actively-trading system (T4, the one that watches live games and bets in real time) stopped evaluating games sometime after midnight UTC, but the health checks all said "running fine" — a variant of a blind spot we'd hit once before (GG-163) and had already built alarms for. This time the failure was subtler: the process itself never crashed, it just quietly stopped picking up the day's game data after a routine midnight file-rollover, so nothing paged.

Root cause: a one-time "load today's games" check that only ever fired once per process lifetime, instead of re-checking whenever a newer file showed up. Fixed, tested (2864 tests still pass), deployed, and I pulled a live row straight off the server afterward showing it correctly evaluating an actual STL@CHC game in progress — not just "service is up," but "it is doing its job right now."

No money at risk during the gap — paper trading only. Nothing else changed: no bet sizing, no risk limits touched.
