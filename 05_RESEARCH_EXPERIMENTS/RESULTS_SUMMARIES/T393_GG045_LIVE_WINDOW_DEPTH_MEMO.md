# T-393 — GG-045 Live-Window Kalshi Orderbook Depth Study (KXMLBHIT)

**Status:** COMPLETE — 3 valid samples collected, analyzed, write-back done.
**Session:** Terminal C (samples 1-2, drafting) → crashed before sample 3 write-back → resumed by a Cowork session (2026-07-20/21) which diagnosed the VPS one-shot's empty result, located a second, valid, previously-undocumented local pull Terminal C had made before crashing, adopted it as sample 3, and completed the write-back. Worktree `session/20260718T052953Z-gg045-live-depth-pull`.
**Governance:** GG-045 (capital ceiling from market depth), APR-0029 D2 (live-window-only pulls — satisfied for every sample below), feeds APR-0029 D1 go/no-go (**operator decision — deliberately NOT made in this memo**)
**Data:** `logs/orderbook_depth_mlb_20260718_175907.json` (sample 1), `logs/orderbook_depth_mlb_20260719_203317.json` (sample 2), `logs/orderbook_depth_mlb_20260720_012459.json` (sample 3) + ESPN scoreboard snapshots alongside each. Raw per-level orderbooks preserved in every artifact. A fourth artifact, `logs/orderbook_depth_mlb_20260719_230502.json` (the VPS-scheduled systemd-run one-shot, fired 23:05:02Z as designed), returned **zero matched markets** — not a bug; see §1a.

---

## 0. Critical methodology finding first: the parser bug that confounds all prior depth reads

Kalshi's `/markets/{ticker}/orderbook` endpoint now returns **only** the fixed-point schema:

```json
{"orderbook_fp": {"yes_dollars": [["0.1200", "3.00"], ...], "no_dollars": [...]}}
```

— dollar-string prices, (possibly fractional) contract-count quantities. The legacy `{"orderbook": {"yes": [[cents, qty]], ...}}` key that `scripts/query_orderbook_depth_mlb.py` parsed is **gone entirely**. Every pre-2026-07-18 run of this script therefore reported `combined_depth_usd = $0.00` unconditionally, regardless of actual book state.

**Consequence: T-377's pregame "all-zero depth" finding is confounded.** It was read at the time as strong second-instance evidence (with GG-041/NBA) that pregame books are empty; in fact the script could not have reported anything but zero. The T-377 artifact stored only computed metrics (not raw responses), and its worktree is retired, so the true pregame book state on that date is unrecoverable. APR-0029 D2 (live-window-only pulls) remains sound on GG-041's independent evidence and on first principles, but the MLB pregame-zero data point should no longer be cited as measured fact. The parser was fixed this session (worktree commit `82ec70f`, both schemas handled); all figures below are from the fixed parser, cross-validated against nonzero `yes_bid/yes_ask/volume` on the corresponding market objects.

