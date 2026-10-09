> **HISTORICAL (banner added 2026-10-09):** a dated working file from 2026-07-20, kept at the repo root because other files reference it. It does not describe the current project — start at `README.md` / the RUNNING SITREP in `04_EXECUTION/ACTIVE_QUEUE.md`.

# Terminal C — GG-045 live-window depth pull — session state

## Fixed facts
- Worktree: /Users/earlignacio/Documents/Claude/Projects/PM-worktrees/20260718T052953Z-gg045-live-depth-pull
- Branch: session/20260718T052953Z-gg045-live-depth-pull (pushed claim via claim_session.sh, ID=TBD — assign real T-number fresh at write-back time, check SESSION_CLAIMS/TODO_NEXT/DECISION_LOG for highest; T-385 was highest at claim time, collisions rampant)
- Script committed edit e8fcd94: audit JSON now includes raw_orderbook per market.
- Auth VERIFIED working (05:40Z): 136 open KXMLBHIT markets for Jul-18 slate.
- Run env: must `set -a; source "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets/.env"; set +a` before python (worktree has no .env — do NOT copy it in).
- Shell cwd resets between Bash calls — cd into worktree in every command.

## Governing rules
- APR-0029 D2 (ADOPTED): pull ONLY while ≥1 MLB game is ESPN state=="in". Gate before every pull.
- Evidence-only session: do NOT implement D1 max_stake cap in risk.py. D1 go/no-go is Earl's decision — flag it open.
- Hard Rule 7: DECISION_LOG entry at write-back. Path-scoped commits only. Re-read shared nav files fresh before writing (Terminal A/B may be active).

## Slate (2026-07-18, first pitches UTC)
17:10 PIT@CLE, 18:20 MIN@CHC, 19:07 CHW@TOR, 19:10 CIN@COL, 20:05 NYM@PHI, 20:10 TB@BOS, more later (16 games total).

