# Operator Digest — 2026-07-21 (T-393 close-out)

---

**What changed today, in one paragraph:**
This session finished checking over the work from the crashed session that studied how much money is actually sitting in Kalshi's baseball order books. Short version of that finding: real market depth is much thinner than the $500–$2,000 per market we'd been assuming — more like $66–$195 typically — and the liquidity that does exist is lopsided, which matters for how big a bet the bot should be allowed to place. That write-up is done and correct. This session just double-checked every piece of it was saved properly, and then closed out the paperwork for the session itself.

**What this means for your money:**
No change — still zero real money at risk, same as every day until the gate clears. Nothing about today's session touched live trading or bet sizing.

**Does anything need your decision right now?**
Yes — one small thing. The write-up from the depth study is sitting in a pull request (a proposed change bundle) that's fully tested and ready to merge into the main project, but I'm holding off on merging it myself since that's a shared, visible action. Say the word ("merge it") and it's done in one command — otherwise it'll wait for you to look at it first.

**Anything that worried the session, even if not urgent:**
No new worries. The thin-liquidity finding itself is the kind of thing worth keeping in mind (it means the bot's bet-size cap should probably account for actual market depth, not the old rougher estimate), but that's a known open decision already flagged for you, not a new surprise from today.

---

*Full technical detail: see `SESSION_HANDOFF_20260721_0436.md` and `DECISION_LOG.md` for this date.*
