# Operator Digest — 2026-07-29

**What changed today, in one paragraph:**
Two recent findings — the baseball live-betting strategy's confidence ranking still comes out backwards after a proposed fix (tested two ways, both failed), and a separate check showed even a strategy with *real, working* edge can still get unlucky enough to trip the automatic "stop everything" safety switch about half the time within a year, just from normal up-and-down swings. Because of both findings together, we rewrote the proposal for how bet sizes get set going forward: instead of picking a smaller-but-still-active bet size, the new default is **zero** — don't size any bets at all on the affected strategies — until we can specifically show a strategy would survive that swing risk before turning its sizing back on. You reviewed and approved both judgment calls behind this today.

**What this means for your money:**
No change — still zero real money at risk. But there is something to know: this new "bet nothing until proven safe" rule is written down and approved, but **not yet turned on in the actual running system** — the bot on the server is still using the old sizing rule right now. Nobody is watching it lose money because of this (it's still play-money paper trading), but the fix needs a second technical step (updating the actual code) plus a data-science sign-off before it's real. That's the one open item.

**Does anything need your decision right now?**
No — nothing needs you today. The two calls you already made today ("agree on both") are the ones that mattered.

**Anything that worried the session, even if not urgent:**
Just the gap noted above — the safer sizing rule is approved on paper but not yet live in the code. Flagging so it doesn't quietly sit approved-but-inactive for too long.

---

**Addendum — later same-day cleanup session (T8 hygiene sweep):**
A follow-up session double-checked all of last week's modeling work (the A/B/C/D window sweep) for loose ends — uncommitted work, orphaned branches, mismatched logs. Everything checked out clean. No change to money or decisions above. One harmless paperwork item found (a duplicate status-file entry) and flagged for next session to tidy up.

---

*Full technical detail: see `SESSION_HANDOFF_20260729_0029.md`, `SESSION_HANDOFF_20260729_0058.md`, and `DECISION_LOG.md` for 2026-07-28/29, plus `ADR-0048`.*

---

**Addendum — later same-day session (T9/T-400, GG-105 feature-level rework):**

We went back to the baseball model's actual data — not the calibration math, the underlying stats it's fed — to see if there's some feature we haven't tried yet that could fix the "confidence ranking comes out backwards" problem mentioned above. We tested seven different raw stats and one combination of two stats, checked each one against the real betting history so far. None of them worked — the combination candidate actually made things measurably worse, not better. This means the overnight/multi-day baseball strategy (the main one) has now run out of straightforward things to try with the data it currently has. We're recommending the next session shift search effort to the in-game live-betting strategy instead, since it has a much smaller and more forgiving risk profile even without a proven edge yet. Separately, while digging through the data, we found a chunk of it (stats about the opposing pitcher) has been completely empty for every single game ever recorded — nobody had noticed. That's now logged as its own thing to investigate, unrelated to today's main finding.

**What this means for your money:** No change — still zero real money at risk. Nothing today touched live trading logic or risk limits; this was research only.

**Does anything need your decision right now?** No — nothing needs you today. The recommendation to shift focus toward the live in-game strategy is a suggestion for the next session to pick up, not something needing your sign-off now. The "not yet turned on in the actual running system" item from earlier today is unchanged and still the one open item that matters.

**Anything that worried the session, even if not urgent:** The opposing-pitcher data gap mentioned above — one whole category of information the model was supposed to be using has never actually been there, for the entire history of the project. Not urgent (today's testing found no fix in that category anyway), but worth someone eventually tracking down.

*Full technical detail: see `SESSION_HANDOFF_20260729_0530.md`, `DECISION_LOG.md` 2026-07-29 (T9 row), and `05_RESEARCH_EXPERIMENTS/T9_GG105_FEATURE_LEVEL_REWORK_2026-07-28.md`.*
