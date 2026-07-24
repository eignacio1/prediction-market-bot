# Operator Digest — 2026-07-24

**What changed today, in one paragraph:**
We built a candidate improvement to one of the model's batting-average inputs and tested it, but deliberately did NOT turn it on. The idea: when a player has very few recent at-bats, lean more heavily on the league-wide average instead of trusting that small sample too much (this is the same "shrinkage" technique already live in the model, just testing a stronger version of it). We tuned the strength of that lean to whatever value best predicted outcomes on held-out historical data, landed it behind an off-by-default switch, and ran the full test suite to confirm nothing else changed (2,767 tests still pass). Then, checking our own work, we found something worth flagging before this ever gets turned on: the stronger version leans so heavily on the league average that a real player's own recent performance barely counts anymore (only about 8% weight, versus 45% for the version currently live). That's a real trade-off — it could make predictions look better on paper while quietly making them less useful in practice. We logged that concern formally rather than sweeping it under the rug.

**What this means for your money:**
No change — still zero real money at risk, and nothing about today's work touches what the live bot actually does. This is R&D sitting behind a switch that's off.

**Does anything need your decision right now?**
No — nothing needs you today. The next step is for a future session to build a proper backtest that checks whether this candidate actually helps or just games the scoring metric, before anyone considers turning it on.

**Anything that worried the session, even if not urgent:**
Yes — the 8%-vs-45% weighting gap above. It's the kind of thing that can look like an improvement by one measure (accuracy of predictions) while secretly making the model less sensitive to real differences between players. Flagged formally (GG-136) so nobody promotes this candidate without checking that specific concern first.

---

*Full technical detail: see `SESSION_HANDOFF_20260724_0453.md`, `DECISION_LOG.md` for 2026-07-23 (A1 row), `GOVERNANCE_GAP_LOG.md` GG-136.*
