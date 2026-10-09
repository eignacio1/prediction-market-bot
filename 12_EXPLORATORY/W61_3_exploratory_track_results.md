# W61.3 — Exploratory track results (EXPLORATORY — never a verdict)

**Task:** T-753 · **Gap:** GG-533 · **Block:** Wave 61.3 · **Charter:** `CHARTER.md`

## Part A — the fence (2026-10-09)
### A1. What is already known (not redone): where Kalshi sports markets are / are not beatable net of cost
1. EXP-031 (14 families, 2026-08-01→10-01, first-seen snapshot): **zero CANDIDATES.** 10 MLB families labelled; KXMLBHIT is the reference (E −0.0008); every other MLB family is NO BETTER; 4 NFL families INCONCLUSIVE (n/days rule).
2. E = B − null − H is *negative* for every game-market family; the calibration gap B exists (e.g. KXMLBTEAMTOTAL .0257 vs null .0098) but is smaller than the half-spread toll H (.040).
3. T-567 efficiency gradient: KXNFLGAME and KXMLBTOTAL are the most efficient (ERI tier 1; spread ≈2.7–3.0%, depth $1.0k–3.8k); KXMLBHIT and KXMLBF5SPREAD the least (tier 3; spread 11–15%, depth $23–48). Least efficient = thinnest = highest toll.
4. So "less efficient" and "cheaper to trade" point in opposite directions: the inefficiency is largely the cost of trading it.
5. EXP-032 cost surface: H is strongly time-dependent — ~0.5c in the last hours before start vs 1.5–3.0c at 12–48h (TEAMTOTAL), HIT 0.5c→2.5c. EXP-031's first-seen snapshot landed disproportionately in the expensive 24–48h window.
6. EXP-032 headline: **no family's E crosses zero under any policy the archive evidences.** Policy (b) shows E>0 for KXMLBF7/KXMLBTEAMTOTAL only because B is read at one moment and H at another — not tradable.
7. EXP-032 clock gate FAILED for F3/F5/F5SPREAD/F5TOTAL (markets close 1.0–1.7h after start); pregame-clock cost UNMEASURED there.
8. EXP-035 Part 1 (candle reconstruction) FAILED and stays failed (G2 .335, G3 .472); Gate 2 on KXMLBTOTAL alone PASSED 7/7 (G2 .944, B/H/E-sign agree) — candle history is validated for that one family/structure only (store README: NFL KXNFLGAME partial).
9. Archive limits: window is ~2 months (NFL from 2026-09-05); no settlement in the archive (outcomes from Kalshi `result`); NFL families mostly unsettled at EXP-031 time.
10. Net: nothing so far shows a tradable edge net of cost; the only live questions are (i) calibration vs climatology on game markets, (ii) whether a better model beats the *market* by more than H at the cheap pre-start horizon — which is what a challenger must be tested for.

### A2–A3. Fence
- `12_EXPLORATORY/CHARTER.md`, `12_EXPLORATORY/_fence.py` (`safe_out`), `tests/test_exploratory_isolation.py` (AST scan: forbidden imports, forbidden path constants, writes not routed via `safe_out`, network-write shapes, subprocess/exec; 10 negative fixtures + 1 positive; one fixture initially exposed a gap — `os.remove` — fixed before merge).
- Directory name `12_EXPLORATORY` (layout runs 00–11; 12 free).

---

# Part B (EXPLORATORY -- not a verdict, never cite as one)

## B1. Data inventory (copies only, read-only; counts as of 2026-10-09)

