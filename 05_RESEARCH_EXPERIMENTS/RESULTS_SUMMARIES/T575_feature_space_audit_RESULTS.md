# T-575 — Feature Space Audit: Consumed vs. Available-Unwired vs. Absent

**Why this exists:** T-569 found the T4 MLB latency thesis NOT SUPPORTED. The live T4 model is
an extremely simple closed-form binomial with almost no view of the world. A weak model losing
to the market is a weak-model finding, not proof the market is efficient. This audit inventories
what every live model sees, what's already fetched but never reaches a model, and what's absent
entirely — so a future, better-informed thesis test is possible. **Read-only.** No model,
feature, constant, cell-status, or `kelly_fraction` was changed in producing this document.

**Scope:** T-575, operator's 2026-09-24 scoping directive. Deliverables 1 and 2 were produced by
two parallel read-only forks (full findings preserved at
`04_EXECUTION/session_artifacts/T575_deliverable1_consumed_features.md` and
`04_EXECUTION/session_artifacts/T575_deliverable2_available_unwired.md`); Deliverable 4 (correlation
scoping) was completed directly. This file synthesizes all four into the required summary and
corrects T-569's verdict language.

---

## 1. Consumed — what each live model actually sees

| Model | File:line | Class | Inputs (count) | Live? |
|---|---|---|---|---|
| T4 MLB | `run_t4_mlb_live.py:687` `p_hits_gte_threshold` | Closed-form binomial survival function | `h_so_far`, `ab_remaining`, `ba_l10` (or `ba_l10_shrunk` per ADR-0047), `threshold` — **4 inputs** | YES — T4M-PROJ, the only actively-evaluating T4 sub-band |
| T4M-ARITH / T4M-FLOW | (same file, separate code paths) | Code-complete alternate T4 formulations | Not measured — **zero `T4MlbGameContext(` construction call sites anywhere in `run_t4_mlb_live.py`** | NO — unreachable from the live cycle; code-complete but dark |
| T1 MLB (pregame) | `run_mlb_pregame.py` → LR + Platt (ADR-0004) | Logistic Regression + Platt scaling | `ba_l10`, rest days, home/away, `opp_sp_era_l5`, `opp_sp_k9_l5`, `opp_sp_bb9_l5`, `opp_sp_is_known`, `opp_runs_allowed_l10`, `park_factor_hits` (likely inert — see §2), `slg_l10`, `ops_l10`, `hr_rate_l10` — roughly a dozen features, none qualitative/PRF | YES — MLB ACTIVE pool |
| T1 NFL (EXP-027) | `nfl_exp027_adapter.py` | LogisticRegression + CalibratedClassifierCV(sigmoid) | `off_epa`, `def_epa_allowed` (both aggregate sums; `passing_epa`/`rushing_epa` split fetched but not consumed — see §2) | YES, but EXP-027's own verdict is UNDERPOWERED |
| T2 MLB | rule-based binomial-ratio adjustment | — | Batting-slot context (T2 same-day file), no independent quantitative layer beyond T1's carryover | YES |
| T3 (both sports) | rule-based price-drift comparator | — | Price-only, no player/team features | YES |
| NBA (T1/T4/PRF) | — | — | Full PRF/qualitative layer (47 features) is wired here | NO — DARK/FROZEN, standing operator directive |
| NHL | — | — | — | Config-only placeholder; **zero source files exist anywhere in the repo** |

**Headline:** the model at the center of T-569's test — T4M-PROJ — sees 4 scalar inputs. It has
no opponent, park, weather, score, or qualitative signal of any kind. T1 MLB sees roughly 3x
that, but still zero qualitative/PRF signal and a likely-dead park-factor term (§2).

---

## 2. Available-but-unwired — already fetched/computed, never reaches a model

Grouped by the operator's axes (situational / sport / player / team / game / scheme / topic).
Full detail in the fork's scratchpad file cited above; highest-signal items:

