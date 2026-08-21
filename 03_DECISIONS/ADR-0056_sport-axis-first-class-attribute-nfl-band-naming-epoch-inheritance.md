# ADR-0056 — Sport as a First-Class Attribute, Sport Band-Naming Convention, Per-Sport Epoch Inheritance (GG-198)

**Status:** PROPOSED. This ADR folds the operator's signed APR-0032 D1/D2/D3 decisions (Earl Ignacio,
2026-08-21) into an implementable record, per Hard Rule 3 — signing APR-0032's decisions is not the same as
accepting this document. This ADR itself still requires operator sign-off before `market_type_registry.py`,
`execution_bands.py`, or `logic_epoch.py` may be changed.
**Date:** 2026-08-21
**Author:** Session T-481 (`adr0056-sport-axis` worktree)
**Registers/depends on:** `APR-0032` (decision-request document; D1/D2/D3 signed 2026-08-21 — see its
"OPERATOR SIGN-OFF — APR-0032 D1/D2/D3" section, appended this session). `ADR-0054` §4 (the `(MarketType,
band)` cell key — unchanged by this ADR; D1 below is explicitly additive, not a re-key). `ADR-0039` (the
`T4M-` MLB band-prefix precedent D2 below partially supersedes for future sports while grandfathering it for
MLB itself). `GG-198` (OPEN — the three sport-axis questions this ADR closes at implementation, not at
drafting). `GG-200` (2026-08-21, T-480 — the four-sport-roster amendment to APR-0032 D2, folded into D2
below as signed).
**Scope:** Decision record only. No `src/` change is made or authorized to ship by this document alone —
this ADR is itself the "superseding ADR" Hard Rule 3 and APR-0032 both require to exist *before*
`market_type_registry.py` / `execution_bands.py` / `logic_epoch.py` may be edited for this purpose. Once
this ADR is ACCEPTED, the edits it specifies are authorized; drafting it does not perform them.

---

## 1. Context

`APR-0032` (2026-08-20/21, T-473, amended T-480/GG-200) presented three sport-axis questions Phase 3 would
otherwise answer implicitly rather than by operator decision: whether `sport` becomes a first-class
`MarketType` attribute (D1), what naming convention new sports' T4 sub-bands use (D2), and whether a new
sport's `logic_epoch` counter starts fresh or inherits an existing sport's boundary numbering (D3). The
operator signed all three, 2026-08-21, verbatim text reproduced in APR-0032's now-appended "OPERATOR
SIGN-OFF" section. This ADR is the implementable record Hard Rule 3 requires before that sign-off can become
code — it restates each decision as-signed (not as originally recommended, where the two differ), names the
exact mechanism, and names the exact file/symbol each lands in.

---

## 2. D1 — `sport` as a first-class `MarketType` attribute — ADOPTED, option (a)

**Decision as signed:** add `sport` as a first-class attribute on `MarketType`, via **either** an enum
property **or** a `_SPORT_BY_MARKET_TYPE` map — the operator's sign-off names both forms of option (a)
without picking between them; APR-0032's own D1 text frames the map form
(`_SPORT_BY_MARKET_TYPE: dict[MarketType, str]`, alongside the existing `_SERIES_TICKER_BY_MARKET_TYPE`-style
map) as the direct mechanical parallel to code already in the file, so an implementing session should default
to the map form unless a concrete reason favors the property form — that is an implementation-detail choice
this ADR leaves open, not a re-opening of D1 itself.

**What is NOT changed:** the `(MarketType, band)` cell key (`ADR-0054` §4) stands exactly as decided. `sport`
is additive — a grouping/lookup attribute, not a third key axis. APR-0032 D1 option (c) (folding sport into
the key) was considered and rejected; this ADR does not reconsider that rejection.

**Lands in:** `src/prediction_market_bot/c5_execution/market_type_registry.py` — the `MarketType` enum
(currently `class MarketType(Enum)`, line 59 at APR-0032 drafting time) gains the `sport` attribute or
adjacent map; every current member (`MLB_PLAYER_PROP_HITS`, `MLB_MONEYLINE`, `MLB_RUN_LINE`,
`MLB_GAME_TOTAL`, `MLB_TEAM_TOTAL`, `MLB_PARTIAL_GAME`, `NBA_PLAYER_POINTS`) requires one entry; every future
member requires one at the point it is added.

**Enforcement:** APR-0032 D1's options table names `MarketTypeCell.__post_init__`'s existing enforcement
pattern (required `reason`/`measured_date` for `RULED_OUT` status) as the precedent for making a missing
`sport` entry a construction-time failure rather than a silent gap — an implementing session should follow
that precedent (fail closed on an unmapped `MarketType`), not introduce a silent default.

