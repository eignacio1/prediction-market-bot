# Operator Digest — 2026-09-09

- T-529 (auto): T-529: landed T-526 (NFL C1 ingestion) + T-527 (NFL settlement) to main; GG-254 re-disposed PARTIALLY RESOLVED
- T-530: Built the T1 NFL game-market run script (paper only) — wires all four NFL cells (moneyline, spread, game total, team total) through the ADR-0058 stake formula into the paper trader, with the live-order path structurally disabled (`kalshi_client=None`). Added four refusal-path tests (kill switch, no model, unparsed markets, ambiguous tie settlement); full suite 3117 passed / 28 skipped / 0 failed. GG-255 moved OPEN → PARTIALLY RESOLVED. Still open: no cron entry yet, MLB half of the nine ADR-0058 cells has no run script, and the forecast model wired in is a stub, not a trained model — none of that is a blocker for this task, just unclaimed follow-on work. Branch is pushed but not yet merged to `main`.

---

## Update — T-531 close-out (EXP-027/HYP-012, NFL moneyline model)

Ran the first test of a simple NFL game-winner model, football's version of the baseball models already running. Rules were locked in writing before seeing results; built on 10 years of past games; sanity-checked against last season; ran four anti-cheating checks (model peeking at future info). Three passed clean; the fourth's flag was an NFL calendar quirk (Super Bowl counts under the *prior* year's season), not a real leak.

**Money:** No change, zero at risk. Verdict is "not enough evidence yet" — 2026 season hasn't started, so no real games to test bets against. Expected, not a surprise.

**Decision needed now?** No. **Any worry?** No — the calendar quirk was fully explained.

*Full technical detail: `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` (2026-09-09) and `11_MEMORY_HANDOFF/SESSION_HANDOFF_20260909_0526.md`.*

---

## Update — T-533 close-out (NFL cron fix + VPS deploy)

Fixed a real gap before Week 1 kickoff: the NFL price-capture cron was missing a day (Wednesday UTC), so roughly 2.5 hours of pregame price history for the opener would have been silently lost forever — this kind of data can't be recovered after the fact. Added the missing cron line and turned on orderbook-depth capture for NFL (was already on for MLB). Deployed both fixes to the live VPS with a surgical edit that touched only the NFL lines — verified nothing else on the server's schedule changed. Also closed out a leftover branch from an earlier NFL trading-script task (its work had already landed; this just tidied the record).

**Money:** No change, zero at risk — this is capture/scheduling only, no trading logic touched.

**Decision needed now?** No. **Any worry?** One: found (but did not touch) an unrelated MLB cron time that doesn't match what's in the repo — flagged for a future session (GG-262).

*Full detail: `DECISION_LOG.md` (2026-09-09), `SESSION_HANDOFF_20260909_1519.md`.*

---

## Update — T-537 close-out (NFL depth-capture cron, proof it actually works)

Last session (T-533) added a fix so the NFL price-and-depth capture would run correctly this week. This session's job was to prove that fix actually works, not just that it looks right on paper — hand-tested the exact commands, checked the server's schedule and clock, and then watched the real capture fire live during the session: it ran 8 times on schedule between 5:05pm and 7:25pm UTC today, each time capturing exactly what it should, with zero errors. Also took a snapshot of baseball's capture numbers today for comparison, since football and baseball share this same system.

**Money:** No change, zero at risk — this is capture/verification only, no trading logic touched.

**Decision needed now?** No. **Any worry?** No — found no defect, so nothing was changed in the schedule; the earlier fix already works.

*Full detail: `DECISION_LOG.md` (2026-09-09), `SESSION_HANDOFF_20260909_1947.md`.*
