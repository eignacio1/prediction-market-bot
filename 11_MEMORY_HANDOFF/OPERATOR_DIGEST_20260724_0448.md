# Operator Digest — 2026-07-24 (04:48 UTC)

**What changed since the last digest:**
Fixed a bookkeeping bug in how the system tracks "how many clean bets does each strategy have." Previously, whenever one strategy's calculation got a small correction, the counter reset to zero for *all four* active strategies at once — even the three that weren't touched. That's been fixed so each strategy's counter only resets when something about that specific strategy actually changes. Three of the four strategies should now show their real bet counts again instead of appearing to have zero history. I also checked whether the existing weekly quality-monitoring check (the one that watches for miscalibration) needed new code — it didn't; it was already built, already running, just starved of data by the bug above.

**What this means for your money:**
No change — still zero real money at risk. This didn't touch any betting logic, risk limit, or live position. It only fixes how the system measures its own track record.

**Does anything need your decision right now?**
No.

**Anything that worried the session, even if not urgent:**
This fix repopulates the bet-count data but doesn't stop the underlying habit of one strategy's fix silently zeroing another strategy's counter going forward — that's flagged as unowned follow-up work, not fixed this session (was out of scope).

---

*Full technical detail: see `SESSION_HANDOFF_20260724_0448.md` and `DECISION_LOG.md`/`GOVERNANCE_GAP_LOG.md` for 2026-07-23/24.*
