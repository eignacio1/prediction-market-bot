# Ledger Invariant Suite — T-432/BLOCK B

**Deliverable:** `scripts/assert_ledger_invariants.py` + `tests/test_assert_ledger_invariants.py` + wiring into `.claude/hooks/governance_scan.sh` and `CLAUDE.md` Q7.
**Mode:** ALARM-ONLY, non-negotiable (operator directive). Exits 0 regardless of findings unless `--strict` is passed explicitly. `--strict` is reserved, off by default, wired to nothing.
**Why:** GG-166 corrupted ~44% of the epoch-12 clean cohort's outcomes/P&L, was baked into four analysis sessions, and was only caught when an independent decoupled-store data path disagreed with the ledger. Nothing in the session-start protocol, gap log, or session-end checks a VALUE is correct — only that a step was run.

---

## Running it

Data sources (`logs/paper_portfolio_mlb.json`, `logs/paper_portfolio_mlb_t4.json`, `logs/t4_mlb_outcome_store.jsonl`) are gitignored, VPS-fetched, local-only artifacts — a fresh checkout will not have them. Fetch (read-only) before running:

```bash
scp prediction-market-vps:/opt/prediction-market-bot/logs/paper_portfolio_mlb.json logs/
scp prediction-market-vps:/opt/prediction-market-bot/logs/paper_portfolio_mlb_t4.json logs/
scp prediction-market-vps:/opt/prediction-market-bot/logs/t4_mlb_outcome_store.jsonl logs/
python3 scripts/assert_ledger_invariants.py --t1-portfolio logs/paper_portfolio_mlb.json --t4-portfolio logs/paper_portfolio_mlb_t4.json
```

**GG-238 (2026-09-03):** the filenames above were GG-235's original defect (the old `.vps_portfolio_cache_mlb*.json` names no longer exist on the VPS — confirmed by direct `ls` there). Fixing the `scp` commands alone is not sufficient to make the plain `python3 scripts/assert_ledger_invariants.py` invocation (no flags) work end-to-end: the script's own `DEFAULT_T1_PORTFOLIO`/`DEFAULT_T4_PORTFOLIO` constants are hardcoded to the same stale `.vps_portfolio_cache_mlb*.json` names and were not corrected when the VPS-side files were renamed. Until that script is patched (out of scope for this doc fix — see GG-238), invoke it with the explicit `--t1-portfolio`/`--t4-portfolio` flags shown above rather than relying on its defaults.

If a source is absent, the script reports `SOURCE_UNAVAILABLE` for the affected assertions/bands and still exits 0 — it never crashes into a gate failure and never treats a missing file as a violation.

`.claude/hooks/governance_scan.sh` already runs this every session (without `--strict`, exit code discarded via `|| true`) and prints its stderr summary — routine sessions do not need to run it by hand.

---

## Assertion table — operator's original baseline vs. measured (2026-08-11)

Ticker regex used throughout: `^KXMLBHIT-(\d{2})([A-Z]{3})(\d{2})(\d{4})([A-Z]{4,6})(G[12])?-([A-Z]+?)(\d+)-(\d+)$` (groups: YY, MON, DD, HHMM, TEAMS, doubleheader?, PLAYER, jersey, threshold).

