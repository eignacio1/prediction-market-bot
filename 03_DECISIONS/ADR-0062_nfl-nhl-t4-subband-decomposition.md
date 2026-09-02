# ADR-0062: NFL/NHL T4 Sub-Band Decomposition — Names, Roster, Epoch Inheritance

**Status:** PROPOSED — draft only. Not authorized to implement. Adding, renaming, or removing any `ExecutionBand` member, touching `market_type_registry.py`, or setting any `kelly_fraction` requires a separate task under a future ADR-0062 ACCEPTED (Hard Rule 3, Hard Rule 11).

**Date:** 2026-09-01
**Author:** Claude (worktree `session/20260901T052405Z-t510-gg226-nfl-nhl-band-adr`, T-510)
**Resolves (partially, on acceptance):** GG-226 — no namespace-valid `ExecutionBand` member exists for NFL/NHL T4 sub-bands, blocking T-504-style registry scaffolding for 7 of 12 target families.
**Precedent:** ADR-0056 (D1/D2/D3, ACCEPTED 2026-08-21), ADR-0039 (MLB Tier A/Tier B scoping, ACCEPTED/scoped 2026-07-02), T-504 (MLB ARITH/FLOW extension + create/decline methodology, 2026-08-29/31).

---

## 0. Correction to this task's own briefing (flagged per the task's explicit instruction)

