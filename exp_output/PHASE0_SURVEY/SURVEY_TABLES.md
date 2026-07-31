# Phase 0 — Kalshi Market Universe Survey (generated)

Series enumerated: **12355**  |  markets sampled: **5900**
Depth gate: family must clear **$10.00** (= 10 x $1.00 intended stake, spec section 2.7)

**Scope note (added by hand, 2026-07-31):** the 5,900 sampled markets come from
Phase 0-A's `markets_sample.json`, captured over a 220-series "MLB-looking"
search space, not a strict MLB-only filter (per the port-over's known
false-positive concern). 5,283/5,900 markets (89.5%) are on literally
`*MLB*`-ticker series; the remaining 617 are almost entirely adjacent baseball
leagues (KXNPB/Nippon, KXKBO/Korean, KXLMBGAME/Mexican — legitimately
baseball, just not MLB) or MLB-adjacent (`KXTEAMSINWS`, World Series). Only 45
markets (0.8% of the 5,900) are genuine off-topic false positives
(`KXCITYCHAMPS`, `KXCITYNBAEXPAND`). Table 3's per-family depth figures are
therefore a family-level, not strictly MLB-only, measurement — the
contamination is real but small and does not change any PASS/FAIL verdict at
this magnitude.

## Table 1 — Series by sport and family

| Sport | Family | Series count | Example tickers |
|---|---|---:|---|
| MLB | GAME_TOTAL | 6 | KXLEADERMLBRUNS, KXMLBF5TOTAL, KXMLBSERIESGAMETOTAL |
| MLB | GAME_WINNER | 8 | KXLMBGAME, KXMLBASGAME, KXMLBDIVWINNER |
| MLB | PARTIAL_GAME_WINNER | 3 | KXMLBF3, KXMLBF5, KXMLBF7 |
| MLB | PLAYER_PROP | 31 | KXLEADERMLBHITS, KXLEADERMLBHR, KXLEADERMLBKS |
| MLB | RUN_LINE | 4 | KXMLBF5SPREAD, KXMLBSPREAD, KXNCAABBSPREAD |
| MLB | SEASON_WIN_TOTAL | 32 | KXLEADERMLBWINS, KXMLBWINS-ATH, KXMLBWINS-ATL |
| MLB | TEAM_TOTAL | 1 | KXMLBTEAMTOTAL |
| MLB | UNCLASSIFIED | 98 | KXATTENDMLB, KXCITYMLBEXPAND, KXCOACHOUTMLB |
| NBA | GAME_TOTAL | 22 | KXCBATOTAL, KXEUROCUPTOTAL, KXNBA1HTOTAL |
| NBA | GAME_WINNER | 57 | KXACBGAME, KXBALGAME, KXBBLGAME |
| NBA | PLAYER_PROP | 18 | KXLEADERNBAPTS, KXLEADERWNBAPTS, KXNBAH2HBENCHPTS |
| NBA | RUN_LINE | 25 | KXCBASPREAD, KXEUROCUPSPREAD, KXNBA1HSPREAD |
| NBA | SEASON_WIN_TOTAL | 7 | KXNBAMOSTWINS, KXNBAPLAYOFFWINS, KXNBASERIESROADWINS |
| NBA | TEAM_TOTAL | 1 | KXNBATEAMTOTAL |
| NBA | UNCLASSIFIED | 314 | CBVOLUME, KXABNBA, KXACQUIRECOINBASE |
| NFL | GAME_TOTAL | 8 | KXNCAAFTOTAL, KXNFL1HTOTAL, KXNFL1QTOTAL |
| NFL | GAME_WINNER | 25 | KXMVENFLMULTIGAME, KXMVENFLMULTIGAMEEXTENDED, KXMVENFLSINGLEGAME |
| NFL | PLAYER_PROP | 7 | KXLEADERNFLRUSHYDS, KXNFLPASSYDS, KXNFLSEASONPASSYDS |
| NFL | RUN_LINE | 9 | KXNCAAFSPREAD, KXNFL1HSPREAD, KXNFL1QSPREAD |
| NFL | SEASON_WIN_TOTAL | 76 | KXNCAAFACCWINS, KXNCAAFBIG12WINS, KXNCAAFBIGTENWINS |
| NFL | TEAM_TOTAL | 2 | KXNCAAFTEAMTOTAL, KXNFLTEAMTOTAL |
| NFL | UNCLASSIFIED | 289 | ACPI, ACPICORE, ACPICORE- |
| NHL | GAME_TOTAL | 4 | KXNHLSERIESTOTALGOAL, KXNHLSERIESTOTALGOALS, KXNHLTOTAL |
| NHL | GAME_WINNER | 3 | KXNCAAHOCKEYGAME, KXNHLGAME, KXNHLSERIESGAMES |
| NHL | PLAYER_PROP | 1 | KXNHLPTS |
| NHL | RUN_LINE | 3 | KXNHLSERIESSPREAD, KXNHLSPREAD, KXWOMHOCKEYSPREAD |
| NHL | SEASON_WIN_TOTAL | 1 | KXNHLWINS |
| NHL | UNCLASSIFIED | 51 | KXEARNINGSMENTIONHLT, KXESPYNHL, KXNCAAHOCKEY |
| OTHER | GAME_TOTAL | 172 | KXAFCAC1HTOTAL, KXAFCACTOTAL, KXAFCCL1HTOTAL |
| OTHER | GAME_WINNER | 331 | GAMEAWARDS, GAMERANK, KX1HOMEGAME |
| OTHER | PLAYER_PROP | 83 | BANKRUPTS, BANKRUPTSY, BTCETHRETURN |
| OTHER | RUN_LINE | 167 | KXAFCAC1HSPREAD, KXAFCACSPREAD, KXAFCCL1HSPREAD |
| OTHER | SEASON_WIN_TOTAL | 11 | KXCASEWINSHOHEI, KXDSAWINS, KXGOVWINS |
| OTHER | TEAM_TOTAL | 53 | KXAFCACTEAMTOTAL, KXAFCCLTEAMTOTAL, KXAFCONTEAMTOTAL |
| OTHER | UNCLASSIFIED | 10432 | 10Y2Y, 10Y3M, 1SONG-DRAKE |

