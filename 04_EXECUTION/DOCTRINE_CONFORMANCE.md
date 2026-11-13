# Doctrine conformance audit — code against DOCTRINE.md (W111.2, B-077)

**Audited:** 2026-11-12 (UTC). **Against:** `02_ARCHITECTURE_DESIGN/DOCTRINE.md` (reviewed 2026-11-11), OPERATOR_DIRECTIVES D-04 and D-05, ADR-0077.
**Why this exists:** window error W53. Earlier checks read documents, never code, so "the bot must beat the market" lived in the scoring engine.
**Method:** grep sweep of `src/`, `scripts/`, `12_EXPLORATORY/`, `.claude/commands/`, `04_EXECUTION/` (dashboards, edge map, templates) for verdict words (`no edge`, `ruled out`, `RULED_OUT`, `disproven`, `not mispriced`, `loses to the market`, `beats the market`, `NO_EDGE`), then a read of each hit to see whether it is a **decision** (changes a status, an order, a route or a count) or only **wording**.
**Decision points audited: 41** (rows below).

Plain English key: **CONFORMS** = fits the multi-arm doctrine. **CONTRADICTS** = the code treats "the model lost to the market" as a stop, a ruling out, or a verdict on the pattern. **MISSING** = doctrine requires something no code does yet.

Doctrine rules used:
- **R1** (§1) The bot is layered trees that pick an arm per leaf. The model's own price is one input, never the bet.
- **R2** (§1b) Words: RULED_OUT only for untradeable markets. Human text for a losing pattern is "fade arm closed (routed)" or "routed to <arm> in these leaves".
- **R3** A cell or factor is scored per leaf, net after costs, held out, per arm. Brier against the market may be reported, never the verdict.
- **R4** (§8) Closed cells are provisional; only the operator reopens; no new RULED_OUT until the W111.1 engine fix.
- **R5** A cell that does not beat the market keeps logging and is routed.

## A. Verdict and status engines (W111.1 owns)

| # | Rule | Where | What it does | Verdict | Owner |
|---|---|---|---|---|---|
| 1 | R2 R4 | `pregame_shadow/calibration_engine.py:214,216,225` | Emits RULED_OUT when the CI of delta-Brier vs market/climatology is wholly below zero | CONTRADICTS (D-02, D-03) | 111.1 |
| 2 | R2 R5 | `c5_execution/market_type_registry.py` enum ~447-557 | RULED_OUT is a first-class status for a losing pattern, not only untradeable markets | CONTRADICTS | 111.1 |
| 3 | R4 | `market_type_registry.py` `promote_cell_status` ~886-903 | Guard treats RULED_OUT as terminal | CONTRADICTS | 111.1 |
| 4 | R4 | `market_type_registry.py` ~937-949 | NFL_GAME_TOTAL T1 and T2 seeded RULED_OUT from a Brier look | CONTRADICTS (provisional; B-076 reopens) | 111.1 |
| 5 | R2 | `scripts/proof_calendar.py:233-239` | Prints "CLOSED (RULED_OUT)" and treats a closed cell as having no second look | CONTRADICTS | 111.1 |
| 6 | R5 | `scripts/distance_to_optimum.py:29-33,91-99` | `RULED_OUT_STATUS` cells that still log are not counted in B1 | CONTRADICTS (undercounts logging) | 111.1 |

## B. Order gates and risk (live code, no stake change allowed this wave)