---

## 3. D2 — Sport band-naming convention — ADOPTED, the 2026-08-21 Amendment (T-480/GG-200), NOT the original option (a)

**Decision as signed:** the operator adopted APR-0032 D2's **Amendment (iii) "Revised recommendation"**
(2026-08-21, T-480/GG-200) — **not** the original 2026-08-20 recommended option (a) (`T4N-PROJ`-style single
new letter). The distinction matters: both are labeled "(a)" in different revisions of the same document:

- **Original D2 option (a), 2026-08-20 — NOT adopted.** Extend the ad-hoc single-letter convention:
  `T4N-PROJ` for NFL, mirroring MLB's `T4M-` pattern (`ADR-0039`). Superseded by the amendment before
  sign-off; the operator signed the amended text, not this one.
- **Amended D2, signed 2026-08-21 — ADOPTED.** Explicit four-letter sport codes for every sport from that
  sport's first cell forward: **`T4MLB-`, `T4NBA-`, `T4NFL-`, `T4NHL-`.**

**Mechanism:** each sport's T4 sub-band registry is keyed by its four-letter code as a prefix on the
sub-band string — e.g. a future NFL `T4_NFL_SUBBAND_REGISTRY` would define members such as `T4NFL-PROJ`,
mirroring the structure (not the letter-count) of MLB's existing `T4_MLB_SUBBAND_REGISTRY`
(`ADR-0039`) and NBA's `T4_SUBBAND_REGISTRY`/`T4_SUBBANDS`.

**Grandfathering — exact, per the operator's signed text:**

| Sport | Existing/first names | Status |
|---|---|---|
| MLB | `T4M-PROJ`, `T4M-ARITH`, `T4M-FLOW` (`T4_MLB_SUBBAND_REGISTRY`, ADR-0039) | **GRANDFATHERED — legacy-but-correct, NOT pending rename.** These strings remain exactly as they are today. They are ACTIVE in `logic_epoch.py` `bands_affected` frozensets, the resolved ledger, and the price archive; renaming them is precisely the live-code churn this decision exists to avoid. |
| NBA | bare `T4-STAGED`, `T4-EVENT`, ..., `T4-PROJ`, `T4-ARITH` (`T4_SUBBAND_REGISTRY`/`T4_SUBBANDS`) | **GRANDFATHERED — legacy-but-correct, NOT pending rename.** NBA is DARK/FROZEN; these names are untouched by this decision regardless of that status. |
| NFL | not yet built | **NEW — adopts `T4NFL-` from its first cell.** The superseded `T4N-` single-letter form (original D2 option a) is explicitly **not** adopted; if any draft or prior session used `T4N-` naming, it is not authorized and must be corrected to `T4NFL-` before that code ships. |
| NHL | not yet built | **NEW — adopts `T4NHL-` from its first cell.** |

A future session must be able to determine grandfathered-vs-new from this table alone: MLB and NBA's
existing strings are correct as-is; any sport built after this ADR's implementation lands uses the
four-letter form from its very first sub-band.

**Lands in:** `src/prediction_market_bot/execution_bands.py` — new sub-band registries for NFL/NHL, each its
own `T4_<SPORT>_SUBBAND_REGISTRY` module-level dict/enum, following `ADR-0039`'s MLB precedent structurally
(a separate registry per sport, not a shared one). No existing `T4_SUBBAND_REGISTRY` (NBA) or
`T4_MLB_SUBBAND_REGISTRY` (MLB) entry is renamed.

**Tradeoff, carried forward from APR-0032 as signed:** two-then-more naming generations coexist
indefinitely — NBA bare, MLB `M`-prefixed single-letter, NFL/NHL/future sports four-lettered. This is
accepted as strictly cheaper than any rename, per APR-0032 D2 Amendment's stated reasoning: a rename touches
live code; grandfathering never does.

---

## 4. D3 — Per-sport epoch inheritance — ADOPTED, option (a)

**Decision as signed:** every sport's `logic_epoch` counter is independent, starting at a fresh epoch 1.
NFL does not inherit MLB's 12 existing `logic_epoch.py` boundaries as epoch 13 onward; the same applies to
every other sport.

**Mechanism:** at the point a sport's first `LogicEpochBoundary` is created, its epoch numbering begins at
1, counted independently of every other sport's counter. MLB's existing 12 boundaries (epochs 1–12 at
APR-0032 drafting time) remain MLB's alone and are not renumbered or extended to cover any other sport.

