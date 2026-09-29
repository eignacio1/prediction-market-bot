# Operator Digest — 2026-09-28

**What changed today, in one paragraph:**
We finished the audit on why the live-baseball model loses to the market: it only looks at 4 basic batter numbers — no score, pitcher, ballpark, or "scouting-report" judgment like basketball gets. So "the market beats us" was really "a simple version of us loses" — different, less final. We listed what the model sees, unused data we have, and what's missing, ranked by fix cost.

**What this means for your money:**
No change — still zero real money at risk.

**Does anything need your decision right now?**
No. Two small items (a possibly-broken ballpark feature; two sessions briefly grabbing the same task number) were flagged for next-session logging only.

**Anything that worried the session:**
The ballpark-effect number may have been silently defaulting to "no effect" — flagged, not yet confirmed or fixed.

---

*Full detail: `SESSION_HANDOFF_20260928_2358.md`, `DECISION_LOG.md`.*

---

## Follow-up — T-578

**What changed today, in one paragraph:**
Checked the ballpark-effect number flagged yesterday as possibly stuck on "no effect." It's not broken everywhere — about 15% of games were affected, not all of them, because a handful of stadium names (renamed sponsors, a temporary relocation) didn't match our lookup table. Fixed the matching so it also recognizes name variants going forward.

**What this means for your money:**
No change — still zero real money at risk. The fix isn't live yet; the paper-trading model still uses the old, slightly-degraded numbers until you approve turning it on.

**Does anything need your decision right now?**
Yes, but not urgently: whenever you're ready, sign off on turning the fix on (a short written proposal is ready for your review).

**Anything that worried the session:**
A small number of ballparks (about 8 teams, under 1% of games each) still don't match anything — flagged for future digging, not yet understood.

---

*Full detail: `SESSION_HANDOFF_20260929_0432.md`, `ADR-0064`, `DECISION_LOG.md`.*
