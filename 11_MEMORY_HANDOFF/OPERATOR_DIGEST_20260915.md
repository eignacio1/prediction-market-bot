# Operator Digest — 2026-09-15

**What changed today, in one paragraph:**
We tried again to open the first real football (NFL) bet using the actual trained model (not a placeholder). It ran cleanly against live markets and found nothing worth betting on: most games didn't have the right data, a few had no live prices, and a couple were close but not close enough after fees. So the bet count for football stayed at zero — same outcome as the last attempt, but this time on a different week's games, which is a stronger signal that the model just isn't finding an edge in football right now rather than it being a fluke of one bad week.

**What this means for your money:**
No change — still zero real money at risk, same as every day until the gate clears. Nothing was traded, live or paper, in football today.

**Does anything need your decision right now?**
No — nothing needs you today. The open question (does football need a broader model before it'll ever bet anything) is logged and will resurface on its own when someone builds that.

**Anything that worried the session, even if not urgent:**
No new worry. This confirms — on a second independent attempt — that the football model as currently built (moneyline bets only) may simply not find enough games it can price. That's useful information, not a bug.

---

*Full technical detail: see `SESSION_HANDOFF_20260915_0456.md` and `DECISION_LOG.md` for this date.*

---

**Update — T-548/GG-271 (ring buffer fix):**

**What changed today, in one paragraph:**
A while back we fixed a bug where the baseball bot's memory of old rejected bets could grow without bound. This session checked whether that fix was actually running on the live server — not just sitting in the code. It found the fix IS running (a completely separate, unrelated update earlier today happened to restart the service, which is what activated it), and confirmed it's holding steady over several hours of real activity. No further action was needed.

**What this means for your money:**
No change — still zero real money at risk, same as every day until the gate clears.

**Does anything need your decision right now?**
No — nothing needs you today.

**Anything that worried the session, even if not urgent:**
One process gap, logged for later: a code fix landing isn't the same as it actually running — this one only went live because of an unrelated restart, not because anyone checked. We've opened a note to consider adding an explicit "is it actually active" check going forward.

---

*Full technical detail: see `SESSION_HANDOFF_20260915_0517.md` and `DECISION_LOG.md` for this date.*
**NFL Saturday capture gap, diagnosed and fixed in git.** We were missing all football price data on Saturdays — the schedule grabbing NFL prices ran every day except Saturday, so 09-12 has zero football rows while every other day that week has plenty. That day's data is gone for good. The fix is a one-line schedule addition mirroring Sunday's, dry-run tested. I also built an automatic check to catch this going forward.

The fix sits in a pull request (#133) awaiting your review rather than auto-deployed — the last five changes here were all merged by you, so I kept that pattern rather than pushing it live myself. It still needs deploying plus confirming next Saturday. Until then the gap stays open in tracking.

One loose thread, not chased: two other days had suspiciously identical football counts. Flagged, out of scope.

---

**Update — T-550 (football re-run against actual game results):**

**What changed today, in one paragraph:**
We re-ran the football betting model against real, finished games — not a dry run, actual completed Week 1 matchups. Result: still not enough data to say whether the model has an edge. We'd need roughly 2,600 qualifying games to draw a reliable conclusion at this bet size; we have 14. The average result across those 14 was slightly positive, but with this little data that's statistical noise, not evidence. Along the way we found the task briefing had assumed two weeks of games had finished when only one had, and we found two specific games silently dropped from the count for two unrelated technical reasons (a team-abbreviation mismatch, and one matchup with no archived price data at all) — neither related to the Saturday data-gap fixed earlier today. Both are logged, neither was fixed in this session since fixing them mid-experiment would taint the result.

**What this means for your money:**
No change — still zero real money at risk in football. This result doesn't support betting more, and it doesn't rule football out either — it just isn't enough games yet to know.

**Does anything need your decision right now?**
No — nothing needs you today. When more football weeks finish, this same script should be re-run to build up toward that ~2,600-game threshold.

**Anything that worried the session, even if not urgent:**
The task briefing itself was factually wrong about how many weeks had finished — worth noting since a wrong starting assumption, if unchecked, could have led to us treating a one-week sample as a two-week one. Also flagged two small, low-severity code gaps in how the model finds and counts games — future cleanup, not urgent.

---

*Full technical detail: see `SESSION_HANDOFF_20260916_0016.md` and `DECISION_LOG.md` for this date.*
