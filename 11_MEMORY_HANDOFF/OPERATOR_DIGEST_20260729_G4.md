# Operator Digest — 2026-07-29 (G4)

**What changed today, in one paragraph:**
The bot tracks how good its baseball predictions are, but that tracking was never actually turned on — it existed in test scripts only. It's now switched on and running every night automatically. Also added two new watchdog alerts: one flags bets that have sat open and unresolved for over a week, one flags when too many order attempts are failing (currently about 11% on the main book, which is above the new alert line — so it'll fire right away, on purpose, to prove the alert works).

**What this means for your money:**
No change — still zero real money at risk, same as every day until the gate clears. These are watch-only alerts; nothing they detect will pause or stop trading automatically.

**Does anything need your decision right now?**
No — nothing needs you today. This was built directly to your instruction from earlier (G4 task).

**Anything that worried the session, even if not urgent:**
The 11% failed-order rate on the main book (that the new alert will flag) isn't new — it was already there, just unmonitored until now. Worth a look when you have time, but not urgent.

---

*Full technical detail: see `SESSION_HANDOFF_20260730_0015.md` and `DECISION_LOG.md` for this date.*