The task brief that produced this ADR described ADR-0056 as having "settled APR-0032's D2 as the `T4N-` naming convention for NFL." **This is incorrect.** Direct reading of ADR-0056 §3 shows `T4N-` (single-letter, mirroring MLB's `T4M-`) was the *original* 2026-08-20 recommendation, superseded before sign-off by Amendment (iii) on 2026-08-21 (T-480/GG-200). The convention actually accepted is the four-letter, explicit-sport-code form: **`T4MLB-`, `T4NBA-`, `T4NFL-`, `T4NHL-`** — MLB and NBA grandfathered on their pre-existing names, NFL and NHL required to use the four-letter form from their first cell forward. ADR-0056's own text states plainly that any draft using `T4N-` "is not authorized and must be corrected to `T4NFL-` before that code ships." This ADR uses the verified, actually-adopted convention throughout. The discrepancy is registered as **GG-233** (OPEN, LOW), committed ahead of this draft.

---

## 1. Context

GG-226 (OPEN, MEDIUM, registered by T-504, 2026-08-29/31): T-504 extended MLB's `T4M_ARITH`/`T4M_FLOW` sub-bands to MLB's five non-prop game-market families, but could not do the same for NFL (4 families) or NHL (3 families) because none of the 13 existing `ExecutionBand` T4 sub-band members carry an NFL or NHL namespace, and adding one is an `execution_bands.py` edit outside T-504's scope fence. ADR-0056 D2 already settled *how* any new sport-prefixed member must be named. It did not decide *which* members NFL and NHL should get — that decomposition question, per the operator's task brief, is judgment, not mechanical copying of MLB's roster, and is what this ADR resolves.

This document does not authorize anything. It proposes band names, a per-sub-band propose/decline table with reasoning, and a cell-count projection, so that a future scaffolding session (an NFL/NHL analogue of T-504) has a settled naming and roster decision to build against — the same relationship ADR-0039 had to T-504's actual build.

---

## 2. What was measured, live, before proposing anything

Per the task's explicit "measure before you propose" instruction, live Kalshi data was queried directly (via VPS, public `/trade-api/v2/events` endpoint) on **2026-09-01**, in addition to citing the registry's own prior live-verification history:

| Series | `status=open` events found (2026-09-01) | Unfiltered (any status) sample | Read |
|---|---|---|---|
| `KXNFLGAME` (moneyline) | 5 open (Week 1, e.g. `KXNFLGAME-26SEP09NESEA`) | — | **Live, tradeable now.** Season opens 2026-09-09. |
| `KXNFLSPREAD` | 5 open (same Week 1 slate) | — | **Live, tradeable now.** |
| `KXNFLTOTAL` | 5 open (same Week 1 slate) | — | **Live, tradeable now.** |
| `KXNFLTEAMTOTAL` | **0 open** | 5 found unfiltered, all dated Jan/Feb 2026 (last season's playoffs, now closed) | **Structurally real (ticker family exists, has a real event-naming history) but currently dark** — the 2026-27 season's team-total markets are not yet listed, even though moneyline/spread/total already are for the same Week 1 games. Not ruled out; recorded as a live measurement. |
| `KXNHLGAME` | **0 open** | 5 found unfiltered, all dated June 2026 (2026 Stanley Cup Finals, Carolina–Vegas, now closed) | **Fully off-season**, as expected — NHL's 2026-27 season opens in October. Consistent with T-495's 2026-08-25/26 finding. |
| `KXNHLSPREAD` | 0 open | same June 2026 pattern | Off-season, expected. |
| `KXNHLTOTAL` | 0 open | same June 2026 pattern | Off-season, expected. |

Series/`MarketType` existence itself (which families Kalshi lists at all, and their ticker grammar) was already live-verified and is not re-litigated here: NFL's 4 families (`NFL_MONEYLINE`, `NFL_SPREAD`, `NFL_GAME_TOTAL`, `NFL_TEAM_TOTAL`) at T-474 (2026-08-21); NHL's 3 families (`NHL_MONEYLINE`, `NHL_PUCK_LINE`, `NHL_GAME_TOTAL`, with `NHL_TEAM_TOTAL` deliberately withheld per GG-217 — no backing ticker exists at all, confirmed against the full ~3512-series Sports listing) at T-495 (2026-08-25/26).

**Per operator doctrine (binding on this ADR): a family with no in-play market right now is a measurement finding to record, not grounds to decline building for it.** NHL's current blackout is entirely explained by its off-season calendar, not a structural defect — the sport is still being built per standing directive. NFL_TEAM_TOTAL's current gap (structurally real, temporarily unlisted) is treated the same way: recorded, not treated as a reason to exclude the family from this decomposition.

---

## 3. Decision D1 — Band member names (applying ADR-0056 D2, not reopening it)

Following the settled four-letter convention exactly, and mirroring ADR-0039's structural choice of **one sub-band registry per sport** (not a shared one):

- **NFL:** `T4NFL-ARITH`, `T4NFL-FLOW` (with a `T4NFL-FLOW-BLOWOUT` variant mirroring MLB's `T4M-FLOW`/blowout pairing), `T4NFL-BOUNDARY`, `T4NFL-EVENT`.
- **NHL:** `T4NHL-ARITH`, `T4NHL-FLOW`, `T4NHL-BOUNDARY`, `T4NHL-EVENT`.

These are the sub-band *names* this ADR proposes creating as `ExecutionBand` enum members in a future implementation task. No enum member is added by this document.

---

## 4. Decision D2 — Which sub-bands each sport actually gets

Per-sub-band judgment against ADR-0039's full MLB Tier B roster (`PROJ`, `EVENT`, `PITCHER`, `LINEUP`, `FLOW`(+`BLOWOUT`), `BOUNDARY`, `ARITH`, `STAGED`, `CORR`, `EXIT`), applying T-504's create/decline methodology independently to each sport rather than assuming MLB's verdict carries over, per the task's explicit instruction.

| Sub-band concept | NFL | NHL | Reasoning |
|---|---|---|---|
| **ARITH** (deterministic game-state → win-prob arithmetic re-pricing) | **Propose.** | **Propose.** | Both sports have a running game clock and a well-established score-state + time-remaining win-probability function (standard in both NFL and NHL analytics). NFL's discrete down/distance/possession state makes this an even cleaner fit than MLB's outs-remaining math; NHL lacks discrete possession snapshots but still has clean clock+score state to project from — the concept transfers on the clock/score axis, not on possession discreteness. Applies to all in-registry game markets per sport (NFL: moneyline/spread/game_total/team_total; NHL: moneyline/puck_line/game_total). |
| **FLOW** (live scoring-momentum re-pricing, incl. blowout variant) | **Propose.** | **Propose, with a calibration caveat.** | NFL: score-margin-driven momentum and "garbage time" blowout detection are well-established, discrete, and directly analogous to MLB's FLOW/BLOWOUT split. NHL: the concept is structurally applicable (a 3-goal NHL lead behaves like a blowout signal), but NHL's low event count (~5-8 goals/game vs. MLB's dozens of PAs) means any live calibration will need sport-native tuning — this ADR only decides the concept applies and the member should exist; it does not authorize or calibrate FLOW's thresholds for either sport. |
| **BOUNDARY** (structural game-boundary-crossing trigger) | **Propose, scoped only — same not-yet-authorized posture MLB's own `T4M-BOUNDARY` carries.** | **Propose, scoped only, same posture.** | NFL has clean discrete boundaries (quarter ends, two-minute warning) directly analogous to MLB's inning/PA boundaries. NHL has period boundaries and power-play expiry as equally clean discrete triggers. Neither is being authorized to build here — MLB's own `T4M-BOUNDARY` is "scoped but not authorized despite being flagged equally cheap" per ADR-0039, and this ADR does not have grounds to treat NFL/NHL more permissively than MLB's own precedent. |
| **EVENT** (push-driven, blocked for MLB on GG-066's poll-only C1 constraint) | **Defer.** | **Defer.** | EVENT's MLB block is a data-plumbing fact (poll-only ESPN C1 ingestion), not a game-structure fact — whether it applies to NFL/NHL depends on each sport's actual C1 ingestion mechanism (push vs. poll), which was **not verified in this session**. Naming the member is cheap and consistent with the sport-agnostic concept, but this ADR declines to assert live/blocked status for either sport without that verification. Recommend a follow-on check of each sport's C1 module before authorizing. |
| **PROJ** (player-level statistical projection toward a prop threshold) | **Decline.** | **Decline.** | Same reasoning T-504 used for MLB's own non-prop game families: PROJ is player-scoped and has no game-level analogue. More strongly true here — neither NFL's 4 nor NHL's 3 in-registry `MarketType` families are player-props at all; all are team/game-scoped. There is no cell for a PROJ member to attach to in either sport's current registry. |
| **PITCHER** (pitcher-identity info class) | **Decline.** | **Decline.** | ADR-0039 itself names this as an MLB-unique information class with "no NBA analogue" stated explicitly. A structurally-plausible NHL cousin exists in principle (starting-goalie confirmation is a well-known real signal in hockey betting) but that would be a **new, NHL-native concept requiring its own name and its own justification** — not a renamed PITCHER. Inventing it is out of scope for a decomposition ADR; flagged here as a candidate worth a future, separate proposal, not decided or named in this document. |
| **LINEUP** (batting-order-position info class) | **Decline.** | **Decline.** | Same treatment as PITCHER: no named analogue exists in the ADR-0039 roster for either sport's structure. NHL line-combination matchups are a plausible future-ADR candidate; not invented here. |
| **STAGED** (staged/two-phase order placement mechanism) | **Decline sport-prefixed member.** | **Decline sport-prefixed member.** | ADR-0039 itself classifies STAGED as "sport-agnostic mechanism, not separately authorized" for MLB — it is Tier A architecture, not a Tier B sport-rostered member. The same is true by construction for any sport: it needs no `T4NFL-`/`T4NHL-` namespace at all. |
| **CORR** (cross-position correlation overlay, downward-only) | **Decline sport-prefixed member.** | **Decline sport-prefixed member.** | Portfolio-layer overlay operating across the whole book, not within one sport's cell set — mirrors STAGED's reasoning. A sport-prefixed CORR member would misrepresent it as sport-scoped when it structurally isn't. |
| **EXIT** (portfolio-layer exit-management overlay) | **Decline sport-prefixed member.** | **Decline sport-prefixed member.** | Same portfolio-layer reasoning as CORR. |

**Net new members proposed (not created) by this ADR:** 4 per sport — `ARITH`, `FLOW` (+`BLOWOUT` variant, NFL only named explicitly above; NHL may want the same variant, left to the implementing session to decide given the calibration caveat), `BOUNDARY`, `EVENT` — with `EVENT`'s authorization explicitly deferred pending C1 verification.

---

## 5. Decision D3 — Logic-epoch inheritance

ADR-0056 D3 already settled this generally: every sport's `logic_epoch` counter is independent and starts fresh at epoch 1, not inherited from MLB's 12 boundaries. This ADR does not revisit D3 — it confirms NFL and NHL's T4 sub-bands, once built, are governed by each sport's own fresh-epoch-1 counter, exactly as D3 already requires for every other NFL/NHL cell. Note (informational, not decided here): T-474 (2026-08-21) found `logic_epoch.py` had no per-sport counter implemented in code at all at that time (registered as GG-202); this ADR does not verify whether that has since been implemented — check `logic_epoch.py` directly before treating D3 as live in code, not just accepted on paper.

---

## 6. Decision D4 — Cell-count projection

This is arithmetic, not a commitment — no cell is created by this document. Two different grids exist in this project and should not be conflated: `COVERAGE_TARGET_MATRIX.md`'s coarse ~25-cell (market-mechanism × band-tier) target grid, and `market_type_registry.py`'s fine-grained `(MarketType, ExecutionBand)` registry, currently at 78 cells post-T-504. This projection is against the latter.

If a future session builds exactly the members this ADR proposes for authorization-eligible sub-bands (`ARITH`, `FLOW`, `BOUNDARY` — excluding `EVENT`, deferred) across every in-registry family per sport:

- **NFL:** 3 sub-bands × 4 families (`MONEYLINE`, `SPREAD`, `GAME_TOTAL`, `TEAM_TOTAL`) = **12 new cells**.
- **NHL:** 3 sub-bands × 3 families (`MONEYLINE`, `PUCK_LINE`, `GAME_TOTAL`) = **9 new cells**.
- **Subtotal:** 21 new `NOT_IMPLEMENTED` cells, 78 → **99**.
- If `EVENT` is later authorized for both sports after C1 verification: +4 (NFL) +3 (NHL) = 7 more → **106**.

This does not itself answer the open operator question of how many cells must clear before live capital is authorized (COVERAGE_TARGET_MATRIX.md's "strategic tension nobody has adjudicated" — generality vs. edge). It only sizes what "build the NFL/NHL analogue of T-504" would add to the denominator. Every one of these cells, if built, starts `NOT_IMPLEMENTED`, exactly as T-504's MLB cells did — no `kelly_fraction`, no `CellStatus` promotion, nothing wired.

---

## 7. Explicitly not decided by this ADR

- Whether `T4NFL-*`/`T4NHL-*` members are actually added to `execution_bands.py`. That is a future scaffolding task's job, mirroring T-504.
- Whether `EVENT` is authorized for either sport (depends on unverified C1 ingestion mechanism).
- Any `kelly_fraction` value for any proposed member.
- Whether NFL_TEAM_TOTAL or any NHL family is authorized to trade once its market goes live — that is a separate activation decision, not a naming/roster decision.
- Whether the `T4NFL-FLOW-BLOWOUT`-style variant is warranted for NHL specifically — flagged as an open question for the implementing session given the calibration caveat in §4.
- The PITCHER/LINEUP-analogue candidates named in §4 (NHL starting-goalie signal, NHL line-combination matchups) — not proposed, not named, explicitly deferred to a future, separate ADR if pursued.
- Any change to MLB's or NBA's existing grandfathered band names.

---

## 8. Sign-off

Status: **PROPOSED**. Awaiting operator review. Not authorized for implementation.
