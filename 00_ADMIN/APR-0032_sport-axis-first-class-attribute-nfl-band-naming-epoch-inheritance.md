# APR-0032 — Sport as a First-Class Attribute, NFL Band-Naming Convention, NFL Epoch Inheritance (GG-198)

**Status:** DRAFT — decision request. This document presents three related sport-axis questions with
options, evidence, and a recommendation each. It does not decide any of them and does not authorize any
`src/` change. Per Hard Rule 3, if the operator accepts a recommendation below, a superseding ADR (most
likely folded into or following `ADR-0054`) would still be required before any `market_type_registry.py` /
`execution_bands.py` / `logic_epoch.py` change ships.
**Touches (if accepted):** `src/prediction_market_bot/c5_execution/market_type_registry.py` (`MarketType`
enum, D1); `src/prediction_market_bot/execution_bands.py` (`ExecutionBand` enum / sub-band registries, D2);
`src/prediction_market_bot/logic_epoch.py` (`LogicEpochBoundary.bands_affected`, D3). No file is modified by
this document itself.
**Drafted:** 2026-08-20/21, T-473
**Prior context:** `ADR-0054` (PROPOSED, 2026-08-19, §4) decided the Phase 3 cell key is `(MarketType,
band)`, not `(sport, MarketType, band)` — correct for the question it asked, but it did not separately ask
whether `(MarketType, band)` is *sufficient*, on its own, for the sport-*grouping* operations Phase 3 will
need once a second sport (NFL, per `COVERAGE_TARGET_MATRIX.md`) is added. `ADR-0054` §8 item 5 already names
a 12-boundary re-audit as unstaffed, for the `(MarketType, band)` re-key specifically — this document is
about a different, adjacent axis that re-audit does not cover. Motivating gap: `GOVERNANCE_GAP_LOG.md`
GG-198.

---

## Why This Proposal Exists

Phase 3 is about to build cell keys. Three sport-axis questions currently have no recorded answer. If Phase
3's implementation reaches a decision point on any of them, it will answer them by whatever is convenient at
that moment — not by an operator decision — and that implicit answer propagates into every `bands_affected`
frozenset written from that point forward, and into the next `(MarketType, band)`-keyed re-audit ADR-0054
§8 already flags as unstaffed. Deciding these three questions in writing now costs a page. Retrofitting a
different answer later costs redoing that 12-boundary audit twice — once for the cell-key re-type ADR-0054
already scoped, once again for whichever of these three answers turns out wrong.

---

## Verified Premise (direct read, this session)

**1. Sport is a naming convention today, not a field.**

```
$ grep -n "class MarketType" -A 20 src/prediction_market_bot/c5_execution/market_type_registry.py
59:class MarketType(Enum):
    ...
72:    MLB_PLAYER_PROP_HITS = "mlb_player_prop_hits"
73:    MLB_MONEYLINE = "mlb_moneyline"
74:    MLB_RUN_LINE = "mlb_run_line"
75:    MLB_GAME_TOTAL = "mlb_game_total"
76:    MLB_TEAM_TOTAL = "mlb_team_total"
77:    MLB_PARTIAL_GAME = "mlb_partial_game"
78:    NBA_PLAYER_POINTS = "nba_player_points"

$ grep -in "sport" src/prediction_market_bot/c5_execution/market_type_registry.py
61:    A tradeable market family, scoped by sport where the family is
62:    sport-specific (player prop families do not share a series across sports).
154:# any new sport.
291:        reason unrelated to measurement (sport tabled, off-season, etc.).

$ grep -rn "sport_for\|def sport\b" src/
(no matches)
```

Every member is sport-scoped by name prefix; `sport` never appears as code — only in prose. There is no
`sport` attribute, no `sport_for()` lookup, nowhere in `src/`.

**2. The band axis already encodes sport, asymmetrically.**

```
$ sed -n '42,93p' src/prediction_market_bot/execution_bands.py
```
`ExecutionBand` defines bare `T4-STAGED` / `T4-EVENT` / ... / `T4-PROJ` / `T4-ARITH` (NBA, under
`T4_SUBBAND_REGISTRY`/`T4_SUBBANDS`), then separately defines `T4M-PROJ` / `T4M-ARITH` / `T4M-FLOW` (MLB,
under a distinct `T4_MLB_SUBBAND_REGISTRY`, ADR-0039) — an `M`-prefixed convention that exists only because
MLB was added second and needed to avoid colliding with NBA's un-prefixed names. Nothing chose this pattern
deliberately for reuse; it is what NBA-first, MLB-second produced.