**Why (per the signed decision, restated for implementers):** `ADR-0054` §4's own discipline requires every
`bands_affected` entry be "verified from diff, never assumed." None of MLB's 12 boundaries have a
diff-verifiable relationship to NFL, NHL, or (for the 11 boundaries logged before this ADR) NBA-independent
code, since that code did not exist when most of those boundaries were logged. Inheriting them would assert
an unverifiable claim about each one. A fresh per-sport counter costs nothing an existing counter doesn't
already cost, and keeps each sport's `clean_n`/`n*` (`APR-0024`) provenance auditable from that sport's own
first resolved bet forward.

**Four-sport application (per APR-0032's 2026-08-21 four-sport note, folded into this decision as signed,
not as a separate open question):** this yields **four independent epoch counters** — MLB (currently at
epoch 12), NBA (a fourth counter already in existence, dark but not epoch-1-virgin), and fresh epoch-1
counters for NFL and NHL each at the point their first `LogicEpochBoundary` is created. This is not a case
requiring re-decision per sport; D3 as signed applies uniformly to every sport this ADR governs (§5) and to
any sport added after it.

**Lands in:** `src/prediction_market_bot/logic_epoch.py` — `LogicEpochBoundary`'s epoch numbering scheme
gains a per-sport counter (mechanism: either a separate epoch sequence keyed by sport, or an equivalent
scoping so that `clean_epoch_floor_for_band`/`is_clean_for_band`-style accessors resolve epoch number
relative to the correct sport's counter, not a single global sequence). The exact data-shape choice (a
`dict[sport, int]` counter vs. per-sport `LogicEpochBoundary` subclassing/namespacing vs. another equivalent
mechanism) is an implementation detail this ADR does not pre-decide; the invariant it does fix is: **no
sport's epoch numbering is derived from, or offset by, another sport's boundary count.**

---

## 5. Scope — governs all four core sports

This ADR governs **MLB, NBA, NFL, and NHL** — the four core sports named in the operator's 2026-08-21
doctrine (APR-0032's four-sport notes, T-480/GG-200) and in `COVERAGE_TARGET_MATRIX.md`. A sport added to
the roster after this ADR is ACCEPTED is an **application** of D1/D2/D3 as already decided here, not a new
decision requiring its own sign-off: it gets one `_SPORT_BY_MARKET_TYPE` entry per `MarketType` member (D1),
a new four-letter-prefixed sub-band registry from its first cell (D2), and its own fresh epoch-1 counter
(D3).

---

## 6. What this ADR deliberately does not decide

- **When any sport is built.** `COVERAGE_TARGET_MATRIX.md`-level sequencing (which sport, in what order, on
  what timeline) is untouched by this ADR. This document governs the *shape* of sport-axis mechanics once a
  sport is built, not the schedule for building it.
- **Any `kelly_fraction` value or `CellStatus`.** No band's sizing or activation status changes as a result
  of this ADR. NFL and NHL are not authorized to trade by this document.
- **`ADR-0054` §8 item 5** (the 12-boundary re-audit for the `(MarketType, band)` cell-key re-type). That is
  a separate, already-named, already-unstaffed follow-on this ADR does not restate, absorb, or block on.
  D3's fresh-epoch-1 decision for *new* sports is independent of whether MLB's existing 12 boundaries are
  ever re-audited against the `(MarketType, band)` key.
- **Whether NFL is authorized to trade.** Building NFL's C1/C2/C3 layers, registering its `MarketType`
  members, and this ADR's sport-axis mechanics landing in code are all prerequisite to, but not the same as,
  authorizing live or paper trading on NFL markets — that remains gated by the project's normal G0–G6
  progression per sport/pool.
- **A retroactive rename of MLB's or NBA's existing band strings.** §3's grandfathering table is exact and
  final for those two sports under this decision; reopening it requires a superseding ADR, not an
  implementation-time judgment call.

---

## 7. GG-198 closure condition

`GG-198` (OPEN — the three sport-axis questions this ADR resolves) does **not** close when this ADR is
drafted or even ACCEPTED. It closes when the implementation named in §§2–4 actually lands in
`market_type_registry.py`, `execution_bands.py`, and `logic_epoch.py` — i.e. when the decisions recorded
here are verifiably code, not merely signed-off text. An implementing session should close GG-198 at that
point, referencing this ADR and the landing commit, not at ADR-acceptance time.

---

## 8. Sign-off

**Status: PROPOSED.** The operator signed APR-0032's D1/D2/D3 decisions (2026-08-21) but has not yet signed
this ADR itself — per this document's own §1 framing and Hard Rule 3, those are distinct acts. This ADR
requires its own explicit operator acceptance before the `src/` changes named in §§2–4 may ship.
