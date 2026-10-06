# W56.2 — Live Terminal results (2026-10-06)

Read-only change. No order, position, fill, stake or kelly_fraction touched. PRs #167 (ba2fe33) and #169 (1f15ebf) merged, CI green; Deploy restarted `pmbot-web-dashboard` only (`t4-mlb restart decision: not_needed -- no file imported by t4-mlb changed in this push`).

## Before (D1) — `img/W56_2_before_desktop.png`
No unified decision stream (Live Tape showed audit events); shadow tape had no WOULD-FIRE/stake and excluded T4 cycle-log evaluations; OVERVIEW showed T1 drawdown only (no T4M-PROJ, no 20% reference) with red at >10% (implied a breach); no per-arm last-row age.

## After (D5) — `img/W56_2_after_desktop.png`, `img/W56_2_after_phone.png`
Default **NOW** tab on the running terminal: mode SHADOW, real capital $0, realized drawdown T1 12.44% (-$124.44) and T4M-PROJ 13.45% (-$134.47) vs the 20% kill switch with bars and book-write age, evaluations today (249), per-arm last-row chips (stale amber), and a 150-row newest-first tape (time, sport, market, band, model p, price, net edge, WOULD-FIRE, "$0 SHADOW"). Verified real recent rows (T4M-PROJ rows seconds old).

## Definitions chosen (no repo fire rule exists)
WOULD-FIRE = fee-adjusted net edge > 0 (best of `e_net_yes_k007`/`e_net_no_k007` for shadow rows; `net_edge` for T4 cycle rows). Shadow computation only. Operator may redefine.

## Found live, fixed in #169
`risk.py` import fails in the VPS dashboard python (no `jsonlines`) -> kill-switch limit was None; now read from source. Arm with no sport/band shown as "unlabelled".

## Not fixed (out of scope, for operator)
- Premise to check: 842+ open paper positions with $0.55–$1.00 sizes and T4 positions opened today despite all kelly_fraction = 0.
- C4 tile "not instrumented" for the same `jsonlines` import failure (pre-existing).
- Cycle-log rows with empty ticker render as a blank "—" row (edge 0.0000).
- Phone: top status bar wraps/overflows (pre-existing); decision table scrolls horizontally.
- NOW rail partly duplicates the strip.
