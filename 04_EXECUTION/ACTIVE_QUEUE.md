# Active queue — the only prompt file to read

> **RULE: prompt text here is ONLY for blocks firing now.** Closed prompts move verbatim to
> `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`; closed waves keep their ROWS in the Sequencing track below.

**Verified against:** `origin/main = 4dbd923` (2026-10-03 20:25 UTC, strategic window, via `git fetch` + GitHub API).
VPS facts are the 50.2 cleanup terminal's report, not re-verified from here.

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | **GG-432** (50.2 claimed through GG-439) · **T-637** (50.2 claimed through T-645) · **ADR-0070** (PROPOSED) · **EXP-037** |
| Capital | **$0.** `kelly_fraction = 0.0` on every operating band. Demo venue only. SHADOW = evaluate and log. |
| NFL + MLB postseason shadow | **Armed** (50.2): EXP-037 cron block installed; crontab backup `/root/crontab.bak.20261003T200240Z`; first NFL T1 firing 2026-10-04 00:05 UTC. |
| NHL | Flying in shadow (T3 rows live). Registry still says NOT_IMPLEMENTED. Never uses the confirmed goalie (GG-401). Team-code parser unverified (GG-403). |
| PR #157 (50.1 process fixes) | **Open draft, head `855a5f0`, CI green, NOT mergeable: 4 conflicts** (DECISION_LOG, PLAN, TODO_NEXT, MEMORY_BANK) plus this file and the archive once this rotation lands. |
| VPS | HEAD `eb2d1434` (50.2). `pmbot-web-dashboard` process still on `077558b`. |
| Deploy | **Every push to main that touches anything outside the 9 doc folders auto-deploys and restarts `t4-mlb` + `pmbot-web-dashboard`** (`deploy.yml`, GG-432). A push is docs-only only if EVERY file in it is under `00_ADMIN 01_SPEC 02_ARCHITECTURE_DESIGN 03_DECISIONS 04_EXECUTION 05_RESEARCH_EXPERIMENTS 07_TEST_VALIDATION_EVIDENCE 08_MODEL_RISK_GOVERNANCE 11_MEMORY_HANDOFF`. |
| Live games today (10-03 UTC) | ATL@LAD in progress; NYY@TB 22:30Z; SD@MIL 00:30Z. **Earliest code-push window: about 03:30 UTC = 8:30 PM PT.** |

---

## ⬛ OPERATOR DIRECTIVE, 2026-10-02 17:03 PT — TIME-BOUNDED BLOCKS

> *"We added so many extra tasks to the windows that it was about to take over 2+ hours for each window to
> complete so I cut it short each way. I'm not letting windows run for hours on end — if there's a task that'll
> take that long, don't place it."*

> And minutes later, when a wave was first sized at ~75 minutes a block: *"Even 75 minutes is way too long —
> none of these tasks better take 75 minutes."*

**Every block is sized at about 30 minutes, hard stop at 45** — at the nearest pushed boundary, with a handoff
that names where the next session resumes. Scope is cut to fit the clock, never the reverse: one job per block,
done completely. Budget includes the one full test-suite run (~11 minutes) a block landing `src/` code needs.

**What does not belong in a window:** anything whose wall time is set by waiting rather than working. Those run
unattended on the VPS under their own authorization, and a later block reads what they produced.

---

## ⬛ WHAT 50.2 FOUND (and what this window found checking it)

- **NFL + MLB postseason shadow crons are armed.** The 33 pre-game cells now log unattended. Nothing restarted.
- **Who restarted t4-mlb: CI.** `deploy.yml` restarts `t4-mlb` and the dashboard on every code push to main (GG-432).
  That contradicts the standing "never restart t4-mlb" rule; the policy is yours (Needs your decision, first row).