| # | Assertion | Operator's baseline | Measured (this task) | Disposition |
|---|---|---|---|---|
| A | ticker date == game_date | T4: 1,443/2,416 (59.7%); T1: 0/0 | T4M-PROJ: 459/2,516 (18.2%) overall, **438/627 (69.9%) within epoch 12 specifically**; T1: 0/499 | **Kept as-is.** Numbers differ from the operator's cited baseline (different n and denominator — measured fresh against the live portfolio caches, not the file the original figure was drawn from); per the operator's own evaluation criterion, the fresh directly-verified number is authoritative. The epoch concentration is the real finding: this is a **live, current-epoch regression** (GG-170, OPEN), not legacy residue. |
| B | ticker threshold == kalshi_threshold | 0/0 both | T1: 0/499; T4M-PROJ: 0/2,516 | Kept as-is. Clean, confirmed. |
| C | 0 < entry_price_paid ≤ 1 | T4: 2,229/2,416 (92.3%) viol; T1: 485/485 (100%) viol | T1: field absent on all 499 (n/a); T4M-PROJ: 627 applicable (1,889 absent), 0 violations | **Corrected with a presence guard**, per brief. The operator's own baseline was flagged as a spec error — `entry_price_paid` is an ADR-0050/epoch≥12/T4M-PROJ-only field; T1 never has it and pre-epoch-12 T4M-PROJ rows never have it. Coercing "absent" into "violates 0<x≤1" is exactly the false-positive pattern PRESENCE GUARD exists to prevent. Corrected assertion is 100% clean where the field actually exists. |
| C2 | 0 ≤ mid_price_at_entry ≤ 1 | 0/0 both | T1: 0/499; T4M-PROJ: 0/2,516 | Kept as-is. Clean, universally present. |
| D | contracts == size_usd / entry_price | 0/187 (T4), 0/0 (T1) | T1: field absent on all 499; T4M-PROJ: 627 applicable, 0 violations | **Corrected with a presence guard**, same reasoning as C — `contracts` (float) is ADR-0050/epoch≥12/T4M-PROJ-only. |
| E | pnl sign matches outcome | 0/2,193 (T4), 0/468 (T1) | T1: 0/466 resolved; T4M-PROJ: 0/2,316 resolved | Kept as-is. Clean. |
| F | resolved_at > entered_at | 0/0 both | T1: 0/466; T4M-PROJ: 0/2,316 | Kept as-is. Clean. |
| G | gross_edge == (model_p − mid) − vig | T4: 0/0; T1: 483/485 (99.6%) viol | T1 half-vig formula (`model_p − mid − vig/2`): 0/499; T4M-PROJ full-vig formula (`model_p − mid − vig`): 0/2,516 | **Corrected: band-scoped**, per brief. The operator's original single global formula was flagged as a spec error — ADR-0045/GG-119 established that T1 bakes **half**-vig into its stored `gross_edge` (`kalshi_client.py`'s `half_spread = vig/2`, consumed at `run_mlb_paper_trade.py`'s write path) while T4M-PROJ bakes **full** vig, always YES-frame (`run_t4_mlb_live.py:1148`). Evaluating T1 against the full-vig formula is exactly what produced the operator's 99.6% false-positive rate. Both bands are 100% clean once scoped to their own verified formula. Bands with no verified formula (T2, UNTAGGED) report `NO_FORMULA`, never a guessed violation. |
| H | no both-direction OPEN on same ticker | 17/151 (T4), 0/17 (T1) | T1: 0/17 open tickers; T4M-PROJ: 0/110 open tickers (of 172 open positions) | Kept as-is. Now fully clean — the operator's legacy baseline (17 conflicts) has since resolved; those positions are no longer OPEN. |

**Extend assertions** (I–N, no operator baseline — measured fresh):