A secondary sampling hazard, also fixed in method: `--all --limit N` mode front-loads pregame markets (API ordering) — a 50-market sample at 17:54Z Jul-18 contained **zero** live-game markets. All valid samples below use targeted per-ticker pulls on markets matched to ESPN-confirmed live games. (Note: rolled-over/makeup games keep their original ticker date-code — PIT@CLE's Jul-18 games traded under `26JUL171910PITCLE` tickers. Match by team code, not date.)

## 1. Samples

| # | UTC time | Slate state (ESPN, snapshot on file) | Markets pulled | Nonzero books |
|---|----------|--------------------------------------|----------------|---------------|
| 1 | 2026-07-18 17:59Z | 1 game live (PIT@CLE, Bot 4th) | 49 (all PITCLE) | 49/49 |
| 2 | 2026-07-19 20:33Z | **10 games live** (peak overlap — the state T4M-PROJ trades into) | 521 across all 10 games | 521/521 |
| 3 | 2026-07-20 01:25Z | 1 game live, late innings (LAD@NYY G2, Bot 7th) | 57 (all LADNYY G2) | 57/57 |

Samples span two consecutive game-days (the Jul-18 evening window was missed during a session pause; the Jul-19 slate satisfies D2 identically and adds cross-day consistency). "Tradeable" below excludes near-resolved markets (best bid ≥97¢ on either side — e.g. `-1` hit markets after the player's first hit): sample 1 → 44/49, sample 2 → 373/521, sample 3 → 47/57.

### 1a. The scheduled VPS one-shot (23:05Z Jul-19) returned zero matched markets — explained, not a defect

Terminal C's design for sample 3 was a laptop-independent `systemd-run` one-shot on the VPS (`scripts/vps_gg045_sample3.py`, timer `gg045-sample3.timer` @ 23:05:02Z + guarded backup `gg045-sample3-backup.timer` @ 23:50:00Z). Both timers fired exactly as designed — confirmed via `journalctl` — and the backup's self-skip guard worked correctly (it saw the primary's artifact already logged and did not re-run). But the primary run's artifact (`logs/orderbook_depth_mlb_20260719_230502.json`, retrieved from the VPS post-crash) has `"results": []`: ESPN showed exactly one live game (STL@ARI, Bot 8th) at pull time, and 0 of that game's 120 `status="open"` KXMLBHIT tickers matched.

This was root-caused (not left as an open question): the away+home ticker-code convention the script used was independently re-verified correct against a separate 11-game live window the same investigating session found later that night (875 open markets, all ticker codes matched their ESPN shortNames exactly). The real cause is structural — **individual KXMLBHIT batter markets close progressively as each player completes his plate appearances for the game, not at the game's final out.** By Bot 8th of a lone remaining game, most or all of that specific game's own batter markets had already closed; the 120 open markets that did exist at 23:05Z all belonged to other, not-yet-started or next-day games. A "lone late-inning game" sampling design will structurally tend toward zero open markets for that game, independent of any matching bug. This is itself a useful finding for anyone designing future live-window pulls: **target overlap windows (multiple concurrent games) or mid-to-late-but-not-final innings, not a single game's last frame.**

Sample 3 as adopted below is a different, valid pull — found already sitting in the worktree's local (gitignored) `logs/`, timestamped 01:24:59Z Jul-20 (~2h20m after the VPS one-shot), evidently run manually by Terminal C against LAD@NYY Game 2 while it was live (Bot 7th) shortly before the session crashed, and never written back. It satisfies D2 (ESPN snapshot on file confirms `state=="in"`) and is single-game/late-innings in character, matching the original sample-3 design intent better than a multi-game overlap would (samples 2 and 3 are then usefully different window *types*, not two overlap samples).

## 2. Combined resting depth vs the $500–$2,000 working estimate

Tradeable markets, combined both-sides all-levels resting depth (the metric the old estimate implicitly described):

| | min | p25 | median | p75 | mean | max |
|---|---|---|---|---|---|---|
| Sample 1 (n=44) | $3.61 | $7.44 | **$186** | $714 | $413 | $2,070 |
| Sample 2 (n=373) | $1.78 | $18.40 | **$195** | $1,058 | $578 | $2,956 |
| Sample 3 (n=47) | $3.54 | $16.86 | **$66** | $663 | $504 | $7,545 |

60–70% of tradeable markets sit below $500 combined; ~95-96% below $2,000, across all three samples. **The $500–$2,000 estimate describes roughly the upper quartile, not the range. The median live in-play book is ~$70-$200, trending lower in the single-game late-innings sample (fewer, more-resolved markets pull the median down).** The estimate's ceiling is about right; its floor is 2.5-7× too high as a central tendency.

## 3. The finding that changes the question: liquidity is one-sided, and the bot bets into the empty side

Resting depth is overwhelmingly NO-bid liquidity. The YES-bid book is near-empty across all three samples (median committed USD at best YES bid: $0.16–0.29). On Kalshi mechanics, **a NO buy fills against resting YES bids** (deployable NO stake per level = qty × (1 − yes_price)); a YES buy fills against resting NO bids. The bot's direction mix is 94% NO for T1 (n=295 closed) and 72% NO for T4M-PROJ (n=1,197 closed) — **the dominant bet direction consumes the thin side of the book.**

Bot-perspective fillable stake:

| | touch (best level) median | whole-book median |
|---|---|---|
| NO bet, sample 2 (n=373) | $20.79 | $26.71 |
| YES bet, sample 2 (n=373) | $14.00 | $394.59 |
| NO bet, sample 3 (n=47) | $4.80 | $24.75 |
| YES bet, sample 3 (n=47) | $0.50 | $342.77 |

Fill feasibility at actual stake sizes (share of tradeable markets where the book can absorb the stake):

| Stake | S2 NO @ touch | S2 NO whole-book | S2 YES whole-book | S3 NO @ touch | S3 NO whole-book | S3 YES whole-book |
|---|---|---|---|---|---|---|
| $0.55 (T4M-PROJ median) | 84% | 84% | 99% | 70% | 70% | 100% |
| $9 (T1 median) | 52% | 84% | 99% | 43% | 70% | 100% |
| $44 (T1 max to date) | 6% | 30% | 99% | 2% | 23% | 100% |
| $250 | 0% | 7% | 97% | 0% | 2% | 98% |
| $500 (= `max_single_event_exposure_usd`) | 0% | **2%** | 39% | 0% | **2%** | 30% |

(Sample 1, single early game, is thinner still on the NO side: $9 whole-book 34%. Sample 3 — also a single late-innings game — is the thinnest of the three, consistent with §1a's progressive-closure finding: the markets still open that late skew toward thin, near-the-margin books.)

## 4. Answers to the three GG-045 questions

**(a) Distribution vs estimate:** see §2 — median ~$70-$200 combined depending on sample; estimate's range is the top quartile in all three.

**(b) Current paper stakes vs top-of-book:** current sizing is mostly inside the book. T4M-PROJ ($0.55 median, $1,000 bankroll) fills at touch in 70-84% of markets across samples. T1 ($9 median at $799.78 bankroll) fills at touch in roughly half (sample 2) to less than half (sample 3), whole-book in 70-84%. But T1's observed max stake ($44) already exceeds touch liquidity in 94-98% of markets — the tail of the current stake distribution is already market-moving-sized on the NO side, and the effect is worse in the thinner single-game sample.

**(c) At what bankroll does Kelly sizing start moving these markets?** Stakes scale ~linearly with bankroll under fractional Kelly. T1's median stake hits the NO-side whole-book median (sample 2: ~$27, sample 3: ~$25) at roughly a **$2,200-2,400 bankroll** (touch median ~$21 sample 2 / ~$4.80 sample 3 — sample 3's touch threshold is reached far sooner, around $440-800). T4M-PROJ has ~38× headroom (~$38K bankroll) at its current per-bet sizing on sample 2's book; sample 3's thinner book cuts that headroom further. The prior working line "at $10K+ bankroll, full Kelly sizing would move the market" (CLAUDE.md) is **~4-19× too optimistic for T1's NO-dominant flow** depending on which sampled window is used — degradation on the measured books begins around $500-2.5K bankroll, at or below the current paper bankroll in the thinnest sampled case.

The $500 hard cap itself fails the script's 5%-of-combined-depth impact test in **100% of tradeable markets** in all three samples, and is whole-book NO-fillable in only 2%.

## 5. Caveats

1. **Resting book ≠ realized liquidity.** Market-maker quote refresh (replenishment after a fill) is invisible in a static snapshot; true fillable size over minutes is likely larger than the resting book. These figures are a lower bound on liquidity, but they are the only measurable bound, and the paper trader currently assumes fill-at-quote at any size — a fill-realism gap between the paper book and these measurements that G6→live translation must confront.
2. **Units assumption:** `orderbook_fp` quantity column read as contract count (fractional allowed); ladder shapes (e.g. 200-lot MM quotes at 88¢ next to 156-lot 1¢ lottery bids) support this, but it is documented as an assumption, not verified against a filled order.
3. n = 3 timepoints across 2 consecutive game-days; intra-day and week-scale variation still only lightly sampled (two single-game and one 10-game-overlap window). Sample 3's thinness may partly reflect its single-late-game character (§1a) rather than a distinct depth regime — cannot yet separate "time of night" from "number of concurrently live games" as the driving variable with n=3.
4. Near-resolved-market exclusion threshold (97¢) is a judgment call; sensitivity not tested.
5. The scheduled VPS one-shot's zero-match result (§1a) is informative about market-close dynamics but is not itself a depth data point — excluded from all statistics above.

## 6. APR-0029 D1 go/no-go — OPEN OPERATOR DECISION

This memo supplies the empirical prerequisite D1 was waiting on. **Whether to implement the depth-aware max_stake cap in `risk.py`, and at what parameters, is Earl's decision — deliberately not made here.** Points the data puts in front of that decision:

- A depth-aware cap keyed to *combined* depth would key on the wrong quantity for this book shape — the binding constraint is **side-specific fillable stake** (for NO bets: qty × (1 − yes_price) summed over the YES-bid book), which runs ~7-15× smaller than combined depth at the median, and varies by window type (single-game late-innings books ran thinner than the 10-game overlap window).
- Current median stakes are inside the book, so a cap would rarely bind today at $800–$1,000 bankrolls; it starts doing real work anywhere from ~$500 (thinnest sampled window) to ~$2.5K (peak-overlap window) T1 bankroll.
- The static $500 cap is not a meaningful depth guard in these markets (2% NO-fillable in every sample).

## 7. Registry actions taken this session

- GG-045 updated with measured figures from all three samples (this memo is the evidence artifact).
- T-377 pregame-zero finding annotated as parser-confounded (§0).
- Sample 3's VPS-scheduled empty result documented and root-caused, not silently dropped (§1a).
- DECISION_LOG entry added (Hard Rule 7).
- Raw artifacts (4: samples 1-3 + the empty VPS run) copied to main-tree `logs/` (gitignored per retention policy — deliberate).
