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
