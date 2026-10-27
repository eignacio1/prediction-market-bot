# W89.5 — NBA PAM roles against the KXNBAPTS points-prop price (EXPLORATORY)

**EXPLORATORY** (CHARTER rule 6). No order, row, registry cell, pre-registration, model or stake touched. Pillar: DEPTH. Data window: 2026-10-20 to 2026-10-26 (7 game dates).

> Operator, W16: "beating buddy off his phone placing parlays, that's the first step"

## Verdict

**NULL at current n.** No PAM role explains where the KXNBAPTS price is wrong. Neither PRF-1 nor PRF-4 shows a price gap or an out-of-sample Brier gain. None of the 22 roles tested survives BH at q=0.10, under either anchor. The tested path "PAM fact → adjusted price → compared with the market" now exists and ran. It returned a null, and the null is small-n, not a proven absence.

## Part A — the join

Source: public unauthenticated Kalshi market data (strike, result, 1-minute quotes) joined to ESPN final box scores. No shadow ledger or sealed file was read, which avoids the charter-rule-2 conflict recorded in GG-1064.

| Item | Value |
|---|---|
| Settled binary KXNBAPTS markets | 2,421 |
| Events / matched to ESPN | 54 / 52 |
| Markets joined to a stat line | **2,409** |
| Unmatched players | **0** |
| Kalshi result vs box-score disagreements | 0 |
| Rows without candles / candle errors | 0 / 0 |
| DNP rows | 0 (caveat below) |

**Unmatched events (all listed):** `KXNBAPTS-26OCT08PHIBKN` and `KXNBAPTS-26OCT05NYKPHI`. Both are preseason-dated, before the 2026-10-20 regular-season window, and were not looked up. GS@DEN (`26OCT26GSWDEN`) was unmatched in the first pull only because the game was not final yet. It matched on the rerun.

**Caveats**
- `dnp_rows = 0` is surprising. Kalshi may list only players who played, but this was not verified, so it is registered as a data check.
- Premise correction (measured): these markets mostly open **before** tip, not in-game. 2,156 of the 2,369 rows in the first pull (before GS@DEN was added) opened pre-tip; the median open was about 19h before tip. The first usable quote can be days early, so a second anchor was added.
- Usable quote = two-sided with spread ≤ 0.10.
- **Anchor=first:** the first usable quote. 1,820 strikes usable and 589 dropped (no usable quote), across 52 games.
- **Anchor=last_pretip:** the last usable quote at or before tip, as a sensitivity check. 1,640 usable and 769 dropped.
- **Players with no 2025-26 PAM record (roles unassigned):** Aday Mara, Caleb Wilson, Cameron Boozer, Damian Lillard, Darius Acuff Jr., Darryn Peterson, Fred VanVleet, Keaton Wagler, Kingston Flemings, Kyrie Irving, Mikel Brown Jr., Morez Johnson Jr. (first anchor only), Tyrese Haliburton, Yaxel Lendeborg. This is rookies, injured or returning players, and new signings. 93.2% of usable strikes have a PAM record.
- All numbers below are from the final run (2,409 joined, 52 games), after GS@DEN finished and was added.

## Part B — does role explain the price error?

Method: the unit is a settled strike. y = 1[points > strike]; p = the market mid at the anchor.
1. **Price gap.** Mean(y − p) for players with the role (role flag = MET or MET_PARTIAL, 2025-26 season-end taxonomy v4, unedited), with a game-clustered bootstrap interval and a centered game-resample two-sided p.
2. **Out of sample by date.** Expanding-window ridge logistic, anchor-only vs anchor + role flag. Brier difference (anchor-only minus adjusted; positive = role helps) with a game-clustered interval and MDE.
3. **BH at q=0.10** across all roles.

Roles tested: PRF-1 and PRF-4 (fixed in advance), plus every other role with at least 8 players and at least 60 strikes (a counts-only floor, no outcome-chosen threshold). That gives 22 roles.