**3. Epoch boundaries are band-keyed strings, sport-blind, 12 of them.**

```
$ grep -c "LogicEpochBoundary(" src/prediction_market_bot/logic_epoch.py
12
$ grep -n "bands_affected" src/prediction_market_bot/logic_epoch.py | head -20
```
Every `bands_affected` value is a `frozenset[str]` of bare band strings (`{"T4M-PROJ"}`, `{"T1"}`,
`{"T1","T2","T3","T4M-PROJ"}`, `ALL_BANDS`). `ADR-0054` §4 already confirms this machinery "is zero-aware of
`market_type`" for the `(MarketType, band)` question; it is equally zero-aware of sport, since sport isn't a
distinct axis anywhere in the codebase today — it is encoded only in band and MarketType *string content*
(`T4M-` prefix, `MLB_` prefix), never in a queryable field.

---

## D1 — Should `sport` become a first-class attribute on `MarketType`?

**The `(MarketType, band)` cell key (ADR-0054 §4) is correct and should stand as-is.** No two `MarketType`
members can collide on sport — every member is already sport-scoped by construction (`MLB_MONEYLINE` vs. a
hypothetical `NFL_MONEYLINE` are different enum members regardless of whether `sport` exists as a field).
Adding `sport` would not change what the cell key *distinguishes*. This document does not propose reopening
ADR-0054 §4's `(MarketType, band)` decision or adding a third key axis.

**What `(MarketType, band)` alone cannot do is *group* by sport**, and two operations Phase 3 needs are
group operations, not distinguish operations:

- **"One epoch bump, every MLB cell starts at zero the same day."** Today this requires enumerating every
  MLB `MarketType` member and every MLB band string by hand at the call site that constructs a
  `LogicEpochBoundary` — there is no `for cell in cells_where(sport="MLB")` to write. A hand-enumerated list
  silently drifts the moment a new MLB `MarketType` or band is added and the enumeration isn't updated
  alongside it — the same class of silent-drift failure `ADR-0054` §4 already diagnosed for the
  `(MarketType, band)` collapse (GG-077-style: a change that should scope to N cells instead scopes to
  0 or to all).
- **"The NFL arm's cells graduate separately from MLB's."** `GOVERNANCE_GAP_LOG.md`'s existing
  "Gaps by Arm" classification (NBA=23/MLB=57/Core=46, T-374) is already done *by hand*, "manual content
  review... not a keyword match" per that section's own methodology note — i.e. the project already wants
  sport-level grouping badly enough to do it manually for gap tracking. A `sport` field would make that
  grouping a query instead of a read-every-entry pass, for gaps, for `run_power_calc.py::run_all_cells()`
  output, and for epoch bumps alike.

### Options

