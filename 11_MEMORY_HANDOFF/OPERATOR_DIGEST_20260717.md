# Operator Digest — 2026-07-17 (T-377, GG-045 Kalshi market-depth capital ceiling)

**What changed today, in one paragraph:**
This was a prep/data-collection session, not a trading change — you'd flagged a while back that the $500-per-bet safety cap was reasoned from a liquidity estimate nobody had actually verified. This session pulled the real bet-size history from the live books (baseball's slow strategy has placed 259 bets between about $1 and $44 each; the fast in-game strategy has placed 910 bets around 50 cents each) — everything observed so far is far below the $500 cap, so there's no urgency at today's bankroll. It also tried, for the first time, to measure how much real buying/selling depth actually sits in Kalshi's baseball prop markets — but the attempt was run before any game was live, and came back showing zero depth everywhere, which turns out to be an artifact of timing (these markets are simply empty until a game is actually in progress), not a real finding. The same dead-end happened once before with basketball markets, so this confirms it's a pattern, not a fluke. A proposed second safety cap — sized relative to real market depth once we have it — is written up and waiting on you, but nothing changes until the real live-game measurement is taken, which didn't happen today.

**What this means for your money:**
No change — still zero real money at risk. Nothing in this session touched live trading code, risk sizing, or bet placement; it was pure measurement and paperwork.

**Does anything need your decision right now?**
No — nothing needs you today. There's a proposal on file (a depth-aware backup safety cap, on top of the existing $500 one) but it explicitly isn't ready for your sign-off yet — it needs a real measurement taken while a game is actually live first, which is next session's job.

**Anything that worried the session, even if not urgent:**
None new. The zero-depth reading looked alarming at first glance but was fully explained by bad timing (no game was live), not a real problem with the markets or the bot.

---

## Update — later the same day (T-381, GG-059 close-out)

**What changed:** Added a new panel to the dashboard that watches for bad data quietly getting into the system's feature files — the kind of problem where nothing crashes, but a number is wrong or missing and nobody notices until it affects a bet. The panel shows, at a glance, whether any of the automatic data checks failed recently. Also confirmed a previously-open question: baseball and basketball's data files are kept properly separate on disk, so one sport's data can't accidentally leak into or overwrite the other's — verified, not just assumed. Both were open items from an earlier review (GG-059) and are now fully closed.

**What this means for your money:** No change — still zero real money at risk. This is a monitoring improvement only; no trading logic, risk limits, or bet-sizing code was touched.

**Does anything need your decision right now?** No — nothing needs you today. This work is on GitHub as a pull request (a "ready to merge" package) but has not yet been merged into the main codebase or deployed to the server — a routine confirmation step got blocked by a safety check on our end (not a problem with the work itself), so it's sitting one step short of done. It'll go out in the next session without needing anything from you.

**Anything that worried the session, even if not urgent:** No new concerns today.

---

*Full technical detail: see `SESSION_HANDOFF_20260717_2235.md` and `DECISION_LOG.md` for 2026-07-17.*
