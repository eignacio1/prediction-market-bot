# W106.3 Part A — prop inventory and liquidity tiers (EXPLORATORY)

Live API (public GET, 4,167 sports series, 2026-11-10): per-game prop series today — MLB: HIT, HR, HRR, KS, RBI, TB. NBA: 3PT, AST, BLK, PTS, REB, STL (+PROT variants, PTSPRECISE, FIRSTBASKET, PTSLEADER). NFL: PASSYDS (+H2H/PRECISE/PROT), PASSATT, PASSCOMP, PASSINT, PASSTDS, REC, RECYDS, ANYTD, FIRSTTD, TD, INT, SACK, FG. NHL: AST, GOAL, PTS, SAVE(S), FIRSTGOAL.

**Archived prop families: 1 of ~40 listed (KXMLBHIT: 532,614 snapshots, 38,546 tickers, 90 days).** All other props: not archived (GAP).

Liquidity tier by archived-depth median, `$within 5c of mid, min side` (thin <100, mid 100–1000, deep >1000), medians over usable depth samples:

| Family | n samples | median $ | half-spread | tier |
|---|---|---|---|---|
| KXMLBHIT (prop) | 2,780 | 72 | 1.5c | thin |
| KXMLBF5SPREAD | 1,952 | 48 | 2.0c | thin |
| KXMLBF3 | 1,872 | 93 | 2.0c | thin |
| KXMLBTEAMTOTAL | 3,638 | 96 | 2.0c | thin |
| KXMLBF5TOTAL | 1,789 | 107 | 1.5c | mid |
| KXMLBF5 | 1,914 | 243 | 1.5c | mid |
| KXMLBGAME | 4,110 | 302 | 2.0c | mid |
| KXMLBSPREAD | 1,960 | 1,067 | 1.0c | deep |
| KXMLBTOTAL | 2,023 | 5,339 | 1.0c | deep |
| KXNBAGAME / TEAMTOTAL / TOTAL / SPREAD | 561/537/545/555 | 0 / 3 / 228 / 844 | 9.0 / 4.5 / 2.0 / 1.5c | thin / thin / mid / mid |
| KXNFLGAME / SPREAD / TEAMTOTAL / TOTAL | 969/916/922/930 | 2,105 / 684 / 123 / 146 | 1.0 / 1.0 / 1.5 / 1.5c | deep / mid / mid / mid |
| KXNHLGAME / SPREAD / TEAMTOTAL / TOTAL | 561/548/220/530 | 18 / 229 / 0 / 0 | 4.0 / 3.0 / 7.0 / 36.2c | thin / mid / thin / thin |

Settlements: 251,528 settled tickers fetched for KXMLBHIT/TOTAL/SPREAD/GAME/TEAMTOTAL/F5TOTAL (live `/markets` + `/historical/markets`, cutoff 2026-09-10).
