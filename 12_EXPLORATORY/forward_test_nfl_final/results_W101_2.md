# W101.2 Part A: the ADR-0072 NFL final word (read-only; nothing applied)

Source: box `exp_output/FORWARD_TEST/demo_fill_forward_report.json` (generated 2026-11-04T11:25Z), `logs/demo_fill_forward_report.log`,
`markouts/markouts.jsonl` (read directly over ssh, read-only). Code: `scripts/demo_fill_forward_report.py` at origin/main `36f49a9`.

## VERDICT WORD (the pre-registration, as the code applies it): **ADOPT - (a), (b), (c) all hold at judged n** (NFL, shadow book)

Premise correction: the daily log prints `shadow|NFL: ADOPT` first on the **2026-11-02T11:25Z** line (not 11-03); 11-01 read
"(a)/(b) hold, pending (c)". Cause: the NFL treatment arm's 550th markout-bearing fill landed 2026-11-02T00:55:59Z (control's was
2026-10-25T19:41Z), so the first daily report after that instant (11-02 11:25Z) is the 10-21 addendum's "one more look". 11-02, 11-03
and 11-04 all read ADOPT: the word did not flip. (I could not replay the exact 11-02 numbers; the box keeps only the log line and the
latest JSON. The log line shows (a) s-p +0.05 control / +0.24 treatment on 11-02 and +0.06 / +0.25 on 11-04.)

## Numbers (post-top-up, shadow/NFL, as of 2026-11-04T11:25Z; 41 games)

| Quantity | Control | Treatment | Result |
|---|---|---|---|
| Post-top-up fills | 6,904 settled | 2,590 settled | judged n 550 per arm met with room |
| Post-top-up ok orders | 13,748 | 13,742 | |
| Fill rate | 50.3% | 18.9% | (b) ratio **0.376** >= 0.25: holds |
| (a) mean settle-minus-price, diff | | | **+0.190**, se 0.062, one-sided 95% game-clustered lower bound **+0.088** > 0: holds; upper 95% +0.291, so REJECT (< +0.05) does not fire |
| Markout-bearing fills (post 10-21T04:30Z) | 1,307 | 573 | judged (>= 550 per arm); treatment crossed 11-02T00:55Z |
| (c) 30-min markout, treatment minus control | | | **-0.0117**, se 0.0132, 95% interval [-0.0334, +0.0101]; upper bound >= 0: "holds" |

## Code against the addenda, line by line

| Rule (addendum) | Code | Match |
|---|---|---|
| "Judged" for (c) = >= 550 markout-bearing fills per arm (10-21) | `markout_c`: counts rows with `h30` not null, fill_ts >= EPOCH, `c["n"] >= JUDGED_N and t["n"] >= JUDGED_N` | YES |
| (a)/(b) judged n = >= 550 post-top-up settled fills per arm (10-20) | `verdict_for`: `min_n` of clustered settled-fill counts | YES |
| Cash-starved days excluded (orders before 2026-10-16T05:40Z) | `ots < TOPUP_TS` skipped for verdict fills; `orders_post` for (b) | YES |
| Per (book, sport) | verdict keyed `(book, sport)`, shadow only | YES |
| Game-clustered one-sided 95% | `_clustered` (ratio estimator, games = clusters), Z=1.645 | YES |
| (b) = fills / ok orders, treatment >= 25% of control | `orders_post` counts `ok` orders only; rejected excluded | YES |
| (c) fails only if upper95 < 0 | `holds = upper95 >= 0` | YES |
| Reject if upper95 of (a) diff < +0.05 | `REJECT_UPPER = 0.05` | YES |

No departure on any pre-registered parameter, so **no GG for a code-vs-addendum gap; code and addendum give the same word.**
Two observations, neither a departure (to be registered by the strategic window if it wants them):
1. `markout_c` filters markouts by sport only (markout rows carry no `book`). Today it is equivalent to per-book because the collector
   (`demo_fill_markout_collector.py`) reads only `shadow_order` events. It would silently pool books if the collector ever read paper.
2. The 10-21 addendum says the look is taken "once"; the report recomputes daily. The word has been stable for three days, so this
   changes nothing now, but a later flip would have no pre-registered answer to "which day was the look".

## Reconciling with W98.2 ("treatment's large positive P&L comes from which orders fill after waiting 60 s, not from a measured edge")

Does (c) answer it for NFL? **Partly.** What it answers: after a treatment order fills, does the market keep drifting against the held
side by more than control's fills do? The 30-minute held-side mid minus fill price is -0.012 for treatment relative to control,
not credibly different from zero. So there is no measured sign that the waited-for fills are being picked off by informed flow
that moves the price afterward. That is the specific adverse-selection worry, and it is not supported.

What (c) does not answer:
- **Why those orders fill.** Waiting 60 s fills an order when the book moves to it. (a) +0.19 is a difference in settle-minus-price
  between *different populations of fills* (62% of control's fills never happen in treatment). It tells us the surviving fills are
  better; it does not say the posting rule creates edge, which is W98.2's point and still stands. (c) is nearly silent on it.
- **The interval is wide on the harmful side.** "Holds" means only that the upper bound is not below 0. The data are equally
  consistent with treatment's markout being worse by up to ~3.3 cents (lower bound -0.033), against an (a) gain of 8.8 to 29 cents.
  (c) as pre-registered is a "not credibly worse" test, not a "not worse by more than X" test; I changed neither.
- **Entry versus pricing.** W98.2 found taking at the quote costs ~0.10 per contract in NFL. Treatment's gain is partly the cost of
  *not* paying that, and is available only if the order fills.
- **Per-order view (descriptive, not pre-registered).** Per submitted order, control earned 6,960 x 0.0563 / 13,860 = +0.028 and
  treatment 2,604 x 0.2463 / 13,852 = +0.046 (source: the cell rows in the same JSON, which include pre-top-up). Treatment is ahead
  per order, so it is not "better only because it trades less", but this figure was not in the pre-registration and is not a score.
- 41 games, two arms of the same games: the clustering is right, but the claim is about NFL shadow demo books, not live capital.

## OPERATOR LINE (plain English)

The pre-registered NFL word is **ADOPT**: NFL shadow demo orders placed treatment-style (post at the book, cancel at 60 s) fill about
a third as often but their fills earn about 19 cents more per contract than the old way, with no sign the price moves against them
afterward. **Recommendation: adopt for NFL shadow demo orders only, as an experiment, not as proof of edge** - W98.2's caution that
the gain is about which orders fill still stands, the afterward-price check is weak on the harmful side, and it changes a pre-registered
test's placement, so I have not applied it; that call is yours. Keep NBA and NHL running as they are.

NBA: (a) holds, (b) fails (fill ratio 0.203 < 0.25): "removed fills, not adverse selection", not adopted; its markouts are 544 treatment
fills, 6 short of judged. NHL: (a) holds, (b) fails (0.222): same word; NHL markouts 149 treatment fills, not judged. Neither can ADOPT
under the pre-registration unless (b) moves, so a markout read does not change their words.