| Sport | Market family | Seasons | Rows | Location | Validated |
|---|---|---|---|---|---|
| NFL | KXNFLGAME candles (1m + 60m) + market metadata | 2025 (from Aug-01) | 862 markets; 415 candle sets per period (830 rows each file); 12 markets flagged; ~preseason + partial regular season | `exp_output/KALSHI_HISTORY/markets/` in main tree; `candles/` + `raw/` ONLY in old agent worktree `.claude/worktrees/agent-a622a0ccc3aead20c/` (not in main, not in git) | y: `VALIDATION.json` per-set (sorted, unique, no crossed/null/out-of-range); content sha256 per set |
| NFL | KXNFLSPREAD/TEAMTOT/TOTAL/GAME live snapshots | 2026 only | ~0.5M rows (SPREAD 193k, TEAMTOT 154k, TOTAL 142k, GAME 28k) | `exp_output/PRICE_ARCHIVE/prices_*.jsonl` | archiver output; gate = EXP-031/032 consumption; 2026 = NOT eligible as pre-2026 |
| NFL | outcomes + features (nflverse schedule, team stats) | 2015-2025 | 2015-2025 REG games; train 2015-23, cal 2024, held-out 2025 (272 games) | public nflverse via `NFLIngestionClient` (re-fetchable); frozen `models/nfl_pregame_v1*.json` | y: EXP-037 train script, TI-01 as_of, sha-verified artifact |
| MLB | KXMLB* snapshots (HIT, TOTAL, TEAMTOT, GAME, SPREAD, F3/F5/F7) | 2026 only | ~1.4M rows (TEAMTOT 329k, TOTAL 250k, HIT 510k, SPREAD 149k, GAME 120k, F5/F7/F3 ~0.3M) | `exp_output/PRICE_ARCHIVE/` | EXP-031/032/035 consumed; Gate 2 7/7 for KXMLBTOTAL only |
| MLB | outcomes/features | 2015-2025 | `mlb_feature_matrix.csv` 132,184 rows | `exp_output/MLB/`; `models/mlb_game_pregame_v1*.json` | y: frozen model train 2015-23 / cal 2024 / held-out 2025 |
| NHL | prices | 2026 only (archiver) | not itemized here | `PRICE_ARCHIVE/` | not validated for pre-2026 |
| NHL | outcomes/features | frozen model `nhl_pregame_v1*.json`, held-out reliability report | seasons not stated in artifact JSON (no train_seasons key) | `models/` | partial: held-out reliability md/svg exists |
| NBA | prices | none pre-2026 (Finals clean dataset only: `data/nba_finals_clean_dataset.csv`) | -- | `data/` | NBA is DARK/FROZEN |
| NBA | outcomes/features | train 2016-23, cal 2024, held-out 2025 per `nba_pregame_v1.json` | -- | `models/` | y (held-out file) |

Gap that matters: **no pre-2026 Kalshi prices exist for any sport except the partial 2025 KXNFLGAME candle set**, and that set lives only in an untracked agent worktree. Any price-based study of NHL, NBA, MLB is impossible on pre-2026 data; only Brier-vs-climatology on outcomes is.

## B2. NFL challenger slate

| # | Kind | Candidate | Data available? | Pre-2026 only? | Cost to test | Rank |
|---|---|---|---|---|---|---|
| c | Recalibration | Walk-forward probit-Platt refit (2024 + 2025 weeks < w) on the frozen raw margin | yes (frozen model + schedule) | yes | ~minutes, no feature rebuild | 1 (cheapest) |
| b | Variant | Ridge lambda / EPA window-decay search (8, 0.85, lambda 100 fixed a priori) | yes | yes | feature rebuild per setting, risk of tuning on 2025 | 2 |
| a | Feature | Static roof/dome + division-game flag (point-in-time legal); weather/QB/travel excluded: no PIT source | partial (roof static; dome indicator only) | yes | rebuild + refit, new feature-selection degrees of freedom | 3 |

## B3. Result of candidate (c) -- `20261009_nfl_recal_challenger/` (`results.json`)

Out-of-sample on 2025 REG (n=272 games), Brier of home-win probability:

| | Brier |
|---|---|
| climatology | 0.2476 |
| frozen EXP-037 | 0.2185 |
| challenger (walk-forward recalibration) | 0.2197 |

Challenger minus frozen: **+0.00114** (95% game-bootstrap CI -0.00022 to +0.00254, B=2000, seed 20261009). Late season (week >= 10, n=137): +0.00073 (-0.0010 to +0.0025). **No improvement; sign is marginally worse.** The frozen calibration is not visibly mis-specified on 2025.