## Table 2 — MLB series detail

| Series | Family | Title | Markets sampled |
|---|---|---|---:|
| `KXATTENDMLB` | UNCLASSIFIED | WHO WILL ATTEND THE BASEBALL GAME | 0 |
| `KXCITYMLBEXPAND` | UNCLASSIFIED | MLB expansion | 0 |
| `KXCOACHOUTMLB` | UNCLASSIFIED | Baseball Managers Out | 27 |
| `KXCOACHOUTMLBDATE` | UNCLASSIFIED | MLB Coach Out Date | 3 |
| `KXCONGRESSBASEBALL` | UNCLASSIFIED | Congressional Baseball Game | 0 |
| `KXESPYMLB` | UNCLASSIFIED | ‭BEST MLB PLAYER‬ | 0 |
| `KXEWCMLBB` | UNCLASSIFIED | Mobile Legends: Bang Bang Mid Season Cup at 2025 Esports World Cup | 0 |
| `KXLEADERMLBAVG` | UNCLASSIFIED | MLB Batting Average Leader | 57 |
| `KXLEADERMLBDOUBLES` | UNCLASSIFIED | MLB Doubles Leader | 71 |
| `KXLEADERMLBERA` | UNCLASSIFIED | MLB ERA Leader | 56 |
| `KXLEADERMLBHITS` | PLAYER_PROP | MLB Hits Leader | 72 |
| `KXLEADERMLBHR` | PLAYER_PROP | MLB Home Runs Leader | 31 |
| `KXLEADERMLBKS` | PLAYER_PROP | Pro Baseball Strikeouts Leader | 27 |
| `KXLEADERMLBOPS` | UNCLASSIFIED | MLB OPS Leader | 46 |
| `KXLEADERMLBRBI` | PLAYER_PROP | MLB RBIs Leader | 71 |
| `KXLEADERMLBRUNS` | GAME_TOTAL | MLB Runs Leader | 62 |
| `KXLEADERMLBSAVES` | UNCLASSIFIED | MLB Saves Leader | 0 |
| `KXLEADERMLBSTEALS` | UNCLASSIFIED | MLB Steals Leader | 50 |
| `KXLEADERMLBSTRIKEOUTS` | PLAYER_PROP | MLB Strikeouts Leader | 0 |
| `KXLEADERMLBTRIPLES` | UNCLASSIFIED | MLB Triples Leader | 40 |
| `KXLEADERMLBWAR` | UNCLASSIFIED | MLB WAR Leader | 57 |
| `KXLEADERMLBWINS` | SEASON_WIN_TOTAL | MLB Wins Leader | 57 |
| `KXLMBGAME` | GAME_WINNER | Mexican Baseball League | 60 |
| `KXMEDIACOVERMLBTHESHOW` | UNCLASSIFIED | WHO WILL BE ON THE COVER OF MLB THE SHOW | 0 |
| `KXMLB` | UNCLASSIFIED | World Series | 30 |
| `KXMLB500` | UNCLASSIFIED | MLB teams at .500 | 0 |
| `KXMLBAL` | UNCLASSIFIED | MLB American League Championship | 15 |
| `KXMLBALCENT` | UNCLASSIFIED | American League Central Winner | 5 |
| `KXMLBALCPOTY` | UNCLASSIFIED | Pro Baseball American League Comeback Player of the Year | 11 |
| `KXMLBALCY` | UNCLASSIFIED | Pro Baseball American League Cy Young | 42 |
| `KXMLBALEAST` | UNCLASSIFIED | American League East Winner | 5 |
| `KXMLBALHAARON` | UNCLASSIFIED | Pro Baseball American League Hank Aaron | 41 |
| `KXMLBALLSTAR` | UNCLASSIFIED | Pro Baseball All-Stars | 0 |
| `KXMLBALLSTARHR` | PLAYER_PROP | Pro Baseball All-Star Game Total Home Runs | 0 |
| `KXMLBALMOTY` | UNCLASSIFIED | Pro Baseball American League Manager of the Year | 17 |
| `KXMLBALMVP` | UNCLASSIFIED | Pro Baseball American League MVP | 47 |
| `KXMLBALRELOTY` | UNCLASSIFIED | Pro Baseball American League Reliever of the Year | 22 |
| `KXMLBALROTY` | UNCLASSIFIED | Pro Baseball American League Rookie of the Year | 30 |
| `KXMLBALWEST` | UNCLASSIFIED | American League West Winner | 5 |
| `KXMLBASGAME` | GAME_WINNER | Professional Baseball All-Star Game | 0 |
| `KXMLBASGHIT` | PLAYER_PROP | All Star Game Hits | 0 |
| `KXMLBASGHR` | PLAYER_PROP | All Star Game Home Runs | 0 |
| `KXMLBASGKS` | UNCLASSIFIED | All Star Game Strikesouts | 0 |
| `KXMLBASGMVP` | UNCLASSIFIED | Pro Baseball All-Star Game MVP | 0 |
| `KXMLBAWARDCOMBO` | UNCLASSIFIED | Pro Baseball Award Combo | 1 |
| `KXMLBBESTRECORD` | UNCLASSIFIED | Pro Baseball Best Record | 30 |
| `KXMLBCBA` | UNCLASSIFIED | MLB CBA | 1 |
| `KXMLBCOACH` | UNCLASSIFIED | Pro Baseball Next Manager | 0 |
| `KXMLBDEBUT` | UNCLASSIFIED | Pro Baseball Debut | 141 |
| `KXMLBDIVWINNER` | GAME_WINNER | MLB divisions | 0 |
| `KXMLBDRAFTPICK` | UNCLASSIFIED | Pro Baseball Draft Pick | 0 |
| `KXMLBDRAFTTOP` | UNCLASSIFIED | Pro Baseball Top Pick | 0 |
| `KXMLBEOTY` | UNCLASSIFIED | Pro Baseball Executive of the Year | 31 |
| `KXMLBEXTRAS` | UNCLASSIFIED | MLB Extra Innings | 45 |
| `KXMLBF3` | PARTIAL_GAME_WINNER | First 3 Innings Winner | 45 |
| `KXMLBF5` | PARTIAL_GAME_WINNER | First 5 Innings Winner | 45 |
| `KXMLBF5SPREAD` | RUN_LINE | First 5 Innings Spread | 60 |
| `KXMLBF5TOTAL` | GAME_TOTAL | First 5 Innings Total | 105 |
| `KXMLBF7` | PARTIAL_GAME_WINNER | First 7 Innings Winner | 45 |
| `KXMLBFASTPITCH` | UNCLASSIFIED | Fastest Pitch of season | 7 |
| `KXMLBFTGAME` | GAME_WINNER | Pro Baseball Futures Game | 0 |
| `KXMLBGAME` | GAME_WINNER | Professional Baseball Game | 90 |
| `KXMLBGG` | UNCLASSIFIED | Pro Baseball Gold Glove | 187 |
| `KXMLBHIT` | PLAYER_PROP | Pro Baseball Hits | 125 |
| `KXMLBHR` | PLAYER_PROP | Pro Baseball Home Runs | 72 |
| `KXMLBHRDERBY` | PLAYER_PROP | Pro Baseball Homerun Derby | 0 |
| `KXMLBHRDERBY500` | PLAYER_PROP | 500+ Foot HRs at the Home Run Derby | 0 |
| `KXMLBHRDERBYDISTANCE` | PLAYER_PROP | Pro Baseball Home Run Derby Longest Distance | 0 |
| `KXMLBHRDERBYFIN` | PLAYER_PROP | Pro Baseball Home Run Derby Finals Qualifiers | 0 |
| `KXMLBHRDERBYFORECAST` | PLAYER_PROP | Home Run Derby Finals Forecast | 0 |
| `KXMLBHRDERBYLONGEST` | PLAYER_PROP | Pro Baseball Home Run Derby Player to Hit Longest | 0 |
| `KXMLBHRDERBYMATCHUP` | PLAYER_PROP | Pro Baseball Home Run Derby Final Matchup | 0 |
| `KXMLBHRDERBYOU` | PLAYER_PROP | Pro Baseball Home Run Derby Over/Under Home Runs | 0 |
| `KXMLBHRDERBYQUAL` | PLAYER_PROP | Pro Baseball Home Run Derby Selections | 0 |
| `KXMLBHRDERBYR1LEAD` | PLAYER_PROP | Round 1 Leader | 0 |
| `KXMLBHRDERBYSEMI` | PLAYER_PROP | Pro Baseball Home Run Derby Semifinals Qualifiers | 0 |
| `KXMLBHRDERBYTOT` | PLAYER_PROP | Home Run Derby Total Home Runs | 0 |
| `KXMLBHRDERBYVELO` | PLAYER_PROP | Highest Exit Velocity Home run | 0 |
| `KXMLBHRR` | PLAYER_PROP | Pro Baseball Hits Runs RBIs | 175 |
| `KXMLBKS` | PLAYER_PROP | Pro Baseball Strikeouts | 198 |
| `KXMLBLSTREAK` | UNCLASSIFIED | Longest Losing Streak | 30 |
| `KXMLBMENTION` | UNCLASSIFIED | MLB Announcers | 95 |
| `KXMLBNEXTHR` | PLAYER_PROP | Pro Baseball Next Homerun | 0 |
| `KXMLBNEXTTEAM` | UNCLASSIFIED | Pro Baseball Next Team | 341 |
| `KXMLBNL` | UNCLASSIFIED | MLB National League Championship | 15 |
| `KXMLBNLCENT` | UNCLASSIFIED | National League Central Winner | 5 |
| `KXMLBNLCPOTY` | UNCLASSIFIED | National League Comeback Player of the Year | 11 |
| `KXMLBNLCY` | UNCLASSIFIED | Pro Baseball National League Cy Young | 46 |
| `KXMLBNLEAST` | UNCLASSIFIED | National League East Winner | 5 |
| `KXMLBNLHAARON` | UNCLASSIFIED | Pro Baseball American League Hank Aaron | 51 |
| `KXMLBNLMOTY` | UNCLASSIFIED | Pro Baseball National League Manager of the Year | 17 |
| `KXMLBNLMVP` | UNCLASSIFIED | Pro Baseball National League MVP | 53 |
| `KXMLBNLRELOTY` | UNCLASSIFIED | Pro Baseball National League Reliever of the Year | 21 |
| `KXMLBNLROTY` | UNCLASSIFIED | Pro Baseball National League Rookie of the Year | 30 |
| `KXMLBNLWEST` | UNCLASSIFIED | National League West Winner | 5 |
| `KXMLBOAK` | UNCLASSIFIED | Oakland Athletics relocate | 0 |
| `KXMLBOUTS` | UNCLASSIFIED | Pro Baseball Outs Recorded | 22 |
| `KXMLBPITCH` | UNCLASSIFIED | Pro Baseball Player to Pitch | 1 |
| `KXMLBPITCHEROTM` | UNCLASSIFIED | Pro Baseball Pitcher of the Month | 46 |
| `KXMLBPLAYEROTM` | UNCLASSIFIED | Pro Baseball Player of the Month | 53 |
| `KXMLBPLAYEROTW` | UNCLASSIFIED | Pro Baseball Player of the Week | 0 |
| `KXMLBPLAYOFFS` | UNCLASSIFIED | Pro Baseball Playoff Qualifiers | 30 |
| `KXMLBRBI` | PLAYER_PROP | Pro Baseball RBIs | 86 |
| `KXMLBRETURN` | UNCLASSIFIED | Pro Baseball Player Return | 0 |
| `KXMLBRFI` | UNCLASSIFIED | Pro Baseball Run in First Inning | 45 |
| `KXMLBSB` | UNCLASSIFIED | Pro Baseball Stolen Bases | 28 |
| `KXMLBSEASONHR` | PLAYER_PROP | Pro Baseball Season Home Runs | 179 |
| `KXMLBSERIES` | UNCLASSIFIED | Professional Baseball Series | 0 |
| `KXMLBSERIESEXACT` | UNCLASSIFIED | Professional Baseball Series Exact Result | 0 |
| `KXMLBSERIESGAMETOTAL` | GAME_TOTAL | Professional Baseball Series Total Games | 0 |
| `KXMLBSISTREAK` | UNCLASSIFIED | Pro Baseball Scoreless Innings Streak | 0 |
| `KXMLBSPREAD` | RUN_LINE | Pro Baseball Spread | 90 |
| `KXMLBSS` | UNCLASSIFIED | Pro Baseball Silver Slugger | 160 |
| `KXMLBSTAT` | UNCLASSIFIED | Pro Baseball Season Stat | 10 |
| `KXMLBSTATCOUNT` | UNCLASSIFIED | Pro Baseball Season Stat | 36 |
| `KXMLBSTGAME` | GAME_WINNER | Pro Baseball Spring Training game | 0 |
| `KXMLBSTRIKE` | UNCLASSIFIED | MLB STRIKE | 0 |
| `KXMLBTB` | UNCLASSIFIED | Pro Baseball Total Bases | 165 |
| `KXMLBTEAMSTAT` | UNCLASSIFIED | Pro Baseball Team Stat | 120 |
| `KXMLBTEAMTOTAL` | TEAM_TOTAL | Pro Baseball Team Total | 210 |
| `KXMLBTOTAL` | GAME_TOTAL | Pro Baseball Total Points | 165 |
| `KXMLBTRADE` | UNCLASSIFIED | Pro Baseball Trades | 25 |
| `KXMLBWINS-ATH` | SEASON_WIN_TOTAL | Pro baseball wins A's | 7 |
| `KXMLBWINS-ATL` | SEASON_WIN_TOTAL | Pro baseball wins Atlanta | 7 |
| `KXMLBWINS-AZ` | SEASON_WIN_TOTAL | Pro baseball wins Arizona | 7 |
| `KXMLBWINS-BAL` | SEASON_WIN_TOTAL | Pro baseball wins Baltimore | 7 |
| `KXMLBWINS-BOS` | SEASON_WIN_TOTAL | Pro baseball wins Boston | 7 |
| `KXMLBWINS-CHC` | SEASON_WIN_TOTAL | Pro baseball wins Chicago C | 7 |
| `KXMLBWINS-CIN` | SEASON_WIN_TOTAL | Pro baseball wins Cincinnati | 7 |
| `KXMLBWINS-CLE` | SEASON_WIN_TOTAL | Pro baseball wins Cleveland | 7 |
| `KXMLBWINS-COL` | SEASON_WIN_TOTAL | Pro baseball wins Colorado | 7 |
| `KXMLBWINS-CWS` | SEASON_WIN_TOTAL | Pro baseball wins Chicago W | 9 |
| `KXMLBWINS-DET` | SEASON_WIN_TOTAL | Pro baseball wins Detroit | 7 |
| `KXMLBWINS-HOU` | SEASON_WIN_TOTAL | Pro baseball wins Houston | 7 |
| `KXMLBWINS-KC` | SEASON_WIN_TOTAL | Pro baseball wins Kansas City | 7 |
| `KXMLBWINS-LAA` | SEASON_WIN_TOTAL | Pro baseball wins Los Angeles A | 7 |
| `KXMLBWINS-LAD` | SEASON_WIN_TOTAL | Pro baseball wins Los Angeles D | 7 |
| `KXMLBWINS-MIA` | SEASON_WIN_TOTAL | Pro baseball wins Miami | 7 |
| `KXMLBWINS-MIL` | SEASON_WIN_TOTAL | Pro baseball wins Milwaukee | 7 |
| `KXMLBWINS-MIN` | SEASON_WIN_TOTAL | Pro baseball wins Minnesota | 7 |
| `KXMLBWINS-NYM` | SEASON_WIN_TOTAL | Pro baseball wins New York M | 7 |
| `KXMLBWINS-NYY` | SEASON_WIN_TOTAL | Pro baseball wins New York Y | 7 |
| `KXMLBWINS-PHI` | SEASON_WIN_TOTAL | Pro baseball wins Philadelphia | 7 |
| `KXMLBWINS-PIT` | SEASON_WIN_TOTAL | Pro baseball wins Pittsburgh | 7 |
| `KXMLBWINS-SD` | SEASON_WIN_TOTAL | Pro baseball wins San Diego | 7 |
| `KXMLBWINS-SEA` | SEASON_WIN_TOTAL | Pro baseball wins Seattle | 7 |
| `KXMLBWINS-SF` | SEASON_WIN_TOTAL | Pro baseball wins San Francisco | 7 |
| `KXMLBWINS-STL` | SEASON_WIN_TOTAL | Pro baseball wins St. Louis | 7 |
| `KXMLBWINS-TB` | SEASON_WIN_TOTAL | Pro baseball wins Tampa Bay | 7 |
| `KXMLBWINS-TEX` | SEASON_WIN_TOTAL | Pro baseball wins Texas | 7 |
| `KXMLBWINS-TOR` | SEASON_WIN_TOTAL | Pro baseball wins Toronto | 7 |
| `KXMLBWINS-WSH` | SEASON_WIN_TOTAL | Pro baseball wins Washington | 7 |
| `KXMLBWORLD` | UNCLASSIFIED | World Baseball Classic | 0 |
| `KXMLBWORSTRECORD` | UNCLASSIFIED | Pro Baseball Best Record | 30 |
| `KXMLBWS` | UNCLASSIFIED | MLB World Series | 0 |
| `KXMLBWSMVP` | UNCLASSIFIED | Pro Baseball Championship MVP | 0 |
| `KXMLBWSTREAK` | UNCLASSIFIED | Longest Winning Streak | 30 |
| `KXNCAABASEBALL` | UNCLASSIFIED | College Baseball Champion | 0 |
| `KXNCAABBCONF` | UNCLASSIFIED | College Baseball Conference Tournament | 0 |
| `KXNCAABBFINAL` | UNCLASSIFIED | College Baseball Final Qualifiers | 0 |
| `KXNCAABBGAME` | GAME_WINNER | College Baseball Game | 0 |
| `KXNCAABBGS` | UNCLASSIFIED | College Baseball Golden Spikes Award | 0 |
| `KXNCAABBHR` | PLAYER_PROP | College Baseball Homeruns | 0 |
| `KXNCAABBPLAYOFFS` | UNCLASSIFIED | College Baseball Playoff Qualifiers | 0 |
| `KXNCAABBSPREAD` | RUN_LINE | College Baseball Spread | 0 |
| `KXNCAABBTOTAL` | GAME_TOTAL | College Baseball Total Runs | 0 |
| `KXNCAAMBACHAMP` | UNCLASSIFIED | College Baseball Championship | 0 |
| `KXNEXTMANAGERMLB` | UNCLASSIFIED | Next Manager | 43 |
| `KXNEXTTEAMMLB` | UNCLASSIFIED | MLB Player Next Team | 372 |
| `KXTEAMSINNCAABBWS` | UNCLASSIFIED | Teams in College Baseball Finals | 0 |
| `KXTEAMSINWS` | UNCLASSIFIED | Teams in MLB Finals | 225 |
| `KXWBCGAME` | GAME_WINNER | World Baseball Classic Game | 0 |
| `KXWBCHIT` | PLAYER_PROP | World Baseball Classic Hits | 0 |
| `KXWBCHR` | PLAYER_PROP | World Baseball Classic Homerun | 0 |
| `KXWBCKS` | UNCLASSIFIED | World Baseball Classic Strikeouts | 0 |
| `KXWBCRFI` | UNCLASSIFIED | World Baseball Class Run in First Inning | 0 |
| `KXWBCSPREAD` | RUN_LINE | World Baseball Classic Spread | 0 |
| `KXWBCTOTAL` | GAME_TOTAL | World Baseball Classic Total | 0 |
| `KXWINSTREAKHOUMLB10` | SEASON_WIN_TOTAL | Houston winning 10 games | 0 |
| `KXWSAL` | UNCLASSIFIED | MLB American League champion | 0 |
| `KXWSNL` | UNCLASSIFIED | MLB National League champion | 0 |
| `MLBCBA` | UNCLASSIFIED | MLB CBA | 0 |
| `MLBOAK` | UNCLASSIFIED | Oakland Athletics relocate | 0 |

