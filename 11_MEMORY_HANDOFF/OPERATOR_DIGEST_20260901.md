# Operator Digest — 2026-09-01

**What changed today:**
Re-ran last week's trading-cost estimate against the fixed ledger from the recent data-repair. The bottom line moved: the average profit per bet on the player-props side dropped noticeably once realistic trading costs are priced in, and the amount of evidence needed before that edge can be trusted is now roughly ten times bigger than it looked before the repair — not "one more bet away," as previously reported, but thousands of bets away at current pace. The underlying direction (still profitable on average) held up; the confidence margin did not. Also found and logged (not fixed) a small housekeeping issue: one of the internal status notes has grown too long again and needs a routine trim — logged as a follow-up task, not done today.

**Money impact:** None today. No real money at risk; nothing touched trading limits, live positions, or bet sizing.

**Decision needed?** None urgent. This is informational — the commercial-validation bar for the player-props strategy is farther away than last week's number suggested.

**Worry flag:** The prior week's "almost there" reading was based on a smaller, cleaner-looking sample than the corrected data actually supports. Worth keeping in mind before treating any near-term confirmation as solid.

---

**What changed (T-510):**
Drafted a proposal (ADR-0062, not yet accepted) for what to name the sub-strategies inside NFL and NHL's live-betting band, since that naming was blocking any work on those two sports. The draft follows the four-letter naming style already used for MLB and NBA rather than an older two-letter style a task note had incorrectly pointed to — that citation error is now logged separately (GG-233) so it doesn't mislead a future session. The draft proposes three sub-strategies outright and flags a fourth as "named but not yet authorized" pending a data-feed question that hasn't been verified. It deliberately does not copy every sub-strategy MLB has — several were judged not to fit NFL/NHL's market shape and were left out with reasoning recorded in the ADR.

**Money impact:** None. No code changed, no bands added, no sizing touched.

**Decision needed?** Yes, when convenient: review ADR-0062 and accept, reject, or amend it. Nothing NFL/NHL-related can proceed on the live-betting band until that happens.

**Worry flag:** None new — this was a scoped naming/design proposal, not new operational risk.
