# Project review — 2026-11-16 (SW-9 on Fable, operator's request)

**Last reviewed:** 2026-11-16. Sources: box reads 2026-11-17 00:57Z (`d6_read`, `arm_orders_read`, `budget_read`), W110–W114 handoffs,
the rolling backlog, Muse's archive at b6994a7. Operator 16:56 PT: "give me the high-end view of the project and what needs addressing
... rework the backlog ... a sweep ... an iteration task list that the window can act upon once Fable is removed after today."

## 1. The high-end view

**The machine exists; almost nothing flows through it to a verdict.** Four engines, ~90 logging cells, a router, a sizing rule, an order
path, a nightly data partner. As of tonight **3 of 117 cells are wired end to end on the box (NBA) — the first ever** — and the first
settled arm P&L exists. Three things stand between this and a bot that routes on its own evidence:

1. **No leaf has earned an arm, and at this design none will soon.** Every per-leaf test returned 0 survivors (NFL 0 / 82, NBA 0 / 85 and
   0 / 54, retro-route 1 / 365) while family-level held-out effects are real (ride NFL moneyline, fade NHL puck line, follow NHL moneyline
   moves). The cause is the statistics, not the sports: six weeks of rows cut into hundreds of leaves, each judged alone. → **115.1**.
2. **Execution decides the sign.** RIDE: 256 orders, 39 fills, fills win 69% (unfilled 59%), **+0.006 per contract before fees** — the
   fee takes it negative. MOMENTUM: fills win 42% vs 65% unfilled (adverse selection). And the sizing rule's own day cap zeroed ~7,500
   orders, so the evidence is rationed by a cap built for a real book. Placement is a fixed rule, not a choice. → **115.2**.
3. **The box is not the repo.** NFL and NHL have no filter data on the box (layer 3 = 0), 5,390 rows are unrouted, and each wave fixed a
   layer in the repo while the box stayed behind. → **115.3**.

**What is in good shape:** doctrine (one dated file, checked), CLAUDE.md (lean, checked against code), the directives ledger, D6 measured
on the box, Muse (620 tables / 4 days, snapshots every day), box health GREEN (94 live).

## 2. Insights from the sweep

- **I-1 The evidence rate is the binding constraint.** ~15 NBA + ~10 NHL games a day and 16 NFL a week cannot feed hundreds of leaves.
  Pooling (115.1) and long-history priors are not optional refinements; they are the only way the tree routes this season.
- **I-2 The prize has never been sized.** Fill rates are 6–21% at $1 demo stakes. Nobody has computed what a wired cell is worth in
  dollars at a real bankroll (fillable size × net per contract). It decides which cells deserve wiring first. (B-097)
- **I-3 RIDE is roughly break-even before fees.** If that holds at n, riding as a taker loses the fee; riding as a maker needs fills
  without selection. The ride arm's value is a placement question (115.2), not a prediction question.
- **I-4 The day cap is throttling the experiment.** ~7,500 demo orders zeroed by `size_for`'s per-day cap. Demo evidence should be capped
  by exposure realism, not starved. (115.2 Part A)
- **I-5 Outcome lookups fail a lot** (170 of 256 RIDE, 58 of 100 FADE): the settled-P&L numbers above rest on a minority of orders.
  (115.2 Part A)
- **I-6 The Muse channel is one-way and fragile.** The nightly sweep has not started since 11-13; Muse's runs report the fetch of
  TO_MUSE.md "flagged by a safety check". The Monday message is the only reliable instruction path; mid-week fixes do not land. (B-096)
- **I-7 Layer 1 covers 9 of 25 NBA cells, 9 of 29 NFL, 9 of 21 NHL, 3 of 42 MLB.** Most registered cells have no simulated probability
  on the box at all. D6 will plateau near ~30 until engines price the remaining families (team totals by band, props, alt lines).
- **I-8 Repo mass taxes every session:** 784 handoff files in the live folder, 263 open governance gaps, 53 backlog tickets, three dead
  PRs (#149, #458, #477), an 11,000-line Muse STATUS. Cheap to fix on Haiku. (B-098)
- **I-9 The strategy window is the largest single token cost.** One Fable turn in this window took ~55% of a session limit because the
  window carries days of context. Fable belongs in fresh terminals with a tight brief (the FABLE BUDGET rule), never in a long window.
- **I-10 G6 has no dated path.** There is a gate definition (ADR-0076) and no estimate of when any cell could reach judged n with a
  positive net. 115.1's power calendar gives the first honest date.

## 3. Iteration list — for the window after Fable (Sonnet / Haiku; in order)

| # | Task | Model | Done when |
|---|---|---|---|
| IT-1 | Verify Wave 115 on close: router v2 pre-registration frozen; placement model merged OFF; D6 per sport on the box | window | queue rows filled, D6 recounted by `d6_read` |
| IT-2 | Put the operator's decisions in one place: ADR-0072 addendum (115.2), install tasks (115.3), router v2 logging switch | window | approval sentences in "Needs your decision" |
| IT-3 | Wave 116 block A: MLB routed on the 2026 look-back (B-088), through router v2 if merged | Sonnet | MLB cells carry arms |
| IT-4 | Wave 116 block B: NBA props through the tree (B-093) | Sonnet | prop cells have layers 2–5 |
| IT-5 | Wave 116 block C: capacity and dollar ceiling per arm per sport (B-097) | Sonnet | $ / day at $1k, $10k, $100k per sport |
| IT-6 | Wave 116 block D: repo hygiene — archive old handoffs, close #149 #458 #477, burn down gaps by file (B-098, B-074) | Haiku | live handoff folder < 60 files; open gaps counted |
| IT-7 | Muse watchdog: recreate the sweep if 11-16 fails; fold fixes into the Monday message (B-096) | window / Haiku | a sweep entry lands |
| IT-8 | Layer 1 coverage: engines price the unpriced families per sport (I-7) — one sport per wave, NBA first | Sonnet | layer-1 cells per sport up |
| IT-9 | Pot-of-gold arm scored through router v2; same-game combos as its input (B-024) | Sonnet | pot-of-gold leaves with a posterior |
| IT-10 | Weekly: recount D6 and E1–E3 per arm on the box; update CLAUDE.md Right now; read the power calendar | window | every wave close |
| IT-11 | Rewrite STRATEGY_OVERVIEW / ARCHITECTURE_OVERVIEW bodies to the doctrine (B-075) | Haiku | bodies match DOCTRINE.md |
| IT-12 | NHL goalie timing vs Muse snapshots once NHL_EVENTS is on the box (B-012) | Sonnet | timing table vs Kalshi moves |

## 4. Recommendations

1. **Run Fable only in the three terminals; put this window back on Sonnet (or Opus) now.** (I-9)
2. **Approve 115.3's install tasks and 115.2's ADR-0072 addendum quickly when they arrive** — they gate NFL / NHL wiring and the first
   placement comparison.
3. **Judge the next two weeks by three numbers:** D6 on the box, leaves with an arm under router v2, net per filled contract after fees
   per arm.
4. **Do not add markets or sports until D6 passes ~20 cells**; breadth is ahead of everything else (90 logging cells, 3 wired).
5. **Muse:** send tonight's message; treat the Monday message as the only instruction channel until the sweep is repaired.