- **The dashboard's stale panel and its 26.63% drawdown are one file** (strategic window, arithmetic):
  `paper_portfolio_mlb.json`, last written 2026-08-06 00:05Z (+58d20h = the panel's "read 58d20h ago", GG-431);
  $733.75 of $1,000 = 26.63%, past the 20% permanent kill switch.
- **The two drawdowns are not the same quantity** (strategic window, code read — 51.1 verifies): the T1 runner feeds
  the kill switch *realized* loss only (`run_mlb_paper_trade.py:670-671`); the dashboard shows
  `(initial − bankroll) / initial` (`web_dashboard.py:761`, `:1498`), which also counts stake locked in ~17 positions
  open since August. So the tile may be alarming on money that is tied up, not lost — or the kill switch may have
  missed a real breach. No capital either way (kelly 0.0).
- **PR #157 is not mergeable as it stands** (GitHub: `mergeable_state = dirty`) — 50.2's report did not say so. 51.3 makes it mergeable; it lands in a later idle window.

---

## ⬛ FIRE NOW — Wave 51, three blocks

| Paste | Block | When | Budget | One-line purpose |
|---|---|---|---|---|
| **1st** | **51.1 Kill-switch truth** | now, LOCAL | ~30 min | Is the 20% kill switch tripped, should it be, and does the dashboard show what the risk engine reads? Read-only; any fix on a branch. |
| **2nd** | **51.2 NHL silent drops** | now, LOCAL | ~30 min | Verify all 32 team codes against live Kalshi tickers, fix the parser, count every abstention by reason. Branch only. |
| **3rd** | **51.3 PR #157 merge-ready** | now, LOCAL | ~30 min | Resolve #157's conflicts, CI green, pre-merge record, NHL row counts. Merges nothing. |

**No block pushes code to main** — MLB postseason games are live, and any code push restarts `t4-mlb`. Landing #157,
the NHL SHADOW flip and 51.1/51.2's branches is one short block, issued only when an idle window is actually open.

### 51.1 — Kill-switch truth

```text
WAVE 51.1 - KILL-SWITCH TRUTH (local terminal, about 30 min, hard stop 45)

You are a Claude Code session on the prediction-market-bot repo. Run the CLAUDE.md
session-start protocol first: isolated worktree via
scripts/new_session_worktree.sh "w51-killswitch-truth", then scripts/claim_session.sh
with tier STANDARD and this single deliverable. Claim IDs at run time; this prompt
pre-assigns no T-/GG- numbers.

QUESTION: The Live Terminal shows MLB T1 drawdown 26.63% against the 20% permanent
kill switch (risk.py _HARD_LIMITS max_drawdown_pct 0.20). Is the kill switch tripped,
should it have been, and does the dashboard show the quantity the risk engine reads?

PREMISES - claims to verify, not facts:
P1. The 26.63% comes from logs/paper_portfolio_mlb.json on the VPS: bankroll_usd about
    733.75, initial_bankroll_usd 1000, last_updated 2026-08-06T00:05Z, about 17 open
    positions.
P2. Two definitions are in play. run_mlb_paper_trade.py:670-671 passes the kill switch
    max(0, -total_realized_pnl) / initial (realized loss only).
    scripts/web_dashboard.py:761 and :1498 show (initial - bankroll) / initial, which also
    counts stake locked in open positions.
P3. GG-431's stale panel ("read 58d20h ago") is the same file:
    2026-08-06 00:05Z + 58d20h = 2026-10-03 20:05Z.
P4. T1 MLB kelly_fraction is 0.0 (ADR-0048); no stake is at risk either way.

DELIVERABLES - read-only on the VPS (no restart, no cron change, no file edit there):
D1. From the VPS file: total_realized_pnl, bankroll_usd, initial, count and summed stake
    of open_positions, oldest and newest open dates. Show the arithmetic for both
    drawdown definitions.
D2. From logs/paper_mlb_cron.log: the "[C4] Bankroll ... Drawdown" lines around
    2026-08-05..08-07 and the most recent one. Grep the cron log and the audit logs for
    KILL_SWITCH and risk_eval_kill_switch. Is kill-switch state persisted anywhere, and
    is it set now?
D3. Why did the file stop being written on 2026-08-06? Name the code line that decides
    whether it is written, and whether a 0-bet run (kelly 0.0) skips the write. Answer
    plainly: frozen because nothing changed, or frozen because something broke.
D4. Why are about 17 positions still open after 58 days? Read-only Kalshi check: are
    their markets settled? Settled but unresolved = a resolver gap. Register it. Do not
    resolve, close or edit any position.
D5. VERDICT, exactly one of:
    (a) tripped, and holding correctly;
    (b) not tripped and correctly not tripped (realized under 20%); dashboard metric wrong;
    (c) should have tripped and did not - register CRITICAL;
    (d) other, stated plainly.
D6. Only if the dashboard disagrees with the risk engine: on a branch, fix
    web_dashboard.py so the drawdown tile shows the realized quantity the kill switch
    reads, open stake as a separate labelled number, and a book with no write in over
    72h labelled FROZEN with its last-write date. Tests green. Push the branch.
    DO NOT MERGE: a code push to main auto-deploys and restarts t4-mlb (deploy.yml,
    GG-432) while postseason games are live. Hand the branch and SHA to the landing
    block.

OUT OF SCOPE - register and stop (Hard Rule 11): editing or resolving positions, any
kelly or limit change, any restart, any cron change.

CLOSE: results summary under 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/, GG entries,
one DECISION_LOG line for the verdict, handoff naming the branch and SHA. Pushes to
main must be docs-only: every file under the 9 paths-ignored doc folders, nothing else.
At 45 minutes stop at the nearest pushed boundary and say where the next session resumes.
```

### 51.2 — NHL silent drops

```text
WAVE 51.2 - NHL SILENT DROPS (local terminal, about 30 min, hard stop 45)

You are a Claude Code session on the prediction-market-bot repo. Run the CLAUDE.md
session-start protocol first: isolated worktree via
scripts/new_session_worktree.sh "w51-nhl-team-codes", then scripts/claim_session.sh
with tier STANDARD and this single deliverable. Claim IDs at run time.

QUESTION: Is the NHL shadow arm silently dropping markets? Close GG-403 and the
counter half of GG-405.

PREMISES - claims to verify, not facts (source: GG400_429_TRIAGE_2026-10-03.md on the
PR #157 branch):
P1. TEAM_ALIASES is empty (src/prediction_market_bot/c3_forecasting/nhl_pregame.py:193).
    Both parsers assume 3+3-letter team codes: _TICK regex at nhl_pregame.py:190 and
    len(teams) != 6 at scripts/nhl_shadow_eval.py:76. A 2-letter Kalshi code returns None
    with no log and no counter.
P2. Night-one T3 abstained on some markets (about 195 rows vs 240 expected); causes
    were never logged.
P3. Scoring takes Kalshi's own result (nhl_shadow_settle.py:24-28), so overtime and
    shootout affect only whether the model's p matches the contract, not the scored y.

DELIVERABLES:
D1. Read-only Kalshi pull of every open and recently settled KXNHLGAME, KXNHLSPREAD and
    KXNHLTOTAL ticker. Extract every team code seen. Diff against the 32 NHL
    abbreviations the NHL data side uses. Table: code, team, parses today (yes/no).
D2. Fix: populate TEAM_ALIASES from D1's evidence (cite the ticker for each alias) and
    make both parsers accept every code seen. Tests built from real tickers from D1,
    including every previously failing code.
D3. Abstention counters in nhl_shadow_eval.py: one named counter per reason (ticker
    unparsed, team unmapped, no game match, forecast None, any other return-None path),
    written to the run log or the shadow ledger's run metadata, so a dropped market is
    never silent again.
D4. Coverage boundary: rows before this fix lands are a different population from rows
    after it. Record the boundary in the EXP-036 results summary as a dated note.
    Do NOT edit the frozen pre-registration.
D5. Full suite green. Push the branch. DO NOT MERGE: a code push to main auto-deploys
    and restarts t4-mlb (deploy.yml, GG-432) while postseason games are live. Hand the
    branch and SHA to the landing block.

OUT OF SCOPE - register and stop (Hard Rule 11): the confirmed-goalie source (GG-401),
the spread cutoff (GG-404), the clustered scorer (GG-407), matinee cron hours (GG-405
first half), any cron change, any edit to the frozen model or pre-registration. If D1
shows every code already parses, say so, keep D3, and close GG-403 on the evidence.

CLOSE: results note, GG updates, handoff naming the branch and SHA. Pushes to main must
be docs-only. At 45 minutes stop at the nearest pushed boundary.
```

### 51.3 — PR #157 merge-ready

```text
WAVE 51.3 - PR 157 MERGE-READY (local terminal, about 30 min, hard stop 45)

You are a Claude Code session on the prediction-market-bot repo. Run the CLAUDE.md
session-start protocol first: isolated worktree via
scripts/new_session_worktree.sh "w51-pr157-ready", then scripts/claim_session.sh with
tier STANDARD and this single deliverable. Claim IDs at run time.

QUESTION: Make PR 157 mergeable and fully pre-checked, so landing it later is a short
mechanical run. This block merges nothing to main.

CONTEXT - claims to verify: PR 157 (head 855a5f0, draft, CI green) carries 50.1's
process fixes: GG-419 claim_session HEAD guard, GG-427 deps, GG-428 network marker,
.gitignore, and the GG-400..429 triage. GitHub reports it NOT mergeable: conflicts in
DECISION_LOG.md, PLAN.md, TODO_NEXT.md and MEMORY_BANK.md, plus ACTIVE_QUEUE.md and
ACTIVE_QUEUE_ARCHIVE.md since the Wave 51 rotation landed on main.

D1. Merge origin/main into the PR branch. Resolve:
    - ACTIVE_QUEUE.md and ACTIVE_QUEUE_ARCHIVE.md: take main's version. It already
      contains everything the PR rotated.
    - The 4 nav files: keep every entry from both sides, in date order. Delete nothing.
      Paste the resolved hunks.
    Push the PR branch. Branch pushes do not deploy.
D2. Wait for CI green on the new head. Confirm GitHub now reports it mergeable. Mark it
    ready for review.
D3. Pre-merge record in the PR description: every file in the PR diff that is reachable
    from t4-mlb or a cron job, each confirmed additive and covered by the green suite,
    and the exact Deploy behaviour expected on merge (deploy.yml restarts t4-mlb and
    pmbot-web-dashboard).
D4. Read-only, for the later NHL status flip: from the NHL shadow ledger on the VPS,
    list which NHL (MarketType x band) cells have produced valid rows, with row counts
    and first/last dates. Record it in the handoff. Change no registry status.

DO NOT: merge PR 157, push code to main, restart anything, or touch web_dashboard.py or
any NHL source file (51.1 and 51.2 own those).

CLOSE: handoff with the new PR head SHA, CI run id, mergeable state, and the D4 table.
Pushes to main must be docs-only. At 45 minutes stop at the nearest pushed boundary.
```

---

## Read this first (standing)

- **Three blocks per wave. Not four.** Operator directive 2026-09-15.
- **Every block: ~30 minutes, hard stop at 45.** One job per block, done completely. Waiting is not work.
- **Deliverable 0 in every block: confirm your base** (`git fetch`; work from current `origin/main`).
- **Claim IDs at run time and re-verify after ANY release or retry** (GG-322). Never "TBD".
- **A premise written in a block is a claim to verify, not a fact.** Including every number in this file.
- **Never bypass, disable, or work around a permission control.** Record the exact command and refusal text, then hand back.
- **Pre-register before scoring.** Frozen pre-registrations stay frozen. No scoring before a cell's judged n.
- **SHADOW means evaluate and log.** No order, position, paper fill, stake or `kelly_fraction` change.
- **A merge is a deployment here, and a code deployment restarts `t4-mlb`** (deploy.yml, GG-432). Until the operator
  decides GG-432: code reaches main only when no MLB game is live (Stats API shows none In Progress, T4 cycle log idle
  > 15 min, no first pitch within 60 min). Docs-only pushes are always fine.
- **Paper and shadow work is plumbing** (operator's standing framing). Real capital is his.
- **The Live Terminal and the project view move with the bot.** A block that adds a cell, ledger, source or verdict makes it visible.
- Register-and-stop on any gap outside scope (Hard Rule 11).

---

## Sequencing track

Legend: ✅ landed on main · ⚠️ done but NOT on main (branch / PR) · ✂️ cut short by operator · ❌ never ran · ⏳ in flight · ⬜ not started

### ⏳ WAVE 51 — RUN NOW · 3-wide · disjoint surfaces

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 51.1 | Kill-switch truth | ⚠️ done, branch not merged | Verdict (d): realized drawdown **10.60%**, not tripped; dashboard's 26.63% = 10.60% realized + 16.02% stake in 17 positions already settled on Kalshi but never resolved — if all lost, realized is 26.6% > 20% (GG-441). Dashboard fix on `6cbe62f`. GG-440..442 | Merge in the landing block |
| 51.2 | NHL silent drops: 32 team codes vs live tickers, parser fix, abstention counters (GG-403, GG-405) | ⏳ | `nhl_pregame.py`, `scripts/nhl_shadow_eval.py` (branch only) | Same |
| 51.3 | PR #157 merge-ready: resolve conflicts, CI green, pre-merge record, NHL row counts | ⏳ | PR #157 branch; nav files on that branch | Merges nothing |
| — | ~~51.3 original: land #157 + NHL SHADOW flip~~ | ❌ withdrawn | — | Needed an idle window; becomes the landing block below |

**Next, not yet issued:** landing block — merge #157, NHL cells with rows → SHADOW, merge 51.1/51.2's green branches. Issued only when no MLB game is live (earliest ~8:30 PM PT tonight).

### ✅ WAVES 49–50 — CLOSED 2026-10-03 · run inside harness sessions, not from this queue

| # | Block | Status | Outcome |
|---|---|---|---|
| 49.1–49.3 | NFL + MLB shadow code, dashboard fixes, NHL pre-registration | ✅ | On main and auto-deployed by CI (VPS `077558b1`); GG-400..429 registered; crons not armed (cloud can't reach VPS) |
| 50.1 | Process fixes + GG-400..429 triage (T-636) | ⚠️ | PR #157, draft, green but conflicted — 51.3 makes it mergeable |
| 50.2 | Cleanup (T-637) | ✅ | Shadow crons ARMED; tree synced; PR #156 closed; #157 held for live games; GG-430..432 (CI restarts t4-mlb) |

### ✂️ WAVE 48 — CLOSED 2026-10-03

| # | Block | Status | Outcome |
|---|---|---|---|
| 48.1 | Land NFL + MLB shadow (T-631) | ✂️ | Stopped early at operator request; rebased only — landed later by 49.1 |
| 48.2 | Record + VPS jobs (T-632) | ✂️ | Queue + `vps_job.py` landed; detached jobs still unauthorized |
| 48.3 | Dashboards in a real browser (T-621..630) | ⚠️→✅ | Fixes on a branch; landed by 49.2 |

### ✂️ WAVE 47 — CLOSED 2026-10-02 · all three cut at ~2h → the 30-min block rule

| # | Block | Status | Outcome |
|---|---|---|---|
| 47.1 | Candles Gate 2 + Live Terminal v2 (T-615) | ✂️ | **Gate 2 PASSED 7/7** on KXMLBTOTAL; Live Terminal v2 + `/project` deployed; GG-340..356 |
| 47.2 | NFL + MLB postseason shadow (T-608 / EXP-037) | ✂️ | 24 cells built + pre-registered, ADR-0070 PROPOSED; landed later by 49.1 |
| 47.3 | NHL arm (T-607 / EXP-036) | ✅ | **First new arm flying** — model frozen, cron installed, first T3 rows |

### ✅ WAVE 46 — CLOSED 2026-10-02

| # | Block | Status | Outcome |
|---|---|---|---|
| 46.1 | Why candles failed (T-605) | ✅ | Matching rule + sparse candles; Gate 2 pre-registered |
| 46.2 | EXP-034 control arm | ⚠️ | Gate FAIL as run (runner lookback); numbers VOID; branch not merged |
| 46.3 | Shared-tree repair (T-606) | ✅ | Stale lock removed, tree synced, ADR-0067 docs landed |

### ⚠️ WAVE 45 — CLOSED 2026-10-02

| # | Block | Status | Outcome |
|---|---|---|---|
| 45.1 | Candle reconstruction Part 1 (T-604 / EXP-035) | ✅ | Gate FAILED → candle numbers VOID; GG-329..333 |
| 45.2 | EXP-034 setup | ⚠️ | Tolerance frozen; comparison not run |
| 45.3 | Record + dashboard page | ⚠️ | Queue landed; dashboard page running; tree sync blocked |

Waves 10–44: see `ACTIVE_QUEUE_ARCHIVE.md`.

---

## THE ARC — renumbered (49-50 went to landing and cleanup)

| Wave | The question it answers |
|---|---|
| **51** | *Is what the operator sees true, and is everything built actually landed?* Kill switch vs dashboard; NHL silent drops; #157 made mergeable. |
| **52** | **NHL scoring readiness** — confirmed-goalie source at T3 (GG-401), pre-registered spread cutoff (GG-404), clustered scorer (GG-407), matinee coverage (GG-405). **NBA (opens 10-20)** in ~30-minute blocks. Merge whatever 51 left on branches. |
| **53** | First looks as cells reach judged n (NFL first: 60 games ≈ late October). A **flat-stake paper ADR** for SHADOW cells — yours to accept. |
| **later** | In-play arms only where C5 / ADR-0068 shows speed is measured. Sizing only for a cell that cleared its gate and its capacity question. |

What should reorder this, and what should stop it:

- **A shadow path that reaches an order, position or sizing function** stops everything shadow until fixed.
- **A dashboard that shows a number it did not read live, or a number that is not what its label says** is a defect of the same severity.
- **A kill switch that should have fired and did not** (51.1 verdict c) stops everything until understood.
- **Per cell, the pre-registered rules decide.** RULED_OUT at judged n is a completed cell.
- **Board-survey stop condition — pre-registered in Wave 45, carried unchanged.**

---

## Queued next — not yet fired

**Landing block** — issued only when no MLB game is live (earliest about 8:30 PM PT tonight): merge #157, flip NHL's cells with rows to SHADOW, merge 51.1/51.2's green branches; idle probe and Deploy checks on each. **NHL scoring readiness** (GG-401, GG-404, GG-405, GG-407) — before any NHL score is read. **NBA game markets.** **The board
survey** (after the history store completes — needs the detached-VPS-jobs line). **MLB winter disposition** after the World
Series. **Step 4 season-awareness** (GG-343..345). **PIPE-08 406s.** **T4M-PROJ and T3 disposition** (both MISFILED). **The
branch estate** (33+ unmerged). **Aged open paper positions** (9 T4, ~17 T1 — 51.1 reports on the T1 set). **Test-suite runtime.**

---

## Needs your decision

**Nothing in Wave 51 is gated on a line here.**

> **AUTHORIZATION — SHADOW-EVALUATION CRON JOBS (operator, 2026-10-02 15:22 PT: "Yes permission granted").** Unchanged;
> used by 50.2. Not covered: any order, position, fill, stake or `kelly_fraction` change; any EXISTING cron line.

> **AUTHORIZATION — LIVE TERMINAL DEPLOY AND RESTART (operator, 2026-10-02 15:44 PT).** Standing. Covers
> `pmbot-web-dashboard` only. Note: under today's `deploy.yml`, any code merge also restarts `t4-mlb` — see GG-432 below.

| Item | Plain English | What it costs while it waits |
|---|---|---|
| **NEW — GG-432: CI restarts t4-mlb on every code push** | Today every merge that touches code restarts the live T4 process, including mid-game. Options: (a) **window's recommendation** — deploy pulls code on every push but skips the `t4-mlb` restart while an MLB game is live (it restarts at the next idle window); (b) never auto-restart `t4-mlb`, restart only by hand; (c) keep as is. | Every code landing waits for an idle window by hand, as Wave 51 does. |
| **Detached read-only VPS jobs** | Long read-only work runs unattended on the VPS through `scripts/vps_job.py`. A line naming *detached read-only VPS jobs* unlocks it. | The board survey and NFL/NHL market backtests stay blocked. |
| **T1 MLB postseason flag** | Adds `--include-postseason` to the existing T1 MLB cron line. Edits an existing line, so the shadow authorization does not cover it. | T1 player-hits stays blind for the rest of the playoffs. |
| **EXP-034** | Run its ≥2.5-hour sampler as a VPS job, or **park** it (window's recommendation). | Nothing urgent. |
| **ADR-0070** | Model-class deviation for NFL/MLB shadow models. **As written it does not cover NHL** (GG-400): widen it while still PROPOSED, or accept that GG-400 stays open. | Nothing until the flat-stake question. |
| **GG-347, remaining half** | The SSH poller from 73.231.159.158 — yours? | An unexplained actor on the VPS. |
| **MLB winter** | After the World Series: stand T1/T4 MLB down, or idle all winter? | Daily false alarms in Step 4 until spring. |
| **Settlement + depth capture schedules · Polymarket KYC · odds feed · provenance allowlist · APR-0035 · ADR-0068 · ADR-0067 · 39.3 triage · ADR-0063/0064/0065/0066 · APR-0034/0036** | Unchanged. | — |

---

## DO NOT — standing

- **Never bypass, disable, or work around a permission control.** Record the exact command and the exact refusal text, then hand back. An approval authorizes a CHANGE, never a bypass.
- **Submit no order against the production Kalshi account or with real funds. Demo only, always.**
- Touch sizing or any `kelly_fraction` without an ADR, including T1.
- Push code to main while an MLB game is live (until GG-432 is decided).
- Promote `assert_ledger_invariants.py` to `--strict`.
- Repair or backfill a DERIVED field without establishing provenance first (GG-228).
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- Recommend against a sport, band or market family on one finding.
- Modify or re-time an existing price-capture window. Additive sibling writers only.
- Rotate, truncate or clear a VPS log or journal.
- Restart a production service without a scoped, written authorization. Do not hand-pull on the VPS.
- Add or edit a cron entry without explicit operator authorization.
- Pre-assign T-/GG-/ADR- numbers. Claim at run time; verify uniqueness across `git log --all`.
- Report a live fix RESOLVED without proving the RUNNING process contains it.
- Manufacture a position, a row, a cohort member, a price, a fill, or a final score.
- Delete, truncate or rewrite a live pool file. Work on copies.
- Weaken a predicate, or widen an allowlist without citation, to raise a count.
- Modify `p_hits_gte_threshold` — 1,694 rows' provenance citation rests on its source hash.
