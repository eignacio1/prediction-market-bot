# Operator Digest — 2026-09-16

**What changed today, in one paragraph:**
You asked why no bet could be placed at all. We found two separate reasons. First, a real bug: two of the football/baseball scripts (T1 NFL and T1 MLB game-market) were missing a setting that made every single bet get rejected as "too small," even though the actual stake size was correct by design — that's fixed now, with tests proving both the fix and that we didn't touch the real minimum-bet rule elsewhere. Second, a working-as-intended situation: the baseball live-trading bot still can't actually submit demo orders to Kalshi because of their ongoing 32+ day outage (GG-203) — but we confirmed that gap doesn't matter for the metric that counts toward your live-trading gate, so rather than force a fix, we wrote up a one-page recommendation for you to decide whether to stop even trying those demo submissions until Kalshi's outage clears.

**What this means for your money:**
No change — still zero real money at risk. The fix does mean football/baseball bets that should have been placed will now actually go through going forward, instead of being silently blocked.

**Does anything need your decision right now?**
One optional item: the write-up (APR-0034) recommending we stop attempting demo order submissions for baseball live-trading until Kalshi's outage resolves. Not urgent — nothing breaks either way — but it's sitting there for you whenever you want to look.

**Anything that worried the session, even if not urgent:**
Kalshi's support bot has replied twice now with generic "demo environments are just unstable" explanations that don't engage with the specific evidence we gave them (a brand-new API key failing on its very first order, and an error message that points at their own internal account records, not a data-sync issue). We've drafted a follow-up asking for a human, not another bot reply. Also: a new item (GG-143) came up as possible follow-on work, but it wasn't part of what you asked for this session, so it was intentionally left alone rather than picked up.

---

*Full technical detail: see `SESSION_HANDOFF_20260916_0500.md` and `DECISION_LOG.md` for this date.*
Two loose pieces of work from a few days ago got properly merged in. We checked every day of the week for both football and baseball to make sure the system is actually recording data when it's supposed to, and confirmed there's only one day of missing football data (Saturday, September 12th) — that gap is now fixed going forward, and we deliberately did not try to fake or reconstruct the missing day's numbers. We also upgraded the alarm that watches for this kind of gap so it now watches every sport/day combination automatically instead of only knowing about football.

**What this means for your money:**
No change — still zero real money at risk, same as every day until the gate clears.

**Does anything need your decision right now?**
No — nothing needs you today.

**Anything that worried the session, even if not urgent:**
Nothing new. The one prior open item (an issue on Kalshi's side, tracked separately) is still being worked by another session and wasn't touched here.

---

*Full technical detail: see `SESSION_HANDOFF_20260916_0449.md` and `DECISION_LOG.md` for this date.*