- **Situational — live score/game-state.** Fetched at C1 for completed games (`home_runs`/
  `away_runs`), but `MLBLiveBatterState` (T4's live struct) has no score field at all. T4 never
  sees whether it's a blowout or a one-run game. The NBA-side `qualitative_amplifier.py` design
  docs already name this exact concept ("game closeness proxy") — it has just never been built
  for MLB or T4.
- **Player — `get_opp_runs_scored()`.** Computed by `MLBTeamStatsStore`, zero call sites in
  `mlb_features.py`. Cheapest item in this entire inventory — one line of C2 wiring plus a
  contract-column addition; the store-side work is already done.
- **Player — PRF/qualitative framework (PAM v4).** Real, non-stub, populated with real
  classification data (47 features, F-103–F-181). Reaches only NBA (dark/frozen). **Zero PRF
  signal exists in either live MLB book today.** Porting it to MLB is a substantial build (new
  MLB-specific archetype classification, new amplification contexts), not a wiring fix.
- **Sport — NFL `passing_epa`/`rushing_epa` split.** Both fetched raw and stored; `off_epa` is
  derived by summing them at ingestion. EXP-027 consumes only the sum. Flagging as available,
  not recommending pursuit (EXP-027 is UNDERPOWERED, a separate open question).
- **Team — `park_factor_hits` is very likely dead in production (inferred from code structure,
  not live-verified).** It's keyed by venue name, but the C1 fetch that would supply venue name
  was disabled after a CDN 406 error, and the inline comment claiming a team-abbreviation
  fallback exists is not supported by any code path found. If true, T1 MLB has been training and
  scoring on a park-factor feature that silently defaults to neutral (1.000) on every row. This
  is a documentation-vs-implementation contradiction, not something in scope to fix here —
  flagged for the parent/gap log.
- **Team — opponent bullpen quality.** Not fetched at all (not merely unwired) — only the
  probable starter is scored anywhere in C1/C2.
- **Game — weather, doubleheader flag, travel/trip-length.** Not fetched; genuine absences (see
  §3), not unwired data.
- **Scheme — T1↔T4 shared feature reuse.** T4 and T1 MLB are architecturally isolated (ADR-0023)
  with no shared feature path. T4 could in principle join against T1's daily feature CSV for
  pregame context; this is a design question, not a wiring fix.

---

## 3. Absent entirely — not fetched, not computed, not available anywhere in the codebase

Report only — nothing below was procured, subscribed to, or wired.

| Attribute | Source exists? | Integration tier if pursued | Licensing note |
|---|---|---|---|
| Pitcher identity/handedness (beyond starter ERA/K9/BB9) | Would require expanding existing C1 MLB pitcher fetch | Low — same ingestion pattern already in use | Same free-tier source (existing MLB stats API); no new licensing |
| Park factors (functional) | Static 30-venue dict exists but is very likely dead (§2) — this is a "fix the wiring" item, not a true absence | Low-Medium — needs a venue-identification path that survives the CDN 406 | None — data already resident |
| Weather (wind/temp, outdoor parks) | Not fetched anywhere | Medium — new C1 source | Would need a weather API; licensing/cost not evaluated (out of scope) |
| Lineup slot context beyond batting order number | Batting slot itself is wired; deeper lineup-construction context (e.g. platoon splits by slot) is not | Medium | None — extension of existing T2 feed |
| Bullpen state/quality | Not fetched at all | Medium-High — new C1 fetch + new store, not a wiring gap | Same source family as starter stats, likely no new licensing |
| Defensive alignment/shifts | Not fetched anywhere | High — would need a specialized data provider | Likely a paid/licensed source (e.g. Statcast-derived); not evaluated |
| Rest/travel beyond `b2b_flag` | Doubleheader flag and trip-length/timezone signal both absent | Medium — schedule-sequence derivation from existing schedule data | None — derivable from data already fetched |
| Injury signal beyond existing flag | Existing flag's source/coverage not audited in this pass | Unknown | Not evaluated |
| NFL: scheme/personnel/pace/coverage/trenches (equivalents to the above for NFL) | Not fetched; NFL ingestion is narrower than MLB's (team-level EPA only) | High — most of these require play-by-play-derived data (nflfastR-style) | nflfastR itself is open/free; deeper next-gen-stats equivalents are typically licensed |

---

## 4. Cross-position correlation — scoping only (no model designed)

**Direct answer: concurrent bets are currently treated as independent. YES.**

- `risk.py`: zero hits for `correlat*`. No correlation or covariance mechanism exists in C4.
- `run_t4_mlb_live.py`: the only cross-position checks are `_find_open_position_opposite_direction()`
  (intra-book, same-ticker wash-trade block, GG-149) and `_t1_open_position_opposite_direction()`
  (cross-book, same-ticker, alarm-only). Both are same-ticker opposite-direction checks — neither
  is a correlation model, and neither looks at different tickers on the same underlying game.
- The only aggregate protection against concentrated same-game exposure is
  `MAX_PORTFOLIO_DEPLOYMENT_PCT = 0.60` — a blunt, correlation-blind, equity-wide cap.
- ADR-0053 §2.5 explicitly *names* a "game-key correlation group" mechanism (grouping open
  exposure by `(game_id, date)` across ticker families) but states it is **out of accepted
  implementation scope, requiring its own future ADR.** It exists only as a named, unauthorized
  proposal — no code implements it.

No correlation model was designed in producing this answer, per task constraint.

---

## 5. Cheapest high-value additions (judgement, not measurement — explicitly a ranked opinion)

This ranking reflects informativeness-per-unit-of-build-cost as judged by this audit, not a
backtested or measured result. Order:

1. **Wire `get_opp_runs_scored()` into T1 MLB.** Already computed; one line of C2 code plus a
   contract-column addition. Zero new data, zero new risk.
2. **Fix (or formally retire) `park_factor_hits`.** If it is indeed dead, T1 MLB has been
   scoring on a silently-neutral feature — either make it real (needs a venue-identification
   fallback) or remove it and stop implying it's contributing signal. Either resolution is
   cheap; the current silent-failure state is the worst of the three options.
3. **Give T4 a live score/leverage signal.** Requires extending `MLBLiveBatterState` with a
   score field (data likely already reachable via the same ESPN feed T4 already polls) — this
   is the single highest-leverage addition to the model T-569 actually tested, since a
   binomial-only model with zero game-state awareness is close to the weakest plausible model
   for the latency thesis.
4. **NFL `passing_epa`/`rushing_epa` split into EXP-027.** Data already resident; requires new
   accessor methods plus a retrain. Judged lower priority than the MLB items above only because
   EXP-027 is already UNDERPOWERED for other reasons — a richer feature set doesn't fix a small-n
   problem by itself.
5. **Port a minimal PRF/qualitative signal to MLB.** Highest expected informativeness of any
   item in this list (real, populated data; zero PRF signal in either live MLB book today) but
   also by far the most expensive — requires new MLB-specific classification, not just wiring.
   Ranked last on a cost-adjusted basis, not on raw expected value.

---

## 6. T-569 correction

`T569_t4_latency_thesis_RESULTS.md`'s verdict has been corrected in place to
**"NOT SUPPORTED (current feature set)"**, with a scope-correction paragraph naming the four
inputs under test (`h_so_far`, `ab_remaining`, `ba_l10`/`ba_l10_shrunk`, `threshold`) and
pointing to this document. No statistic, table, or number in T-569's original analysis was
re-run or altered — only the verdict framing was corrected, per the operator's directive. T-569's
own gap-candidate note (a GGL entry for the wrong-signed/confound-dominated finding) was already
flagged for session "35.1" inside that file and is unchanged here.

**Handoff to session "35.1":** this document itself, and the T-569 correction, may warrant a
`GOVERNANCE_GAP_LOG.md` entry noting (a) the `park_factor_hits` likely-dead finding (§2) and
(b) that T-569's NOT SUPPORTED verdict is scoped to a 4-input model, not a general market-
efficiency finding — neither is registered here per this session's scope fence (no GGL/DECISION_LOG
ownership).

---

**Sources:** `run_t4_mlb_live.py`, `run_mlb_pregame.py`, `nfl_exp027_adapter.py`,
`mlb_features.py`, `mlb_team_stats_store.py`, `mlb_ingestion.py`, `nfl_ingestion.py`,
`qualitative_store.py`, `qualitative_amplifier.py`, `risk.py`, `execution_bands.py`, `ADR-0023`,
`ADR-0047`, `ADR-0053` §2.5. Full per-model and per-attribute detail preserved in the two fork
scratchpad files referenced above (copied into `04_EXECUTION/session_artifacts/` for durability —
see commit).