Market subset (2025 KXNFLGAME with a 1m candle within 1h before kickoff-30min, n=182 games): Brier frozen 0.2182, challenger 0.2189, **market mid 0.2115**. Model minus mid: +0.0068 (-0.0094 to +0.0227); the market is at least as good as either model and the model is not distinguishable from it. Hypothetical flat $1 on every disagreement at the ask (or opposite bid), net of the k007 fee, no slippage: frozen +0.0072/bet over 176 bets, challenger +0.0066/bet over 175 bets (no CI computed; ~0.7c/bet is far inside noise for n=176 at ~0.5 stdev/bet and ignores half-spread beyond the ask/bid touch, depth and the 30-minute choice of snapshot time). **Do not read the P&L line as edge.**

Caveats: 2025 is the frozen model's own held-out season and the market subset only 182 of ~272 games; ticker-to-game mapping by team codes (JAX/LA/WAS/LV normalized); kickoff from nflverse `gametime` in ET; snapshot time 30 min pre-kickoff was chosen a priori and not scanned.

## B4. Pre-registration

Not warranted. The challenger did not beat the frozen model; no PROPOSED challenger pre-registration drafted. Slate candidates (a) and (b) remain for a later wave; neither should be run against 2025 more than once without a new held-out season, since each looks consumes the same 272 games.

## B5. Defects registered, not fixed (Hard Rule 11)

- Pre-2026 Kalshi candle store (`candles/`, `raw/`, 169M + 368M) exists only in an untracked agent worktree; deleting that worktree loses the only pre-2026 price history. Needs a GG/T entry (operator to assign).

---

# Part C (EXPLORATORY -- operator-approved follow-up, 2026-10-09)

## C1. Candle store preserved
`raw/` (368M) and `candles/` (169M) copied from the untracked agent worktree to the main tree
`exp_output/KALSHI_HISTORY/` (sha256 of `candles/KXNFLGAME.jsonl` identical before/after; both dirs are local-only/untracked,
`*.jsonl` is gitignored). Original left in place. A resumed `fetch` for KXNFLGAME (idempotent, public GETs, 1.5 req/s) was started
to fill the Aug-Sep gap; the listing now shows 892 settled markets (up from 862). Rebuild of `candles/` from the extended `raw/`
is pending (see handoff). Coverage used by Part B (Oct-Jan only) is unchanged until that rebuild and re-run.

## C2. Rolling-origin study (`20261009_nfl_rolling_origin/`, `results.json`)
Pre-declared candidates, fixed before running: base (frozen recipe, lambda 100), lambda 30, lambda 300, base + dome/closed-roof flag
(static, point-in-time legal). Test seasons 2019-2023 only (5 seasons, 1,308 games): per test season T, ridge on 2015..T-2,
probit-Platt + sigma on T-1, score T. 2024/2025/2026 outcomes are never read. Game-bootstrap B=2000, seed 20261009.

| Candidate | Brier | Delta vs base (95% CI) | Seasons better than base |
|---|---|---|---|
| base | 0.22853 | -- | -- |
| lambda 30 | 0.22866 | +0.00014 (-0.00018, +0.00046) | 1/5 |
| lambda 300 | 0.22843 | -0.00010 (-0.00033, +0.00014) | 5/5 |
| base + dome | 0.22869 | +0.00016 (-0.00027, +0.00057) | 1/5 |

**Result: no distinguishable improvement.** lambda 300 is directionally better in all five seasons but the pooled effect is 1e-4 Brier with a CI
spanning zero (about 0.04% of the Brier; not economically meaningful and not a basis for a pre-registration). The dome flag does not help. This
study has no market prices (none exist pre-2025), so it speaks to model accuracy only, not edge over the market.

## C3. Pre-registration
Not warranted. Draft not written. Slate candidates (a) dome flag and (b) lambda are both closed as EXPLORATORY "no improvement";
window/decay variants remain unrun.