## Sample plan (3 timepoints)
1. ~17:45Z early window (1 game live) — DONE [x] 17:59Z: logs/orderbook_depth_mlb_20260718_175907.json (valid, fixed parser) + 175428.json (INVALID - broken parser + pregame-only sample) + 175624.json (INVALID - broken parser)
2. ~20:30Z peak overlap — DONE [x] BUT ON 2026-07-19 SLATE (Jul-18 sample-2/3 window missed during token pause; D2 satisfied identically). 20:33Z Jul-19, 10 games live (NYMPHI/BALHOU/MIAMIL/SDKC/MINCHC/CINCOL/WSHATH/DETLAA/SFSEA/STLARI): logs/orderbook_depth_mlb_20260719_203317.json — 521 live-game markets, 521/521 nonzero, combined min $1.78 / median $377.26 / mean $633.14 / max $4,905.30. ESPN snapshot logs/espn_scoreboard_20260719_203106.json.
3. ~23:00Z Jul-19 late innings — RUNS ON VPS, NOT LOCALLY. systemd-run timers on prediction-market-vps: gg045-sample3.timer @ 23:05Z + gg045-sample3-backup.timer @ 23:50Z (guarded: skips if runner log already shows "artifact:"). Runner: /opt/prediction-market-bot/scripts/vps_gg045_sample3.py (committed 82b0ce9; fixed-parser query script also deployed to VPS scripts/). Output on VPS: logs/orderbook_depth_mlb_<ts>.json (sample3_late_innings) + espn snapshot + logs/gg045_sample3_runner.log. Exit 2 = D2 gate failed.
   LOCAL SESSION JOB at next wake after 23:05Z (laptop may sleep through — wakeup fires late, that's fine, artifact is durable): (a) ssh check runner log + scp artifact & espn snapshot into worktree logs/; (b) verify nonzero + run same analysis (fillable-stake script pattern in transcript); (c) finalize memo TBDs; (d) write-back checklist; (e) CLEAN UP VPS: rm scripts/vps_gg045_sample3.py is NOT needed (harmless, committed) but remove leftover timers if any failed to self-clean (systemd-run one-shots auto-clean after firing; check systemctl list-timers 'gg045-*').
NOTE FOR MEMO: samples span two consecutive game-days (Jul-18 sample 1, Jul-19 samples 2-3) — cross-day consistency is a strength, note the slate difference.

## CRITICAL FINDINGS SO FAR (write-back must include)
- PARSER BUG (fixed, commit after e8fcd94): Kalshi orderbook endpoint now serves ONLY orderbook_fp {yes_dollars/no_dollars, dollar-string prices, fractional contract qty}; legacy "orderbook" key gone. ALL prior runs (T-377 pregame zeros included) reported $0.00 unconditionally — T-377's "all-zero pregame" finding is CONFOUNDED (its worktree is retired, raw responses unrecoverable, only metrics stored). GG-045 entry text claiming "strong second-instance evidence" (with GG-041) must be corrected.
- --all mode SAMPLING BUG: fetch order front-loads pregame markets; 50-cap sample had 0 live-game markets. Use targeted per-ticker pulls on live games (match ESPN live games to ticker team codes). 318 open markets total; ~50/game.
- PIT@CLE DH game-1 markets carry YESTERDAY's ticker date (26JUL171910PITCLE) — postponed game rolled over. Match by team code, not date.
- Sample 1 results (49 PITCLE mkts, Bottom 4th): 49/49 nonzero. combined min $3.61 / median $191.26 / mean $879.64 / max $5,653. Big figures = near-resolved markets (YES best 99c). In-play books ~$100-$2,000, skewed low. Median $191 < $500 hard cap — GG-045 is LIVE at current stake sizes, pending top-of-book analysis.
- Units assumption: fp qty column = contract count (fractional allowed). Documented in artifact notes.
- Terminal B worktree active: 20260718T052035Z-terminal-b-gov-writeback — re-read nav files fresh at write-back, expect conflicts.

## ANALYSIS DONE (samples 1-2; memo drafted in worktree 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/TNNN_GG045_LIVE_WINDOW_DEPTH_MEMO.md — rename TNNN at write-back)
- Tradeable = excl. near-resolved (best bid >=97c either side). S1: 44/49; S2: 373/521.
- Combined depth (tradeable): S1 med $186 / mean $413 / max $2,070; S2 med $195 / mean $578 / max $2,956. 60-61% of tradeable markets < $500 combined; 95% < $2,000. → $500-$2,000 estimate is roughly the UPPER quartile, not the range; median is ~$200.
- SIDE ASYMMETRY: resting depth overwhelmingly NO-bid book (YES-bid book near-empty: med TOB $0.25-0.29 in committed USD).
- BOT-PERSPECTIVE FILLABLE STAKE (correct units: NO bet consumes YES-bid book, deployable = qty*(1-yes_price); YES bet consumes NO-bid book = qty*(1-no_price)):
  S2 (10 games): NO-fill touch med $20.79 / whole-book med $26.71; YES-fill touch med $14 / whole-book med $394.59.
  Fill feasibility S2: $0.55 (T4 med stake): NO touch 84%. $9 (T1 med): NO touch 52%, whole-book 84%. $44 (T1 max): NO touch 6%, whole-book 30%. $250: NO whole-book 7%. $500 cap: NO whole-book 2%, YES whole-book 39%.
- Real stakes (VPS portfolios, pulled 2026-07-19): T1 bankroll $799.78, closed n=295 med $8.96 max $43.56, 94% NO; T4M-PROJ bankroll $1,000, closed n=1197 med $0.55 max $0.96, 72% NO. (NB paper_2026*.json files without _mlb suffix = NBA book, bets_placed=0 off-season — do not confuse.)
- Kelly-degradation bankroll (stake scales ~linearly with bankroll): T1 med stake $9 @ $800 bankroll → hits NO-side whole-book med $27 at ~$2,400 bankroll (~$1,900 for touch med $21). T4M-PROJ ~$38K bankroll before med stake exceeds touch. CLAUDE.md's "$10K+ bankroll" line is ~4x too optimistic for T1 NO bets.
- $500 max_single_event_exposure_usd cap: fails script's 5%-impact test in 100% of tradeable mkts both samples; whole-book NO-fillable in 2%.
- CAVEAT for memo: resting book != realized liquidity (MM quote refresh not visible); paper fills assume fill-at-quote — flag fill-realism, don't adjudicate.

## Sample 2/3 procedure (use this, NOT --all)
cd worktree; source main-tree .env; PYTHONPATH=src python3 with: ESPN snapshot -> live game shortNames -> team-code strings (e.g. 'PITCLE','MINCHC','NYMPHI','CHWTOR','CINCOL','TBBOS') -> pull ALL open KXMLBHIT markets whose ticker contains any live game's code -> per-ticker fetch_orderbook + compute_depth_metrics (fixed parser) -> artifact logs/orderbook_depth_mlb_<ts>.json with sample_label sample2_peak_overlap / sample3_late_innings, live_games_espn list, market_quote (yes_bid/yes_ask/volume) per market, raw_orderbook=full raw.

## Per-sample procedure
1. ESPN gate + snapshot:
   curl -s "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard" > logs/espn_scoreboard_$(date -u +%Y%m%d_%H%M%S).json  (run inside worktree; then summarize states; require >=1 "in")
2. Pull: cd worktree && set -a; source main-tree .env; set +a && PYTHONPATH=src python3 scripts/query_orderbook_depth_mlb.py --all --limit 50
   (writes logs/orderbook_depth_mlb_<UTC>.json in worktree)
3. If --all errors mid-window: fall back to --ticker on markets from confirmed-live games (match ticker date/team codes to live ESPN games).
4. Record which games were live at pull time.

## Write-back checklist (after sample 3)
- [ ] Copy logs/orderbook_depth_mlb_*.json + espn snapshots to MAIN tree /Users/earlignacio/Documents/Claude/Projects/Prediction Markets/logs/ (worktree logs/ dies at retirement; logs/ is gitignored both places — that is expected, retention policy)
- [ ] Analysis: per-market combined-depth distribution; side-split + top-of-book from raw_orderbook; vs $500-$2,000 estimate; ratio of live paper stake sizes to top-of-book; bankroll level at which Kelly sizing moves market (LIVE_CAP=500, DEPTH_IMPACT_THRESHOLD_PCT=0.05 in script)
- [ ] Memo: 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/<T-NNN>_GG045_LIVE_WINDOW_DEPTH_MEMO.md
- [ ] GG-045 entry update (measured figures; re-read fresh from HEAD first)
- [ ] DECISION_LOG.md entry (re-read fresh first)
- [ ] Resolve TBD claim row → real T-number (check collisions at that moment)
- [ ] Flag APR-0029 D1 go/no-go as OPEN operator decision — do not decide
- [ ] Commit path-scoped, push branch, PR to main, /session-end, retire worktree

## Wakeup chain
Idle hourly (3600s clamp) until ~16:45Z; then ESPN-gate; pull 1 when >=1 game "in" (~17:45Z target). Between samples: chain wakeups (20:30Z and 23:00Z targets).

## Addendum 2026-07-20/21 (Cowork resume session, after Terminal C crash) — sample 3 diagnosed EMPTY, not yet replaced

**Context:** Terminal C crashed (froze, unrecoverable) before it could retrieve sample 3 or write back. Original worktree/branch were intact on disk and on origin (contrary to what Terminal C's last state believed — "prunable, directory gone" was wrong; verify before trusting a crashed session's own self-report).

**Sample 3 (VPS systemd-run one-shot) DID fire correctly, but produced an EMPTY artifact:**
- `gg045-sample3.timer` fired 2026-07-19 23:05:02Z as scheduled. `gg045-sample3-backup.timer` fired 23:50:00Z, correctly self-skipped (guard saw `artifact:` already logged) — the guard mechanism itself worked exactly as designed.
- Artifact: VPS `logs/orderbook_depth_mlb_20260719_230502.json` — ESPN gate passed (1 live game: STL @ ARI, Bot 8th), but `"results": []` — **0 of 120 open KXMLBHIT tickers matched code "STLARI"**.
- **Root-caused this session — NOT a ticker-format/matching bug.** Verified live tonight (875 open markets, 11 games live) that the away+home ticker convention (`ESPN "DET @ CHC"` → ticker `...DETCHC...`) is correct and matches exactly what `vps_gg045_sample3.py` computed for STL@ARI. The real cause: **individual KXMLBHIT batter markets close progressively as each player completes their plate appearances for the game, not at final out.** By Bot 8th, STL@ARI was the *only* live game and most/all of its own player markets had already closed (each batter finished their at-bats) — so `status="open"` correctly returned 0 markets for that ticker code. The 120 open markets that *did* exist at 23:05Z all belonged to other (not-yet-started or next-day) games.
- **This is a real structural finding for the GG-045 memo, not a null/bug result:** a genuine "late innings, single lone live game" sample is structurally hard to get via `status="open"` — coverage collapses near a game's end. Future attempts at a "late innings" sample should target a game still active with *other* concurrently-live games (so `status=open` still returns markets for still-active batters), not the tail end of the night's last game.

**Opportunity identified, NOT yet acted on:** at 2026-07-21T00:17 UTC (2026-07-20 evening ET) this session found **11 MLB games concurrently live** (MIN@CLE Top6, LAD@PHI Top4, PIT@NYY Bot3, TB@TOR Top5, BAL@BOS Top5, SD@ATL Bot5, NYM@MIL Top3, SF@KC Mid3, CHW@TEX Top1, DET@CHC Delayed/Top1, MIA@HOU Bot1) with 875 open KXMLBHIT markets — a stronger overlap window than sample 2's (10 games/521 markets). This is a good candidate to supersede the failed sample 3, but **the pull was NOT executed this session** — ran out of context budget immediately after diagnosis. Do NOT assume this window is still open when resuming; re-check ESPN scoreboard state fresh (per D2) before pulling — by the time this is picked up the games above will likely have progressed or ended (they were early-to-mid innings, not lockable).

**Next session should:**
1. Re-check ESPN scoreboard fresh; if any concurrent live window exists (today's slate or a future one), run the proven sample-2-style targeted per-ticker pull (see "Sample 2/3 procedure" above) — do NOT reuse `vps_gg045_sample3.py`'s inline matching as-is without accounting for the progressive-closure finding above (it's not buggy, but a single-lone-game-late-innings target will keep returning near-empty).
2. Label the resulting artifact honestly (e.g. `sample3_evening_overlap`, not `sample3_late_innings`, if it ends up being an overlap-style pull rather than true late-innings) — this addendum + the empty 23:05Z artifact should both be referenced in the memo as documented, explained findings, not silently dropped.
3. Once a valid sample 3 (or equivalent) exists: proceed through the original write-back checklist above unchanged (copy artifacts to main tree logs/, run analysis, finalize memo, GG-045 entry + DECISION_LOG update — re-read fresh first per Hard Rule 10 — resolve TBD claim to a real T-number checking current collisions, flag APR-0029 D1 as still-open operator decision, commit path-scoped, push, PR to main, session-end, retire worktree).
4. Nothing has been written to any shared nav file yet this addendum session (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, TODO_NEXT.md, SESSION_CLAIMS.md untouched) — this file (worktree-local) is the only artifact changed. Session claim was NOT taken this turn (ran out of budget before Step 0's `claim_session.sh`) — take it fresh at resume, checking `SESSION_CLAIMS.md` for anything landed since 2026-07-21T00:05:14Z (T-392, the last row seen this session).
