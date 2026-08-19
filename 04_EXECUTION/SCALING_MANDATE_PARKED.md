# Scaling Mandate — parked 2026-08-03, operator directive

**Status:** PARKED. Not an action plan. Do not action without operator direction.
**Why parked:** raised mid-Phase-0; the tactical work continues first. This file exists so the framing survives, because it is the most consequential strategic content in the project and it currently lives only in a chat log.

---

## The mandate, in the operator's terms

This is a **calibration engine** structured as a betting bot. The end state is not "MLB and NBA on Kalshi." It is: **every venue offering prediction-market access, and every market on those venues** — weather in Ohio, a celebrity event, Knicks game 42. NBA and MLB are the boat being tested in the canal to find out whether it survives the ocean. Two sports and one venue is not the target; it is the trial.

The architecture is deliberately segmented into **data aggregation** and **data interpretation** for exactly this reason.

## The operator's own diagnosis, recorded verbatim in substance

1. Weeks — not days — passed without the operator applying the diligence he asked the models to maintain. The consequence was a class of miss that should have surfaced far earlier: standard betting lines never implemented, logging protocols never scaled for expansion, bucket execution never built agnostic.
2. The scale is a source of pride and the source of the problem. The repo is now hard to navigate *efficiently*, and he is the sole operator — the only reviewer, the only decision-maker, the only hand on the kill switch. **Navigational difficulty is therefore a decision-quality risk, not a comfort issue.**
3. **The edge-case objection:** demanding proactive coverage of edge cases is not fair, because edge cases have not happened yet and are unknown by definition. The answer is not a longer list of anticipated failures — it is **infrastructure that absorbs volatility from failures nobody enumerated.**
4. The deliverable standard is handoff: this must eventually go to people the operator cares about who **will have zero ability to fix cracks.** That is the bar. Not performativity.

## The question that was never asked

In 70 days, across every gap, fix, and protocol pass, no session ever asked: *"Have you thought about the types of bets you envisioned the bot would place?"*

The operator's read — correct — is that this is a structural failure, not a model failure: the system was never built to surface that class of question. **Every verification mechanism in this repo checks whether the stated thing was done correctly. None check whether the stated thing is the right thing.** That is the gap this mandate exists to close, and it recurred four times in observable form (GG-144's status-scan blindness, Q4's dead grep, the `market_mapper` registry that never existed, the unanchored 429 pattern).

## What was already agreed (2026-08-02, the console/archive split)

Tactical, in flight, insufficient on its own:

1. **Archive vs console are different structures.** The archive is append-only, complete, lineage-preserving — never weaken it. A console is current-state, decision-ranked, disposable. One file cannot be both; at 3,000 lines the archive property wins and the console property dies.
2. **Split the gap log by status** — OPEN stays, RESOLVED moves verbatim to an archive file. ~85% reduction in what gets read.
3. **Structured status headers, narrative below a fold.** Severity currently lives in *how emphatically the prose is written*, which is precisely why bolded entries hid from the scan.
4. **Generate `OPERATOR_CONSOLE.md`** on every governance scan: decisions blocked on the operator, what's accruing and its clock, what's actually broken. Never hand-patch a generated view.
5. **Rank by "blocks operator," not by severity.** 17 open gaps is not the problem; not knowing which 3 need *him* is.

## What the mandate demands beyond that

The above fixes readability. It does not address scale. Open questions to answer when this is unparked — deliberately framed as questions, not answers, because the operator has not yet directed the design:

- **Venue and market abstraction:** the Phase 1 market-type registry and `VenueAdapter` repair are the first instance of a general problem. What does the registry look like at 50 venues and 10,000 market families rather than 4 and 1?
- **Measurement at scale:** `clean_n` per band already produces epoch-reset churn at 4 bands. What is the shape at hundreds of segmented pools? (The measurement/execution decoupling identified in the 2026-07-30 assessment is the prerequisite and remains unbuilt.)
- **Volatility absorption rather than edge-case enumeration:** what invariants must hold such that an *unanticipated* failure degrades safely? The current answer is kill switches plus per-band isolation — neither designed for unknown failure classes.
- **The question-asking gap:** what mechanism would have surfaced "what bet types did you envision?" on day 10? A periodic intent-vs-implementation reconciliation is the obvious candidate; nothing in the current protocol does this.
- **Handoff-readiness as an explicit gate:** if the standard is "someone who cannot fix cracks can operate it," that is a testable property and it is not currently tested anywhere.

## Sequencing note

Do **not** unpark this mid-Phase-1. It is a foundational redesign; starting it while the abstraction repair is half-done produces two incomplete architectures. The natural moment is after Phase 2's gate returns a verdict — at that point the project either has a validated second market family (and scale becomes urgent) or it does not (and scale becomes moot).
