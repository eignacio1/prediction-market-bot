# T-NNN — GG-045 Live-Window Kalshi Orderbook Depth Study (KXMLBHIT)

**Status:** DRAFT — sample 3 pending (~23:00Z 2026-07-19)
**Session:** Terminal C, worktree `session/20260718T052953Z-gg045-live-depth-pull`
**Governance:** GG-045 (capital ceiling from market depth), APR-0029 D2 (live-window-only pulls — satisfied for every sample below), feeds APR-0029 D1 go/no-go (**operator decision — deliberately NOT made in this memo**)
**Data:** `logs/orderbook_depth_mlb_20260718_175907.json` (sample 1), `logs/orderbook_depth_mlb_20260719_203317.json` (sample 2), `<sample 3 TBD>` + ESPN scoreboard snapshots alongside each. Raw per-level orderbooks preserved in every artifact.

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
| 3 | TBD ~23:00Z Jul-19 | late innings + LAD@NYY evening game | TBD | TBD |

Samples span two consecutive game-days (the Jul-18 evening window was missed during a session pause; the Jul-19 slate satisfies D2 identically and adds cross-day consistency). "Tradeable" below excludes near-resolved markets (best bid ≥97¢ on either side — e.g. `-1` hit markets after the player's first hit): sample 1 → 44/49, sample 2 → 373/521.

## 2. Combined resting depth vs the $500–$2,000 working estimate

Tradeable markets, combined both-sides all-levels resting depth (the metric the old estimate implicitly described):

| | min | p25 | median | p75 | mean | max |
|---|---|---|---|---|---|---|
| Sample 1 (n=44) | $3.61 | $7.44 | **$186** | $714 | $413 | $2,070 |
| Sample 2 (n=373) | $1.78 | $18.40 | **$195** | $1,058 | $578 | $2,956 |

60–61% of tradeable markets sit below $500 combined; ~95% below $2,000. **The $500–$2,000 estimate describes roughly the upper quartile, not the range. The median live in-play book is ~$200.** The estimate's ceiling is about right; its floor is ~2.5× too high as a central tendency.

## 3. The finding that changes the question: liquidity is one-sided, and the bot bets into the empty side

Resting depth is overwhelmingly NO-bid liquidity. The YES-bid book is near-empty across both samples (median committed USD at best YES bid: $0.25–0.29). On Kalshi mechanics, **a NO buy fills against resting YES bids** (deployable NO stake per level = qty × (1 − yes_price)); a YES buy fills against resting NO bids. The bot's direction mix is 94% NO for T1 (n=295 closed) and 72% NO for T4M-PROJ (n=1,197 closed) — **the dominant bet direction consumes the thin side of the book.**

Bot-perspective fillable stake, sample 2 tradeable (n=373):

| | touch (best level) median | whole-book median |
|---|---|---|
| NO bet | $20.79 | $26.71 |
| YES bet | $14.00 | $394.59 |

Fill feasibility at actual stake sizes (share of tradeable markets where the book can absorb the stake):

| Stake | NO @ touch | NO whole-book | YES whole-book |
|---|---|---|---|
| $0.55 (T4M-PROJ median) | 84% | 84% | 99% |
| $9 (T1 median) | 52% | 84% | 99% |
| $44 (T1 max to date) | 6% | 30% | 99% |
| $250 | 0% | 7% | 97% |
| $500 (= `max_single_event_exposure_usd`) | 0% | **2%** | 39% |

(Sample 1, single early game, is thinner still on the NO side: $9 whole-book 34%.)

## 4. Answers to the three GG-045 questions

**(a) Distribution vs estimate:** see §2 — median ~$200 combined; estimate's range is the top quartile.

**(b) Current paper stakes vs top-of-book:** current sizing is mostly inside the book. T4M-PROJ ($0.55 median, $1,000 bankroll) fills at touch in 84% of markets. T1 ($9 median at $799.78 bankroll) fills at touch in ~half, whole-book in 84%. But T1's observed max stake ($44) already exceeds touch liquidity in 94% of markets — the tail of the current stake distribution is already market-moving-sized on the NO side.

**(c) At what bankroll does Kelly sizing start moving these markets?** Stakes scale ~linearly with bankroll under fractional Kelly. T1's median stake hits the NO-side whole-book median (~$27) at roughly a **$2,400 bankroll** (touch median ~$21 at ~$1,900). T4M-PROJ has ~38× headroom (~$38K bankroll) at its current per-bet sizing. The prior working line "at $10K+ bankroll, full Kelly sizing would move the market" (CLAUDE.md) is **~4× too optimistic for T1's NO-dominant flow** — degradation on the measured books begins around $2–2.5K bankroll, within one order of magnitude of the current paper bankroll.

The $500 hard cap itself fails the script's 5%-of-combined-depth impact test in **100% of tradeable markets** in both samples, and is whole-book NO-fillable in 2%.

## 5. Caveats

1. **Resting book ≠ realized liquidity.** Market-maker quote refresh (replenishment after a fill) is invisible in a static snapshot; true fillable size over minutes is likely larger than the resting book. These figures are a lower bound on liquidity, but they are the only measurable bound, and the paper trader currently assumes fill-at-quote at any size — a fill-realism gap between the paper book and these measurements that G6→live translation must confront.
2. **Units assumption:** `orderbook_fp` quantity column read as contract count (fractional allowed); ladder shapes (e.g. 200-lot MM quotes at 88¢ next to 156-lot 1¢ lottery bids) support this, but it is documented as an assumption, not verified against a filled order.
3. n = 2 timepoints on 2 consecutive game-days (3rd pending); intra-day and week-scale variation unmeasured.
4. Near-resolved-market exclusion threshold (97¢) is a judgment call; sensitivity not tested.

## 6. APR-0029 D1 go/no-go — OPEN OPERATOR DECISION

This memo supplies the empirical prerequisite D1 was waiting on. **Whether to implement the depth-aware max_stake cap in `risk.py`, and at what parameters, is Earl's decision — deliberately not made here.** Points the data puts in front of that decision:

- A depth-aware cap keyed to *combined* depth would key on the wrong quantity for this book shape — the binding constraint is **side-specific fillable stake** (for NO bets: qty × (1 − yes_price) summed over the YES-bid book), which runs ~15× smaller than combined depth at the median.
- Current median stakes are inside the book, so a cap would rarely bind today at $800–$1,000 bankrolls; it starts doing real work at ~$2–2.5K T1 bankroll.
- The static $500 cap is not a meaningful depth guard in these markets (2% NO-fillable).

## 7. Registry actions taken this session

- GG-045 updated with measured figures (this memo is the evidence artifact).
- T-377 pregame-zero finding annotated as parser-confounded (§0).
- DECISION_LOG entry added (Hard Rule 7).
- Raw artifacts copied to main-tree `logs/` (gitignored per retention policy — deliberate).
