# Operator Digest — 2026-08-15

- T-452 (auto): T-452: session-end.md now has a hard budget (<=10% ctx/<=10min), DECISION_LOG no-Edit rule, truncation path; GG-182 registered.

---

## T-451/GG-181 — T4 MLB was silently dead for ~15 hours; it's fixed and confirmed live.

The bot's actively-trading system (T4, the one that watches live games and bets in real time) stopped evaluating games sometime after midnight UTC, but the health checks all said "running fine" — a variant of a blind spot we'd hit once before (GG-163) and had already built alarms for. This time the failure was subtler: the process itself never crashed, it just quietly stopped picking up the day's game data after a routine midnight file-rollover, so nothing paged.

Root cause: a one-time "load today's games" check that only ever fired once per process lifetime, instead of re-checking whenever a newer file showed up. Fixed, tested (2864 tests still pass), deployed, and I pulled a live row straight off the server afterward showing it correctly evaluating an actual STL@CHC game in progress — not just "service is up," but "it is doing its job right now."

No money at risk during the gap — paper trading only. Nothing else changed: no bet sizing, no risk limits touched.
**T-453 (STANDARD):**

**What changed today, in one paragraph:** The bot's internal map of "which sport bets we could ever place, in which time window" — one cell today, currently in use (baseball hit props) — got extended so it can track, per cell, whether we have enough sample data to trust it yet, and whether that cell has been shut off for safety reasons. Right now this is just plumbing sitting unused — nothing changed about how the bot actually decides to bet or stop betting today.

**What this means for your money:** No change — still zero real money at risk, same as every day until the gate clears. This session touched none of the code that sizes bets or opens/closes them.

**Does anything need your decision right now?** No — nothing needs you today.

**Anything that worried the session, even if not urgent:** One thing to flag: the new "shut off a cell for safety" tracking isn't actually wired into the bot's real kill switch yet — it's built but not connected. That's fine while we only trade one cell, but it needs to get connected before we ever turn on a second one. Logged as a tracked follow-up (GG-183/T-454), not forgotten. Separately, the automated health check flagged that the live-game data feed for in-game baseball bets looked stale again during this session's close-out — that's a known, already-being-worked issue from a prior session, not new.
- T-455 (auto): T-455 lands GG-182 assertion — session_end_timer.sh (wall-clock+wordcheck), wired into session-end.md
