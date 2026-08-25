# Operator Digest — 2026-08-25

- T-484 (auto): T-484 closed: KXMLBTOTAL outcome store 239->329 rows (307 resolved), VPS+git dual-path resolved, GG-206 registered OPEN

---

## Update — T-493 close-out

**What changed today, in one paragraph:**
Per your directive superseding the "leave T1 alone" instruction, we drafted a formal proposal (ADR-0058) to bring the overnight strategy (T1) back for the new bet types coming online — moneyline, spread, totals — but only in "watch and measure" mode, not real betting. It's a proposal only, not yet approved by you, and it doesn't touch any live betting code or dial.

**What this means for your money:**
No change — still zero real money at risk, and this doesn't touch the sizing rule that's currently set to bet nothing on T1 regardless. The proposal is written specifically so it doesn't need you to first decide whether the reason T1 was capped at zero (a risk-of-ruin finding from baseball player-prop betting) also applies to these new bet types — that's flagged as a separate, still-open question, not assumed either way.

**Does anything need your decision right now?**
Yes — one thing, whenever convenient: review and approve or reject ADR-0058. Nothing runs off it until you do.

**Anything that worried the session, even if not urgent:**
No new concerns. One earlier draft (from a different, overlapping session) that had assumed T1 was permanently dead was found and corrected mid-session to reflect your new directive — a good example of the "double-check before writing" safety habit catching a stale assumption before it caused confusion.
- T-492 (auto): T-492: GG-203 root cause = external Kalshi demo-account order-write fault, no in-repo fix; amended OPEN->PARTIALLY RESOLVED
