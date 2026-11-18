# W118.3 Part B: NHL starting-goalie confirmation as a split, and the price-timing study (IT-12). Last reviewed: 2026-11-18
Frozen before any outcome statistic. Only structure counts were read: 71 games, 341 snapshot rows, 58 side-confirmations with a
`confirmed_at_utc`, 19 sides whose listed goalie name changes across snapshots (Muse archive f969ad1, L3-snapshots/nhl/goalies-2026-11-10..17,
copied into data/). Prices: exp_output/PRICE_ARCHIVE/prices_<date>.jsonl, series KXNHLGAME (~20-min snapshots, yes_bid / yes_ask).

## Hypothesis (EXP-W118.3-GOALIE)
H1: the Kalshi NHL moneyline moves in response to a goalie confirmation, and keeps moving after the first 20 minutes (a lag the archive can see).
Closing this test closes only this hypothesis (parked for R&D); a null routes the split to RIDE / NO BET, never closes a cell.

## Unit, events, windows
- Game: a snapshot game_id `AWAY-HOME-date` matched to a KXNHLGAME event by unordered team pair and date (Kalshi two-letter aliases LA/NJ/TB/SJ).
- Event: one side's FIRST non-null `*_confirmed_at_utc` c in the game. Price p = home-team yes_mid from the archive.
- Eligible: a snapshot of p at or before c within 25 min (pre), and later snapshots at c+20 / +40 / +60 / +120 min (nearest archive run within
  +-10 min). Every window must end before 22:00Z on the game date (a proxy for puck drop; the NHL start time is not in the snapshots).
- Split: INFORMATIVE = the side's listed goalie name differs from the name in the previous snapshot of that game (or the side was Likely /
  Unconfirmed with a different name earlier); ROUTINE = same name. Reported separately; the primary test pools both.

## Statistics (game-clustered 2,000-draw bootstrap, 90% interval)
- Move m(c,L) = |p(c+L) - p(pre)|. Placebo: windows of the same length L in the same game, pre-puck-drop, with no confirmation or status change
  for either side within +-2 h of the window; their median is subtracted. D(L) = mean over events of [m - placebo median].
- Primary: D(60). Lag test: D_lag = mean of |p(c+120) - p(c+40)| minus its placebo (movement AFTER the first 40 minutes).
- Direction is not tested: the goalie's quality (which sign a backup carries) is not in any free store at this n. So the arm, if any, is not a
  directional bet yet; a move that is visible but unsigned routes to NO BET here and to the signed study when a goalie-quality column exists.
- Candidate arm (RIDE-the-move / MOMENTUM after confirmation) only if D_lag's interval excludes 0 AND its point estimate exceeds one taker round
  cost at the observed half-spread. Otherwise: no lag visible = a routing result (NO BET / RIDE on this split).
- n is small by construction (about 58 events); the interval is the verdict, and it is reported with n and the number of eligible events.
