# Operator Digest — 2026-08-20

- T-470 (auto): T-470: outcome-store extended to 08-07..08-15, all 532/532 corrupted epoch-12 positions now re-derivable (repair path, not discard)

## T-477 — epoch-12 ledger repair: planned and test-run, not applied

**What changed today, in one paragraph:** Earlier we found ~500 bets in the paper ledger had the wrong game date attached (from an outage), so their win/loss outcomes couldn't be trusted. Today's session wrote down, in advance, exactly how the fix will work and what would count as suspicious — then ran the fix on a scratch copy only, to see what it would produce. It worked cleanly and fixed all 532 affected bets. But the repaired numbers show we don't have nearly enough clean bets yet to trust the results either way (719 have it, we'd need roughly 5,600).

**What this means for your money:** No change — still zero real money at risk. This doesn't touch the paper bankroll or any live position sizing.

**Does anything need your decision right now?** Yes — a short decision (ADR-0055) is waiting on you: whether to actually apply this repair to the real ledger now that we know what it produces, and what to do about 46 bets that got stuck open during that same outage. See ADR-0055 §7 for the specific options.

**Anything that worried the session, even if not urgent?** One sub-group of bets (144 of them, right in the outage window) looks unusually lucky even after the fix — logged as GG-196 for someone to look into later, not treated as a fire today.

---

*Full technical detail: see `SESSION_HANDOFF_20260820_0455.md` and `DECISION_LOG.md` for this date.*
