# Operator Digest — 2026-09-09

- T-529 (auto): T-529: landed T-526 (NFL C1 ingestion) + T-527 (NFL settlement) to main; GG-254 re-disposed PARTIALLY RESOLVED

---

## Update — T-531 close-out (EXP-027/HYP-012, NFL moneyline model)

Ran the first test of a simple NFL game-winner model, football's version of the baseball models already running. Rules were locked in writing before seeing results; built on 10 years of past games; sanity-checked against last season; ran four anti-cheating checks (model peeking at future info). Three passed clean; the fourth's flag was an NFL calendar quirk (Super Bowl counts under the *prior* year's season), not a real leak.

**Money:** No change, zero at risk. Verdict is "not enough evidence yet" — 2026 season hasn't started, so no real games to test bets against. Expected, not a surprise.

**Decision needed now?** No. **Any worry?** No — the calendar quirk was fully explained.

*Full technical detail: `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` (2026-09-09) and `11_MEMORY_HANDOFF/SESSION_HANDOFF_20260909_0526.md`.*
