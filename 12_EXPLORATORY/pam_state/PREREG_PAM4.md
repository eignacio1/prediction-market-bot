# H-DEPTH-PAM-4 — role security: minutes a displaced teammate loses when the displacer returns (PRE-REGISTRATION)

**Written:** 2026-11-25 (W129.4), committed before any data for this test is read. **Status:** PRE-REGISTERED. **NOT RUN.**
**Design note:** `02_ARCHITECTURE_DESIGN/PAM_ATTRIBUTE_CLASSES.md` class 4. **Doctrine:** HYPOTHESIS_DOCTRINE.md Part I binds.
**Purpose (Hard Rule 12):** DEPTH D5(b) NBA PAM class 4 (absent → interpreted if supported) and D3 (+1 pre-registered test).

## 1. Claim
When a teammate R returns after an absence, a player D who absorbed R's minutes loses part of that bump. The fraction of the bump D **keeps**
is his *role security* γ (class 4). A minutes forecast for D that sets γ from training seasons, by absence length, beats the control that
carries the whole bump (the arm's own recent-minutes input). ADR-0077: this scores an input against outcomes. A pass licenses a challenger;
the factor is *applied* only when the router scores it as a per-leaf split on net after costs per arm. Never a cell verdict.

## 2. Data and seasons
- NBA event store box scores (player minutes, team, game id, date). Pre-tip report status from the cached injury reports (2022-23 on) and the
  live collector for 2026-27. Regular season only. Decision time = tip − 4h (same rule as `pam/state.py` rows).
- **Fit (everything estimated here): seasons 2016–2022**, box scores only (reports do not exist before 2022-23).
- **Judged: 2026-27 regular-season games with tip after this file's commit time.** No earlier test judged 2026-27: PAM-3 judged 2023–2025
  and excluded 2026 and 2027; W69.3 and W93.1 read 2025 and 2026 for points/minutes and availability; EXP-047-C1/C2 read 2023-24.
  **Seasons 2023–2026 are not read by this test at all** (no tuning seasons; there are no tuned parameters beyond γ).

## 3. Units
- **Absence:** R plays, then has ≥5 consecutive team games with 0 minutes (DNP or inactive), on one team in one season.
- **Displaced player D:** teammate who played in ≥4 of R's absence games, with baseline_D = mean minutes over the 10 games before the
  absence began (≥4 played), and bump_D = mean minutes in the absence games − baseline_D ≥ +3.0 minutes.
- **Return event (E):** the first team game after the absence in which R is *cleared pre-tip*: R is not listed Out/Doubtful in the latest
  report slot ≤ tip − 4h, a report exists for that date, and R was listed Out in the last report before. Unit = (D, return game).
  Events without a usable report are excluded and counted. Training (no reports) uses the realized return (R plays ≥12 minutes) and says so.

## 4. Forecasts (all pre-tip inputs)
- **Control (γ=1):** m̂ = mean minutes over D's last 10 team games (includes the bump).
- **Rule:** m̂ = baseline_D + γ_b · bump_D, γ_b ∈ [0,1] by absence-length bucket b ∈ {5–9, 10–24, 25+ games}, fitted by least squares on
  training events (minutes realized in the return game), clipped to [0,1]. One γ per bucket; nothing else is fitted. Frozen into `FIT_PAM4.json`
  at the commit before the first judged read.
- Class 4 field mapping (later block, not built here): `role_security` = γ_b of the bucket; `return_window` = the absence-length bucket.

## 5. Outcome, metric, rule
- **Outcome:** D's minutes in the return game (0 if DNP).
- **Metric:** Δ = mean over events of [(m̂_control − y)² − (m̂_rule − y)²]; positive favors the rule. Interval: 90%, game-clustered bootstrap, 2,000
  resamples, seed 20261125 (doctrine I.6). Secondary (descriptive, BH q 0.10 across the three buckets): same Δ per bucket.
- **Minimum useful effect δ = 1.0 min².** **n\*** = ((1.645 + 0.842) · σ_Δ / δ)², with σ_Δ the SD of per-event paired loss differences from
  leave-one-season-out fits on 2016–2022; computed and frozen in `FIT_PAM4.json` before any judged read. No read below n\* events.
- **Answers:** SUPPORTED if n ≥ n\* and the 90% interval excludes 0 favorably. NOT SUPPORTED if n ≥ n\* and the interval is entirely ≤ 0 or its
  upper end is below δ (hypothesis closed, EXP-id assigned at run, parked for R&D; this closes only this test). UNDERPOWERED if n < n\*.

## 6. Pre-stated modal outcome (P3)
First read at n\* (the 2026-27 sample accrues through the season): **SUPPORTED, small**, γ̂ ≈ 0.4–0.7, Δ ≈ +1 to +3 min² (a returning starter
mechanically takes minutes back; the control ignores that). Any read before n\* is **UNDERPOWERED**. A result outside this range is reported as such.

## 7. Leakage rules
Only games on strictly earlier ET days; the report slot is the latest ≤ tip − 4h; γ_b is frozen before any 2026-27 outcome is read; R's
realized minutes in the return game are never an input; events with R listed Out/Doubtful are excluded, not scored.

## 8. Consequence and run
SUPPORTED → class 4 becomes *interpreted*; next, a pre-registered router challenger (minutes_expected with γ_b) scored per leaf on net after
costs. Not SUPPORTED → hypothesis closed (EXP-id, parked for R&D). Run: `12_EXPLORATORY/pam_state/run_pam4.py` is **not written yet** and must not be
run before `FIT_PAM4.json` is committed and n ≥ n\*. Open limits: report names are partial (about 71% of Out names match a box-score
player), so cleared-R events are a subset; one season of judged data.
