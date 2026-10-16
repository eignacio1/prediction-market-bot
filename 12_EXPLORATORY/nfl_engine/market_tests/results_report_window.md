# W77.2b — the Friday-report window (addendum to results.md)

DEPTH D5(b). Exploratory; comparison only, closing/market prices never a model input.
Finding that removed the planned fetch: the archive's 60-minute KXNFLGAME candles already run from market open (~2 weeks
pre-game) to close; only the 1-minute set is limited to 48h before settlement. So the REPORT window needed no new fetch.
`timing_report.py` -> `timing_report.json`. 413 hourly sets, 186 linked home-side games, 148 Sunday F8 games, n=145 per window.

| Window (ET) | slope, dMid per F8 margin pt | 95% game-bootstrap CI |
|---|---|---|
| PRE placebo Thu 12:00 -> Fri 12:00 | -0.0001 | [-0.0013, +0.0010] |
| **REPORT Fri 12:00 -> Sat 12:00** | **-0.0008** | **[-0.0034, +0.0014]** |
| POST placebo Sat 12:00 -> Sun 09:00 | +0.0002 | [-0.0032, +0.0029] |

F8 margin SD is 1.12 pts, so a 1-SD F8 gap moves the home mid by under 0.1 pt in the report window, with the CI
spanning zero and the placebos. **No measurable post-report drift**, consistent with the INACTIVES null in results.md.
Reading, with W77.2's power caveat applied: this is a hourly-resolution null with CI half-width ~0.0024/pt; a drift as
large as the closing-line pass-through (spread 0.67 pt per F8 pt ~ 0.02 prob/pt) is excluded. The market has priced F8
by the time the report window opens or moves on information the hourly mid cannot separate. It does not show the
unpriced remainder is zero. Verdict on F8 unchanged: REAL-AND-PRICED (partly); no timing edge found. Also open: other
Kalshi series (spread/total/team total) and 2026 candles remain unfetched.
