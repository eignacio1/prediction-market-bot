# Session Handoff — SESSION 55
**Date:** 2026-06-12  
**Commit:** `626d1d1`  
**Next action:** Resolve G5 after game, then T-169 DS ruling

---

## What Happened This Session

Four items completed, continued from a context-resumption mid-sprint.

**T-168 / GG-030 RESOLVED — MC correlated simulation fix**

`simulate_portfolio()` in `scripts/run_monte_carlo.py` was drawing independent Bernoullis per position (T-167's SESSION 53 rewrite). Fixed: one Poisson score drawn per player per simulation, matching the already-correct `--preview` mode. Lambda inferred via `_infer_lambda()` — least-squares fit to each player's `(threshold, model_p)` pairs using `scipy.optimize.minimize_scalar(bounds=(0.1, 80))`. Direction-invariant: `model_p = P(score ≥ threshold | lambda)` regardless of YES/NO; `_infer_lambda()` always uses raw `b["model_p"]`.

Bug found and fixed in `_infer_lambda()`: initial implementation used `1.0 - b["model_p"]` for NO bets. This inverted the Poisson distribution — a NO bet with model_p=0.001 (99.9% p_win) was inferred as lambda where P(score ≥ threshold)=0.999, flipping all win/loss flags. Fixed output before fix: "MC avg bets won: 0.0, P(profit): 0.0%". After fix: "avg bets won: 3.0, P(profit): 97.1%".

G5 VPS MC output (corrected, 41 positions):
- P(profit): 98.3%
- **Kill-switch risk: 1.28%** (loss ≥ $20; ADR-0012 15% × $130.62 bankroll)
- Mean P/L: +$244.23, std $95.25
- Worst case: -$259.56 (exceeds bankroll — paper)
- 9 FAIL (duplicate) tickers both included in default run

The previous 0.00% kill-switch figure (SESSION 52) was structurally wrong — independent Bernoulli draws cannot represent correlated threshold ladder losses.

---

**GG-031 registered — GG-028 blast radius understated**

Direct VPS audit found 9 duplicated (ticker, direction) pairs totaling $402.49 of doubled exposure, not 2 as documented in SESSION 52/53. Full list: Brunson NO×4, Hart YES×2, KAT YES×1, Wemby NO×2. All follow identical pattern: `failed: transient` at 18:0x UTC primary batch → `resting` at 01:30 UTC late cron.

The "mystery 01:00 UTC trigger" investigation is CLOSED — it was the scheduled 01:30 UTC late PIPE-03 window in `cron.conf`. No mystery; no anomalous trigger.

T-169 registered: DS ruling on 9 twins needed post-G5 resolve.

---

**GG-032 registered + T-170 RESOLVED — T4 ledger corrected**

`paper_portfolio_t4.json` header fields were irreconcilable:
- `bankroll_usd: $1,869.68` — WRONG
- `initial_bankroll_usd: $1,000.00` — WRONG
- `total_realized_pnl: -$21.59` — correct (verified against position-level sum)

Root cause: ADR-0022's `_reconstruct_t4_ledger()` wrote the T1 system bankroll (~$1,869) into T4's `bankroll_usd` field. True T4 pool: $500 initial + (-$21.59 realized) = **$478.41**.

Corrected on VPS. Backup at `logs/paper_portfolio_t4.json.bak_t170`. `_t170_correction_note` added to file for audit trail.

**Do not cite the "+87% T4 growth" narrative** — it was comparing $1,869 bankroll to $1,000 initial, both wrong fields. True T4 performance: $478.41 vs $500 start = -4.3%.

---

## Strategic Decisions This Session

1. **`_infer_lambda()` is direction-invariant** — model_p always means P(score ≥ threshold | lambda). Direction determines which side of the threshold wins, not the lambda. This is mathematically grounded: the underlying scoring process is shared; YES and NO are bets on opposite sides of it.

2. **GG-030 governance footer updated** in `run_monte_carlo.py`: replaces the "independent Bernoulli draws" disclaimer with the GG-030 resolved note and explicit description of the correlated simulation approach.

---

## Open Items for Next Session

**Immediate (post-G5 resolve):**
- Run `run_resolve_local.py` to settle 41 G5 positions
- Re-run `run_exp017.py --from-pregame` (EXP-017B G5 data)
- Re-run `run_exp018.py` (EXP-018 G5 data)
- **T-169 DS ruling**: are 9 twin positions annotated as `duplicate_of` (Option A, conservative — exclude from experiment n) or accepted as double exposure (Option B, permissive)?

**Note from governance scan:** Local portfolio shows Resolved: 114. G6 statistical floor is 66. If VPS resolves G5 cleanly, G6 paper evidence count should be well above floor. The binding G6 constraint remains GG-004 (EXP-017 Part B commercial validation), not bet count.

**Dark period (standing):**
- T-153: fill-realism haircut on all G6-facing P&L
- T-156: ADR-0012 amendment (net vs gross daily-loss semantics)
- T-159: portfolio state-machine invariant tests

---

## System State

| Item | Value |
|------|-------|
| VPS bankroll (T1) | $130.62 |
| G5 deployed | $1,003.38 (41 positions, game_date=2026-06-13) |
| G5 MC (corrected) | P(profit)=98.3%, kill-switch=1.28%, mean P/L=+$244 |
| T4 pool (corrected) | $478.41 (was $1,869.68 — artifact) |
| GG-004 | OPEN — EXP-017B needs MLB/regular-season scale |
| GG-017 | OPEN — ADR-0019 Tier 2 empirical gate |
| GG-022 | OPEN — fill-realism haircut (T-153) |
| GG-027 | OPEN — PAM T2/T3/T5 wiring (low severity) |
| GG-031 | OPEN — 9 twin bets, T-169 DS ruling pending |
| Commits | `530e1c3` (T-168 fix) + `626d1d1` (close artifacts) |
| Tests | 851/852 (1 pre-existing timing flake) |