| Option | Mechanism | Cost | Risk |
|---|---|---|---|
| **(a) Add `sport` as an enum attribute or `_SPORT_BY_MARKET_TYPE` map** (recommended) | Alongside the existing `_SERIES_TICKER_BY_MARKET_TYPE`-style map, add `_SPORT_BY_MARKET_TYPE: dict[MarketType, str]`, or give `MarketType` itself a `.sport` property. Every current and future member gets one entry. | Small — one map/property, one entry per existing member (7 today), enforced-at-construction the same way `MarketTypeCell.__post_init__` already enforces `reason`/`measured_date` for `RULED_OUT`. | Low. Additive; does not touch the cell key. |
| (b) Leave sport as a naming convention (status quo) | Continue inferring sport from `MarketType.value.split("_")[0]` or equivalent string parsing wherever grouping is needed. | Zero now; grows with every call site that needs grouping — each one re-derives sport from a string, each one is a place the derivation can silently diverge (exactly GG-191's pattern — ticker-date derivation duplicated across five call sites, hardcoded to one shape, silently wrong on any non-match). | Medium — GG-191 is a live, recent (2026-08-19) example of this exact failure class in this codebase, on a different field. |
| (c) Add sport as a third key axis, `(sport, MarketType, band)` | Reopens ADR-0054 §4. | High — full re-audit of all 12 epoch boundaries a second time, plus every `MarketTypeCell` constructor call site. | High, and unnecessary — `(MarketType, band)` already distinguishes every cell; adding sport to the key conflates "distinguish" with "group," which are different operations with different natural mechanisms (a key vs. a lookup/index). |

**Recommendation: (a).** Add the attribute; do not touch the cell key. This is additive, has essentially no
implementation risk, and directly serves the two group-operations named above without reopening any
already-decided question.

**Four-sport note (2026-08-21, T-480/GG-200 — strengthens, does not change, the recommendation above.)**
Operator doctrine as of 2026-08-21: all four core sports (MLB, NBA, NFL, NHL) are being built. That raises
"group by sport" from a convenience to a hard requirement — Phase 3's coverage target is heading toward
~100 cells (5 bands × ~5 market types × 4 sports) across four independent epoch counters (see D3's own
four-sport note below), not the two-sport MLB/NFL case this section was originally scoped against. The
existing hand-maintained "Gaps by Arm" split in `GOVERNANCE_GAP_LOG.md` (NBA=23/MLB=57/Core=46, T-374)
becomes a four-way split under this roster, done by hand at four times the surface area — option (a)'s query
becomes correspondingly more valuable, not less. Recommendation unchanged: (a).

---

## D2 — NFL Band-Naming Convention

MLB's `T4M-` prefix (ADR-0039) exists because NBA was first and NBA's bare `T4-PROJ` etc. already occupied
the unprefixed names. Nothing has decided what a third sport does. Left undecided, Phase 3's first NFL
sub-band gets named by whichever session writes it first — likely by analogy to MLB's prefix, but not
because anyone chose that as the standing convention.

### Options

| Option | Mechanism | Cost | Risk |
|---|---|---|---|
| **(a) Extend the ad-hoc letter convention: `T4N-PROJ` etc.** (recommended for near-term) | NFL gets its own `T4_NFL_SUBBAND_REGISTRY`, prefix `N`, mirroring MLB's `M` pattern exactly (ADR-0039 as template). | Low — direct copy of an already-accepted pattern; ADR-0039's precedent already answers "how do we do a third parallel registry" procedurally. | Low near-term. Medium long-term: a 4th, 5th sport repeats the same ad-hoc choice each time, and the letter has to be picked by hand and checked for collision (`N` for NFL vs. a hypothetical NHL — both start with N). |
| (b) Normalize MLB/NBA asymmetry first (retrofit NBA to `T4B-` or similar, or promote sport-prefixing as a stated rule with codified letters before NFL exists) | Rename NBA's existing bare `T4-*` bands to a prefixed form, then add NFL under the same normalized rule. | High — every existing NBA `T4-*` reference (code, logs, `EXECUTION_BANDS.md`, historical `bands_affected` entries) would need updating or a compatibility shim; NBA is DARK/FROZEN (operator directive) so this is non-trivial churn on code nobody is actively running, for a naming-only benefit. | Medium — touches dormant code, but "dormant" doesn't mean risk-free (silent breakage would only surface when NBA work resumes ~1 month before 2026-27 season, per `project_nba_deferred.md`, i.e. discovered late). |
| (c) Do nothing; let Phase 3 choose implicitly | No decision recorded. | Zero now. | This is the status quo this APR exists to prevent — see "Why This Proposal Exists" above. |

**Recommendation: (a).** Extending the existing ad-hoc convention (`T4N-PROJ`) is the lowest-cost, most
consistent-with-precedent option, and does not require touching NBA's dormant code. It does not solve the
long-term "letter-collision" risk for a 4th/5th sport, but that risk is speculative and out of scope for a
decision that only needs to cover the next sport actually named in `COVERAGE_TARGET_MATRIX.md` (NFL).
Flagging (b) as the option to revisit if/when a third *live* sport (beyond MLB/NFL) makes the ad-hoc pattern
start to strain — not now.

*(The recommendation above and everything preceding it in D2 is the original 2026-08-20 record. It stands as
written — this section amends it in place rather than replacing it, per the amendment below.)*

### Amendment (2026-08-21, T-480/GG-200)

**(i) Doctrine change.** Operator, 2026-08-21: all four core sports — MLB, NBA, NFL, **NHL** — are being
built. Which cells calibrate edge is discovered per-cell (that is still open, per-band, per APR-0024); whether
a sport gets built is not open. D2's original recommendation was drafted 2026-08-20, one day before this was
stated, against a roster of MLB/NBA/NFL only.

**(ii) Why this inverts (a)'s cost argument.** The original text rated the "letter-collision" risk — `N` for
NFL colliding with a hypothetical NHL, both starting with N — as "speculative and out of scope... not now,"
explicitly reserving it for revisit "if/when a third *live* sport (beyond MLB/NFL)" appears. Under the
four-sport roster, NHL is not hypothetical and not a future revisit trigger — it is the next sport in the
same roster this document is scoping *right now*. The collision is scheduled, not speculative, and the
premise that justified deferring it no longer holds.

This also inverts the asymmetry the original text used to prefer (a) over (b): (b) was rejected because
renaming NBA's bare `T4-*` names is "churn on code nobody is actively running" (NBA is DARK/FROZEN). That
asymmetry doesn't transfer to an `N`→NHL collision — by the time NHL's sub-bands need naming, NFL's `T4N-*`
bands are exactly the kind of code D2 protected NBA from having to rename: potentially ACTIVE, trading,
appearing in `bands_affected` frozensets, the resolved ledger, and the price archive, the same way MLB's
`T4M-PROJ` string does today. Extending (a) as originally scoped defers the same live-code rename risk it was
chosen to avoid — one sport later.

**(iii) Revised recommendation (presented as recommendation, not decision — D2 remains unsigned).** Adopt an
explicit sport-code convention up front, covering all four sports: `T4MLB-`, `T4NBA-`, `T4NFL-`, `T4NHL-`.
Existing `T4M-*` (MLB) and bare `T4-*` (NBA) names are **grandfathered, not renamed** — MLB's `T4M-PROJ` is
the only ACTIVE cell today and its string appears throughout `logic_epoch.py` `bands_affected`, the resolved
ledger, and the price archive; renaming it is exactly the live-code churn this document exists to avoid, for
MLB now instead of NFL later. New sub-band registries (NFL's, NHL's, when each is built) adopt the longer
four-letter form from their first cell.

**Tradeoff, stated honestly:** this leaves two naming generations coexisting indefinitely — NBA bare, MLB
`M`-prefixed, NFL/NHL/future sports four-lettered. That is uglier than a single uniform scheme. It is still
strictly cheaper than any rename, because a rename touches live code (grandfathering never does) and because
a third naming generation later (if a fifth sport ever collides) costs the same regardless of how many
generations already exist — the ugliness doesn't compound, the rename risk would.

**Alternative, for the operator to weigh rather than this document deciding it:** accept `T4N-PROJ` now per
the original (a), and rename at NHL-build time instead of pre-empting it. Cost: whenever NHL is actually
built, NFL's `T4N-*` bands must be renamed if NFL is by then ACTIVE — the same class of live-code churn (band
strings in `bands_affected`, resolved ledger, price archive) that the original D2 text used as its reason to
reject retrofitting NBA. This alternative trades a smaller cost now (one four-letter convention decision) for
a deferred, larger, and by-then-live-code cost later, on a collision this document can already see coming.

