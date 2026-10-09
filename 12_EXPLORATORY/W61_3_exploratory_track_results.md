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