### Primary roles

| Anchor | Role | Strikes | Players | Games | Mean(y−p) [95% CI] | p | OOS n | OOS Brier diff [95% CI] | MDE |
|---|---|---|---|---|---|---|---|---|---|
| first | PRF-1 | 223 | 21 | 41 | −0.009 [−0.092, +0.070] | 0.843 | 1,355 | −0.00010 [−0.00063, +0.00041] | 0.00042 |
| first | PRF-4 | 597 | 67 | 52 | +0.001 [−0.049, +0.052] | 0.974 | 1,355 | −0.00005 [−0.00033, +0.00022] | 0.00026 |
| last_pretip | PRF-1 | 191 | 21 | 40 | −0.026 [−0.106, +0.052] | 0.538 | 1,226 | −0.00017 [−0.00079, +0.00044] | 0.00061 |
| last_pretip | PRF-4 | 537 | 67 | 52 | −0.003 [−0.052, +0.048] | 0.917 | 1,226 | −0.00007 [−0.00049, +0.00030] | 0.00036 |

Overall (first anchor), mean_p = 0.337 and mean_y = 0.347.

### All 22 roles

Full per-role results for both anchors are in `results/w89/cross_first.json` and `cross_last_pretip.json`. The smallest raw p across the 22 roles is 0.146 (first) and 0.157 (last_pretip). Nothing survives BH at q=0.10 in either case.

### Power: when does the season reach a detectable n?

Assumptions: the current rate of about 32 PRF-1 role-strikes per game day and about 85 PRF-4 role-strikes per game day continues, and the CI half-width scales as 1/√n.
- **PRF-1:** half-width ≈ 0.08 at n=223. About 1,500 role-strikes are needed to detect a 0.03 price gap, which is about 48 more days, **around mid-December 2026**.
- **PRF-4:** half-width ≈ 0.05 at n=597. About 1,625 are needed, about 12 more days at 85/day, **around mid-November 2026**.
- These are rough, and strikes within a game are clustered, so the real requirement is higher.

## Techniques: when each applies and when it doesn't

- **Mean(y−p) with game-clustered bootstrap:** applies to a market-anchored calibration gap across strikes in the same game. It does not apply to model quality, because it says nothing about whether role predicts points.
- **Expanding-window ridge logistic Brier difference:** applies to small n with few columns, split by date. It does not apply with fewer than 100 training rows, which are skipped.
- **BH across roles:** applies to many correlated tests, and q=0.10 is conservative. It does not apply if the role list is chosen from outcomes. Here it is fixed by a counts-only floor.
- Known-answer tests are in `tests/test_w89_nba_pam_price.py` (96 passed with the isolation scan).

## Granularity index — stage per factor

| Factor | Split | Rank vs history | Matchup cross | Market map | Application | Stage |
|---|---|---|---|---|---|---|
| PRF-1 | role flag | not built | not built | KXNBAPTS strike price | tested, null | aggregated + interpreted; **applied path tested, null** |
| PRF-4 | role flag | not built | not built | KXNBAPTS strike price | tested, null | aggregated + interpreted; **applied path tested, null** |
| Other 20 roles | role flag | not built | not built | KXNBAPTS strike price | tested, null | same |

An applied factor here means "a tested path from the fact to a price, against the market". It does not mean "found edge".

## Proposed seat rows (results only; not written to `SEATS/nba.toml`, which is block 89.3's)

- **NBA points-prop seat:** the PAM role, read at the strike, against the KXNBAPTS mid. Status: tested, null at n≈1.8k strikes over 52 games. Revisit when PRF-4 reaches about 1,600 role-strikes (about mid-November 2026) and PRF-1 reaches about 1,500 (about mid-December 2026).
- **Data gap:** rookies and new signings have no 2025-26 role. This needs a PAM refresh with 2026-27 season-to-date roles (a registered gap, not a paid-data gap).

## Operator decisions

None required. The null is small-n, so no pre-registration change is proposed.