| # | Assertion | Scope | Result |
|---|---|---|---|
| I | `size_usd == round(min(1.00, 10*entry_price_paid), 4)` | T4M-PROJ, logic_epoch≥12 (ADR-0050) | n=627, 0 violations. Exceeds the operator's cited n=141 VC6 baseline. |
| J | `contracts <= 10.0` | T4M-PROJ, logic_epoch≥12 | n=627, 0 violations. |
| K | `fee_net_edge` vig cascade (`paper_trader.py:460-466`, direction-conditional) | T1 + T4M-PROJ, logic_epoch≥6 (GG-113 clean floor) | T1: n=218, 0 violations; T4M-PROJ: n=1,932, 0 violations. Exceeds the operator's cited n=799 VC6 baseline. |
| L | `actual_hits` non-negative integer; `outcome` ∈ {WIN, LOSS}; `status` ∈ {OPEN, CLOSED, REJECTED} | All bands | 0 violations across both books. Confirms the exact enum sets in live use. |
| M | `logic_epoch` never null | All bands | 0/499 (T1), 0/2,516 (T4M-PROJ) null. |
| N | ticker-derived player token consistent with `player_name` (OR heuristic: last-word or full-concat convention) | All bands, presence-guarded | T1: 0/499 violations. T4M-PROJ: **1/2,516** — `KXMLBHIT-26AUG081915BALTEX-TEXNLOPE33-1` vs. "Nicky Lopez" (`TEXNLOPE` doesn't end with `NLOPE` or `NLOPEZ` — ticker is missing the trailing "Z"). Single genuine anomaly, stable/reproduced across two verification passes. Not auto-corrected (read-only scope) — flagged here for whoever picks up ticker-generation hygiene. |

---

## Task 2 — cross-path agreement (standing check, not an addendum)

Generalized from `run_t426_shadow_power_calc.py::task1_agreement_check()` into a per-band, per-epoch standing comparison of ledger `actual_hits`/`outcome` against T-421's decoupled outcome store's ticker-derived resolution (`cross_path_agreement()` in the deliverable script). Reports what is measured — disagreement is **not** assumed to be a bug; GG-170 (OPEN) already establishes it's expected until T-437 lands.

Measured 2026-08-11:

| Band | Epoch | Matched / Resolved | Hits agree | Outcome agree |
|---|---|---|---|---|
| T1 | 1 | 44/99 | 100.0% | 100.0% |
| T1 | 2 | 50/50 | 100.0% | 100.0% |
| T1 | 3 | 99/110 | 100.0% | 100.0% |
| T1 | 6 | 4/12 | 100.0% | 100.0% |
| T1 | 7 | 30/36 | 100.0% | 100.0% |
| T1 | 8 | 89/159 | 98.9% | 100.0% |
| T4M-PROJ | 3 | 565/580 | 85.3% | 91.9% |
| T4M-PROJ | 6 | 158/158 | 79.1% | 87.3% |
| T4M-PROJ | 7 | 162/184 | 90.1% | 94.4% |
| T4M-PROJ | 8 | 886/942 | 53.0% | 70.2% |
| T4M-PROJ | 12 | 187/452 | 63.1% | 74.9% |

**Reading this:** T1 is effectively fully corroborated by the decoupled store across every epoch present. T4M-PROJ shows real, persistent disagreement in every epoch, worst in epoch 8 and only partially recovered in epoch 12 — this is the live signature of GG-170 (MLB Stats API gameLog date-label instability), not a new finding. This table supersedes the pre-fix 69/156 (44.2%) hits / 47/156 (30.1%) outcome baseline cited in the original task brief with a fuller, per-epoch picture; the ~63-75% epoch-12 range is broadly consistent with the "~36.9%/25.1% disagreement, expected until T-437" figure previously root-caused as GG-170.

---

## `--strict` promotion criterion (Task 4)

`--strict` is not currently called anywhere — no cron, no hook, no CI. This is a **proposal**, not an operator-ratified decision; the numbers below are reasonable defaults, not settled policy.

Promote (start invoking `--strict` somewhere with real consequences, e.g. failing a CI check or blocking a specific merge path) only when **all** of the following hold:

1. **Consecutive clean runs:** 14 consecutive daily runs (governance_scan.sh's existing cadence) with **zero** violations across every currently-clean assertion (B, C2, D, E, F, G, H, I, J, K, L, M) — i.e., no regression on anything that is clean today. This does **not** require A or N to be clean, since both have a live, tracked root cause (GG-170, and N's single ticker-generation anomaly) that is out of this suite's scope to fix.
2. **False-positive rate:** zero false positives across those 14 runs, defined as: no violation traced (via `first_seen_epoch`/`entered_at` provenance) to a record this suite's own logic misjudged rather than a genuine data defect. Any false positive found during the trial window resets the 14-day clock after the fix ships.
3. **Cadence:** the trial must run on the suite's real cadence (once per `governance_scan.sh` invocation, i.e. at least once per session-start) — not a burst of manual re-runs compressed into a single day.
4. **Scope of promotion is per-assertion, not all-or-nothing:** an assertion with a known, tracked, OPEN root cause (A→GG-170, N→ticker-generation hygiene) should **not** block promoting `--strict` gating for the other, already-clean assertions. When (2)-(4) are ready to propose formally, the mechanism is a new CLI flag or config listing which assertion IDs `--strict` should treat as gating vs. informational-only (report-but-don't-fail) — not implemented in this delivery, since the operator has not asked for gating behavior at all yet; this section documents the criterion, not the mechanism.

Until an operator explicitly authorizes point 4's mechanism and signs off on criteria 1-3 having been met, `--strict` remains parsed-but-inert exactly as built.