---

## D3 — NFL Epoch Inheritance

When NFL cells are created, do they inherit MLB's 12 existing `logic_epoch.py` boundaries, or start fresh at
epoch 1 for NFL specifically? This is a one-line decision — which epoch number NFL's first `clean_n`
computation starts counting from — with permanent consequences: every NFL `clean_n` downstream, and every
`n*` power calculation (`APR-0024`) that reads it, depends on which resolved bets count as "post the last
logic-breaking change" for NFL.

### Options

| Option | Mechanism | Cost | Risk |
|---|---|---|---|
| **(a) Fresh epoch 1 for NFL** (recommended) | NFL's `logic_epoch` counter starts independently of MLB's; NFL's first `LogicEpochBoundary` is epoch 1, unrelated to MLB's epoch 12. | Low — no need to retroactively decide whether any of MLB's 12 historical boundaries "actually" affected NFL code that didn't exist yet at the time each was logged. | Low. Correct by construction: none of MLB's 12 boundaries were caused by, or diff-verified against, NFL code — inheriting them would be inheriting boundaries with no verifiable NFL blast radius, which is exactly the un-auditable state ADR-0054 §4 is trying to move *away* from for MLB itself ("verified from diff, never assumed"). |
| (b) Inherit MLB's 12 boundaries as NFL's starting epoch (i.e. NFL's first boundary is epoch 13) | Treat epoch as a single project-wide counter shared across sports. | Low to write, but every one of the 12 existing boundaries would need retroactive classification ("did this affect NFL?") for a sport whose code didn't exist when 11 of the 12 were logged — an unanswerable question for most of them, since "verified from diff" (ADR-0054 §4's own standard) requires a diff against code that predates NFL's existence. | High — either fabricates a NULL-provenance answer for 11+ boundaries (violates the "verified from diff, never assumed" discipline ADR-0054 explicitly commits to), or forces `ALL_BANDS`/all-cells treatment on all of them for NFL, which zeros NFL's `clean_n` at NFL's very first cell for no code reason. |

**Recommendation: (a).** Fresh epoch 1 for NFL. This is the option consistent with `ADR-0054` §4's own stated
discipline (every `bands_affected` entry "verified from diff, never assumed") — MLB's 12 boundaries have no
diff-verifiable relationship to code that doesn't exist yet, so inheriting them would mean asserting an
unverifiable claim about every one of them. A fresh counter costs nothing MLB's counter doesn't already cost,
and keeps NFL's `clean_n`/`n*` provenance auditable from NFL's first bet forward.

**Four-sport note (2026-08-21, T-480/GG-200 — strengthens, does not change, the recommendation above.)**
Under the four-sport roster (MLB, NBA, NFL, NHL all being built), this decision recurs three more times, not
once — NHL needs the same fresh-epoch-1 call NFL does, and NBA (dark today, not epoch-1-virgin) is a fourth
independent counter already in existence. Four independent epoch counters is the only arrangement that keeps
each sport's `clean_n` provenance auditable against that sport's own code history — inheriting any other
sport's boundary numbering multiplies the "unverifiable claim about a boundary that predates this sport's
code" problem D3 already rejects for the two-sport case, once per additional sport. Recommendation unchanged:
(a), independently, for every sport.

---

## What This Does NOT Claim

- **Does not authorize any code change.** This is a decision-request document; `src/` is untouched.
- **Does not reopen `ADR-0054` §4's `(MarketType, band)` cell-key decision.** D1 explicitly recommends
  leaving that key as-is and adding sport as a grouping attribute alongside it, not inside it.
- **Does not decide whether/when NFL is actually built.** That is a `COVERAGE_TARGET_MATRIX.md`-level
  sequencing question, separate from these three axis decisions, which only need to be settled *before*
  Phase 3 reaches a point where it would otherwise decide them by accident.
- **Does not resolve `ADR-0054` §8 item 5** (the 12-boundary re-audit for the `(MarketType, band)` re-key).
  That is a separate, already-named, already-unstaffed follow-on this document does not restate or absorb.
- **Does not change GG-198's OPEN status** until the operator decides D1–D3 and, if any recommendation
  above is accepted, a superseding ADR is drafted and implementation lands.

---

## Broken-System Test

| Failure mode | How this draft prevents it |
|---|---|
| Phase 3 writes NFL's first `MarketTypeCell` and needs "group by sport" for an epoch bump; a session invents a hand-rolled string-parsing helper under time pressure, duplicating the `sport`-from-name-prefix logic ad hoc (GG-191's exact failure pattern, on a different field) | D1 names the two group-operations explicitly and recommends a single first-class attribute instead of letting each call site re-derive sport from string content |
| A future session names NFL's first T4 sub-band `T4-NFL-PROJ` or `T4NFL_PROJ` or some other one-off spelling, inconsistent with either existing sport's pattern, because no convention was ever chosen | D2 names the ad-hoc-extension option as the recommended default, citing ADR-0039 as the direct procedural template |
| NFL's `clean_n` silently starts counting from MLB's epoch 13, and a future commercial-validation read (APR-0024, GG-004-style) treats an inherited-but-unverifiable epoch boundary as a real logic-epoch reset for NFL, when no NFL code diff ever justified it | D3 recommends fresh epoch 1 specifically to avoid asserting an unverifiable per-boundary NFL relevance claim, citing ADR-0054 §4's own "verified from diff, never assumed" standard as the reason |
| A reader assumes this document also resolves ADR-0054 §8 item 5 (the 12-boundary re-audit) since both concern epoch/band mechanics | Named explicitly under "What This Does NOT Claim" as a separate, already-scoped, still-unstaffed item |

---

## Review Checklist (for operator, when this is reviewed)

- [ ] D1 — Decision: add `sport` as a first-class `MarketType` attribute/map (recommended), keep it as a
      naming convention only, or fold sport into the cell key itself (not recommended)
- [ ] D2 — Decision: extend MLB's ad-hoc `T4M-`-style prefix convention to NFL as `T4N-` (recommended),
      normalize the MLB/NBA asymmetry first, or leave undecided for Phase 3 to choose implicitly (not
      recommended — this is the status quo the APR exists to end)
- [ ] D3 — Decision: NFL starts at a fresh logic-epoch 1 (recommended), or inherits MLB's 12 existing
      boundaries as NFL epoch 13 onward (not recommended)
- [ ] Acknowledged: none of these three decisions reopen ADR-0054 §4's `(MarketType, band)` cell-key
      decision or its own §8 item 5 (12-boundary re-audit), which remain separate, already-scoped follow-ons
- [ ] Acknowledged: this draft does not authorize implementation; a superseding ADR is required per Hard
      Rule 3 before any `market_type_registry.py` / `execution_bands.py` / `logic_epoch.py` change ships

**Sign-off:** _not yet submitted for operator review_
**Date:** _n/a_
**Role:** _n/a_
