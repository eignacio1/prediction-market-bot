
## W119.2 — NBA depth wired (STANDARD)
NBA depth splits (matchup, rest, refs-style factors) are now wired into the router behind a switch that is OFF. Nothing live changed. The 12 NBA game cells now show as SHADOW in code, so the code count and the box agree at 60. A new layer-4 rule credits NBA spread T1 and team-total T1; D6 for NBA went from 4 to 7 wired on the box. Not credited: NBA moneyline T1-T3 (no per-arm evidence yet). Two factors (S3/S5) have no live data source on the box and log "unknown". Merged as PR #527, deployed. Your call later: when to flip the switch once shadow rows accrue.
## W119.3 - placement and log size (Earl)
- Moved: EXECUTION. The bot's FADE orders now try a better price on half of them, rest inside the spread, with the other half as the comparison. It's live on the box. Demo only, no real money.
- Early count only: 2 fills of 17 inside orders versus 22 of 342 at the touch. Far too few to judge; we need 100 orders and 20 games per side.
- The daily spending caps still block thousands of orders (about 5,000 RIDE, 2,000 each FADE and MOMENTUM) even after we raised them. Needs a look.
- The ride-board log is cut to what readers use; the real size saving shows up in about two days.
- Main's guard check was red from another window's gap cleanup; I fixed it with a generated file.

## W119.4 — your evidence is now copied off the server
- Your price history, Kalshi history and settled records now have a second copy on your Mac (about 7.2 GB, 5,827 files). I checked every file against the server's copy and they match.
- Nothing was deleted anywhere. Once the server deploys the new code, it will start compressing old price days to free space. I don't yet know how much that frees, so I can't say the server will reach 50%.
- Two groups of files stay uncompressed for now because I couldn't prove every program reading them handles compressed files.
- Needs your yes: install the weekly copy to your Mac (about 2 GB a month)? It is written but not switched on.
- Pillar moved: plumbing (evidence safety). No real money involved.
- W120.4 (auto): W120.4: Strategy/Architecture overviews rewritten to DOCTRINE; PRs 477/458 closed; dashboard wording + CLAUDE.md fixed.

**W120.1 (NFL):** NFL bets now record which of our tested rules applied to them, which is the missing step that kept NFL cells from counting as wired. Nothing changes in how orders are placed; no real money involved. We can't say how many NFL cells count until the next NFL games (Nov 22-23) produce rows; the recount is queued.
- W120.3 (auto): W120.3: three held readers read .gz, Mac evidence copy compacted 7.21->5.70 GiB, box disk still 74% until the 14:17Z retention apply (~63% expected); weekly Mac job awaits operator yes.

**W120.2 (depth):** The three newer routing maps now write down what they would have done next to the live one, on every NBA and NFL shadow row (about 70 rows each in the first hour; NHL appears after its daily 14:00Z run). Orders still follow the live map only, no real money. NHL goalie and special-teams results are recorded but not applied, because applying them would change live NHL orders. One process slip, disclosed: my first commit reached main before any pull request existed; the later checks came back green and nothing changed in behavior.