| # | Rule | Where | What it does | Verdict | Owner |
|---|---|---|---|---|---|
| 7 | R1 | `run_t1_mlb_game_market.py:204,272-279` | `REFUSED_NO_EDGE`: no order unless model p beats market p plus vig | CONFORMS as the FADE arm's entry rule; the label reads as a verdict, and there is no other arm at this gate | backlog ticket (route arms at the gate, needs 111.3 router first) |
| 8 | R1 | `run_t1_nfl_game_market.py:220,304-312` | Same gate for NFL | CONFORMS (fade arm only); same note | backlog |
| 9 | R1 | `execution_bands_orchestrator.py:108,180` | "T1 is the gating condition — no edge means no bet": a model-edge test gates every later band | FIXED 2026-11-13 (W114.3, #497 c5b97f4): `decide(..., route=)` takes the router's arm; the model edge is the FADE entry input and a logged field; no-route path unchanged (tested) | done |
| 10 | R1 | `run_t2_mlb_sameday.py:468,488` | `PASS_NO_EDGE` | CONFORMS as fade arm entry; label | backlog |
| 11 | R5 | `c4_risk_engine/risk.py:65,979-1036` | `run_state = "NO_EDGE"` is a monitoring state | CONFORMS (alarm vocabulary, no routing effect); rename later | backlog |
| 12 | R5 | `scripts/edge_rate_trend.py:9,105,162` | NO_EDGE trend state | CONFORMS (alarm only) | backlog |
| 13 | — | `execution_bands.py:572,659` | Per-band Kelly 0 and band comments | CONFORMS (Kelly 0 is the guardrail) | none |
| 14 | — | `c7_monitoring/semantic_contracts.py:484` | Contract text | CONFORMS (not a verdict) | none |

## C. Router and trees (W111.3 owns)

| # | Rule | Where | What it does | Verdict | Owner |
|---|---|---|---|---|---|
| 15 | R1 | `decision_trees/router.py` (IN_SAMPLE gating) | Router gating on in-sample status | NOT AUDITED HERE; 111.3 owns and rewrites it | 111.3 |
| 16 | R1 R3 | `decision_trees/shadow_route.py`, `longshot.py`, `coverage.py` | Arm routing | 111.3 owns | 111.3 |
| 17 | R3 | `12_EXPLORATORY/retro_route/` | Per-leaf retro scoring | 111.3 owns | 111.3 |

## D. Dashboards, edge map, labels (this block fixes in Part B)

| # | Rule | Where | What it does | Verdict | Owner |
|---|---|---|---|---|---|
| 18 | R2 | `scripts/web_dashboard.py:1577,1996,2234-2240` | Labels "RULED OUT", `ruled_out:'R'`, legend "ruled out" | CONTRADICTS (wording) | 111.2 |
| 19 | R2 | `scripts/cell_display_state.py:21` | Maps registry state to display state `ruled_out` | CONFORMS as internal key; display text fixed via #18 | 111.2 |
| 20 | R2 | `visual_dashboard/body.html:67-68,102,120,123,169,218` | "ruled out the NFL game total", "model that loses to the market", "2 RULED_OUT", "edge found or ruled out" | CONTRADICTS (wording) | 111.2 |
| 21 | R2 | `visual_dashboard/body.html:287,296,298` | Legend: "Blocked", "BLOCKED", "RULED OUT" | CONTRADICTS (wording; keep registry value, change label) | 111.2 |
| 22 | R2 | `visual_dashboard/script.js:10,85,101,151` | "model loses to the market", "Engine loses to the market (w = 0)", "HARMFUL — … loses to the market" | CONTRADICTS (wording; says the model lost, not what the tree does) | 111.2 |
| 23 | R2 | `visual_dashboard/script.js:277-278,387` | `SLABEL.ruled_out = "RULED OUT"`, "BLOCKED" counters | CONTRADICTS (wording) | 111.2 |
| 24 | R2 | `visual_dashboard/script.js:461-464` | `NAME.RULED_OUT = 'Fade arm closed (routed)'` | CONFORMS (already the doctrine phrase) | none |
| 25 | R2 | `scripts/build_visual_dashboard_html.py`, `tests/test_visual_dashboard_edge_map.py:63` | Builds the page; test pins status enum | CONFORMS (enum is registry vocabulary); allowlist | 111.2 |
| 26 | R2 R3 | `12_EXPLORATORY/edge_map/EDGE_MAP.md` + `edge_map.json` | 40 hypotheses; rows read "no edge", "RULED_OUT", "nothing vs market", "market wins"; summary says "7 hypotheses are ruled out" | CONTRADICTS (verdict language on patterns; statuses scored as model-vs-market) | 111.2 (docs-only wording; status names stay) |
| 27 | R3 | edge map rows E01, E09, E10, E14 | Scored as model Brier minus market Brier; no per-leaf, per-arm net | PARTLY FIXED 2026-11-13 (W114.3, #499 e862d90): E01 / E10 lead with held-out net per arm (retro_route), Brier last; E09 / E14 say no family is scored yet | E09 / E14 arm tables need retro_route families |

## E. Commands and templates

| # | Rule | Where | What it does | Verdict | Owner |
|---|---|---|---|---|---|
| 28 | R2 | `.claude/commands/vision.md:8` | Tells a terminal the north star is "edge found or ruled out" | CONTRADICTS | 111.2 |
| 29 | R1 R3 | `.claude/commands/status.md:6` | "does the model beat the market is not the question" | CONFORMS | none |
| 30 | R2 | `WAVE_BLOCKS/COMMON_RULES_W99.md:30`, `W110.md:47,54,56,68` | Quote old results as "RULED_OUT", "NOT mispriced after costs" | CONTRADICTS (historical quotes in frozen wave files) | none: frozen history; allowlisted |
| 31 | R2 | `WAVE_BLOCKS/W90_BLOCKS.md`, `W91_BLOCKS.md`, `COMMON_RULES_W92-W110.md` ("89.3/89.4/89.5 no edge") | Same quotes copied wave to wave | CONTRADICTS (wording), but frozen once issued; fix at source in the template generator | strategic window (wave template) |
| 32 | R2 | `COMMON_RULES_W111.md` | Contains the ban and the replacement phrase | CONFORMS | none |

## F. Exploratory scoring and results

| # | Rule | Where | What it does | Verdict | Owner |
|---|---|---|---|---|---|
| 33 | R3 | `12_EXPLORATORY/market_history/score_vs_market.py:69` | Scores a factor only as a competing price (Brier vs market) | FIXED 2026-11-13 (W114.3, #499 e862d90): output leads with `arms` (per-leaf held-out net per arm), Brier is the last labelled line | done |
| 34 | R3 | `12_EXPLORATORY/nhl_engine/run_w84_3.py:6` | "beats the market" Brier-vs-market scoring | FIXED 2026-11-13 (W114.3, #499 e862d90): docstring and `part_b.py` lead with the arm table; its Brier rule is the last, labelled calibration read (part_b.py not run here: needs box data) | done |
| 35 | R2 | `12_EXPLORATORY/20261009_nfl_first_look_expectations/study.py:80` | Probabilities for `RULED_OUT` outcome of the first look | CONTRADICTS (R4); frozen with its pre-registration | none: frozen; allowlisted |
| 36 | R2 | `NFL_FIRST_LOOK_EXPECTATIONS.md`, `nfl_first_look/results_W98_2.md`, `results_W99_2.md` | Pre-registered rule text and results that used RULED_OUT | frozen pre-registration and results; allowlisted | none |
| 37 | R2 R3 | `quant_w104_blend/RESULT.md:32,52`, `mlb_engine/RESULT_W106_4.md:9`, `quant_w109_props/RESULT.md:23`, `nfl_board_v2/results_W93_4.md:47` | "none beats the market", "Does it beat the market? No", "no edge shown" | CONTRADICTS (wording); results of closed blocks | 111.2 only if the file is not a frozen result; otherwise noted |
| 38 | R2 | `quant/blend.py:141`, `quant/bayes_skill.py` | Docstring "beats the market" | CONFORMS (describes a measurement) | none |
| 39 | R3 | `pregame_shadow/first_look_report.py:69-72` | Synthetic "no_edge" test fixtures | CONFORMS (fixtures) | none |
| 40 | R2 | `pregame_shadow/picks_sheet.py:137`; `scripts/run_t3*_diag.py` | Historical diagnostic wording | CONFORMS / frozen | none |
| 41 | R1 | `scripts/first_look_verdicts_read.py` | Reads verdicts from the engine | CONFORMS (reads what row 1 emits); changes when 111.1 lands | 111.1 |

## Counts

- Audited: **41** decision points and label sites.
- CONTRADICTS: **20** (rows 1-6, 9, 18, 20-23, 26, 28, 30, 31, 33-35, 37). By owner: 111.1 = 6, 111.2 = 8 (rows 18, 20-23, 26, 28, 37), 111.3 = 1 (row 9), backlog or strategic window = 3 (rows 31, 33, 34), frozen history = 2 (rows 30, 35).
- MISSING: **1** (row 27: per-leaf arm scoring in the edge map).
- NOT AUDITED, other block's rewrite: **3** (rows 15-17).
- CONFORMS: the rest (rows 7, 8, 10-14, 19, 24, 25, 29, 32, 36, 38-41).

Rows 7, 8, 10 are the important judgment call: they are the fade arm's entry rule and they conform as that, but each is the **only** arm at its gate. That is a MISSING piece of the tree (routing to ride / momentum / no-bet at the order gate), owned by 111.3's router and a later wave, not fixable in this block.

## Hand-offs to other owners (directive_conflicts)

- 111.1: rows 1-6 (engine, registry enum, promote guard, seeded NFL total cells, proof calendar, B1 count).
- 111.3: row 9 (`execution_bands_orchestrator` gates later bands on T1 model edge) and rows 15-17.
- Backlog: rows 7, 8, 10 (arms at the order gate), 27, 33, 34.
