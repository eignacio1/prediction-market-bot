# Operator Digest — 2026-09-24

- T-570 (auto): T-570: retirement mechanism (warn-only) landed; findings handed to 33.2 for GG registration.
- T-569 (auto): T-569: T4 latency thesis measured (D2/D3/D4 pre-registered) — verdict NOT SUPPORTED

---

## T-571 — Ledger integrity audit

**What changed today, in one paragraph:**
We checked whether the baseball trades our one working result was based on actually happened at the exchange, not just in our own records. Of 765 trades in that batch, we could only independently confirm 34 as real fills with Kalshi. Recomputing the result using only those 34 confirmed-real trades flips it — a win becomes a loss. The other 731 aren't proven fake, just unconfirmed, so this isn't a final verdict, it's a warning that our one demonstrated result may not hold up. Separately, we traced 42 football bets to a one-time manual test run from a few weeks ago and set them aside since we can't identify who ran it or under what review.

**What this means for your money:**
No change — still zero real money at risk, same as every day until the gate clears.

**Does anything need your decision right now?**
No — nothing needs you today. Findings are logged as open questions (GG-300, GG-301, GG-302) for follow-up work, not fixes awaiting your sign-off yet.

**Anything that worried the session, even if not urgent:**
Yes — the project's one credible working result (the baseball calibration finding) does not currently stand as proven on verified real trades. It needs the 731 unconfirmed trades resolved, or a check for whether the 34 confirmed ones are a biased sample, before anyone should treat that finding as settled.

*Full technical detail: see `SESSION_HANDOFF_20260924_0414.md` and `DECISION_LOG.md` for this date.*