## Table 3 — Depth and gate verdict

| Family | Sampled | Usable | Median half-spread (c) | Median depth within 5c (USD) | Min depth (USD) | Gate |
|---|---:|---:|---:|---:|---:|---|
| GAME_TOTAL | 20 | 20 | 18.25 | 0.0 | 0.0 | **FAIL** |
| GAME_WINNER | 20 | 20 | 1.0 | 1646.5 | 0.0 | PASS |
| PARTIAL_GAME_WINNER | 20 | 17 | 1.0 | 410.99 | 156.96 | PASS |
| PLAYER_PROP | 20 | 3 | 2.0 | 0.9 | 0.0 | **FAIL** |
| RUN_LINE | 20 | 20 | 25.5 | 0.0 | 0.0 | **FAIL** |
| SEASON_WIN_TOTAL | 20 | 10 | 1.5 | 5.96 | 0.42 | **FAIL** |
| TEAM_TOTAL | 20 | 20 | 0.5 | 2043.53 | 882.7 | PASS |
| UNCLASSIFIED | 20 | 18 | 4.25 | 61.36 | 0.57 | PASS |

## Table 4 — Unclassified series (review individually)

- `10Y2Y`
- `10Y3M`
- `1SONG-DRAKE`
- `1SONG-KDOT`
- `1SONGBILLIEEILISH`
- `1SONGCHAPPELLROAN`
- `1SONGMACKLEMORE`
- `538APPROVE`
- `538APPROVEMAX`
- `538APPROVEMIN`
- `538APPROVEY`
- `AAAGASD`
- `AAAGASM`
- `AAAGASMAX`
- `AAAGASMAXCA`
- `AAAGASMAXTX`
- `AAAGASMIN`
- `AAAGASMINCA`
- `AAAGASMINTX`
- `AAAGASW`
- `AAAGASY`
- `AAPLCEOCHANGE`
- `AAPLWATCH`
- `ACMAAOTY`
- `ACMAASWOTY`
- `ACMADOTY`
- `ACMAEOTY`
- `ACMAFAOTY`
- `ACMAGOTY`
- `ACMAMAOTY`
- `ACMAMEOTY`
- `ACMANDGOTY`
- `ACMANFAOTY`
- `ACMANMAOTY`
- `ACMASINGOTY`
- `ACMASOTY`
- `ACMASWOTY`
- `ACMAVMOTY`
- `ACPI`
- `ACPICORE`
- `ACPICORE-`
- `ADAMS`
- `AIDEBATES`
- `AILEGISLATION`
- `AITURING`
- `ALBUMTRACKSBRUNO`
- `ALTMAN`
- `AMACOTYKX`
- `AMAZONFTC`
- `AMBCN`
- `AMCCEOCHANGE`
- `ANIMEAOTY`
- `ANIMEBA`
- `ANIMEBCS`
- `ANIMEBF`
- `ANIMEBMC`
- `ANIMEBNS`
- `ANIMEBOA`
- `AOH1996`
- `AOTY`
- _...and 11124 more_

_An unclassified series is a finding, not noise — FAMILY_PATTERNS is a heuristic over ticker strings and every miss should be resolved by hand before this survey is treated as complete._
