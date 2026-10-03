# Active queue — the only prompt file to read

> **RULE: this file contains ONLY blocks that are currently firing.** Closed prompts move verbatim
> to `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md` BEFORE the queue rotates. Waves 48 through 50 are archived there.

**Verified against:** `origin/main = 6a896c6` (2026-10-03 20:15 UTC, strategic window, via `git fetch` + GitHub API).
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
- **PR #157 is not mergeable as it stands** (GitHub: `mergeable_state = dirty`) — 50.2's report did not say so. 51.3 resolves it.

---

## ⬛ FIRE NOW — Wave 51, three blocks

| Paste | Block | When | Budget | One-line purpose |
|---|---|---|---|---|
| **1st** | **51.1 Kill-switch truth** | now, LOCAL | ~30 min | Is the 20% kill switch tripped, should it be, and does the dashboard show what the risk engine reads? Read-only; any fix on a branch. |
| **2nd** | **51.2 NHL silent drops** | now, LOCAL | ~30 min | Verify all 32 team codes against live Kalshi tickers, fix the parser, count every abstention by reason. Branch only. |
| **3rd** | **51.3 Land #157 + NHL SHADOW** | **at or after 8:30 PM PT (03:30 UTC)**, LOCAL | ~30 min | Make #157 mergeable now; merge it and flip NHL's live cells to SHADOW only once no game is live. |

**51.1 and 51.2 push no code to main** — MLB postseason games are live, and any code push restarts `t4-mlb`.
51.3 carries its own idle probe: pasted early, it does the conflict resolution and stops cleanly before merging.

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
    GG-432) while postseason games are live. Hand the branch and SHA to 51.3 or the
    next wave.

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
    branch and SHA to 51.3 or the next wave.

OUT OF SCOPE - register and stop (Hard Rule 11): the confirmed-goalie source (GG-401),
the spread cutoff (GG-404), the clustered scorer (GG-407), matinee cron hours (GG-405
first half), any cron change, any edit to the frozen model or pre-registration. If D1
shows every code already parses, say so, keep D3, and close GG-403 on the evidence.

CLOSE: results note, GG updates, handoff naming the branch and SHA. Pushes to main must
be docs-only. At 45 minutes stop at the nearest pushed boundary.
```

### 51.3 — Land PR #157 + NHL SHADOW flip

```text
WAVE 51.3 - LAND PR 157 + NHL SHADOW FLIP (local terminal, about 30 min, hard stop 45)
PASTE AT OR AFTER 8:30 PM PT (03:30 UTC). If pasted earlier, do D1-D2 and stop at D3.

You are a Claude Code session on the prediction-market-bot repo. Run the CLAUDE.md
session-start protocol first: isolated worktree via
scripts/new_session_worktree.sh "w51-land-157", then scripts/claim_session.sh with tier
STANDARD and this single deliverable. Claim IDs at run time.

CONTEXT: PR 157 (head 855a5f0, draft, CI green) carries 50.1's process fixes: GG-419
claim_session HEAD guard, GG-427 deps, GG-428 network marker, .gitignore, and the
GG-400..429 triage. GitHub reports it NOT mergeable: conflicts in DECISION_LOG.md,
PLAN.md, TODO_NEXT.md, MEMORY_BANK.md, plus ACTIVE_QUEUE.md and
ACTIVE_QUEUE_ARCHIVE.md since the Wave 51 rotation landed. A merge to main
auto-deploys and restarts t4-mlb and pmbot-web-dashboard (deploy.yml). Merging only
when no game is live is the plan the operator dispatched with 50.2.

D1. Merge origin/main into the PR branch. Resolve:
    - ACTIVE_QUEUE.md and ACTIVE_QUEUE_ARCHIVE.md: take main's version. It already
      contains everything the PR rotated.
    - The 4 nav files: keep every entry from both sides, in date order. Delete nothing.
      Paste the resolved hunks.
    Push the PR branch. Branch pushes do not deploy.
D2. Wait for CI green on the new head. Mark the PR ready for review.
D3. IDLE PROBE - all three must hold; paste the evidence:
    (i)   MLB Stats API schedule for today and tomorrow UTC shows no game In Progress;
    (ii)  the last row of logs/t4_mlb_cycle_log.jsonl on the VPS is more than 15 minutes
          old;
    (iii) no MLB game starts within the next 60 minutes.
    If any fails: stop here. Handoff says "PR 157 ready, merge at next idle window".
    Merge nothing.
D4. Merge PR 157 with a merge commit. Watch the Deploy run to completion. Verify on the
    VPS: HEAD equals the merge SHA, t4-mlb and pmbot-web-dashboard active with NRestarts
    sane, and the dashboard /api/data process.sha equals the merge SHA. If Deploy fails,
    stop and report. Do not hand-pull on the VPS.
D5. NHL SHADOW flip. From the NHL shadow ledger on the VPS, list which NHL
    (MarketType x band) cells have produced valid rows. Expected: at least the three T3
    cells - verify, do not assume. Promote exactly those cells NOT_IMPLEMENTED to SHADOW
    via promote_cell_status (market_type_registry.py:799), with notes citing the row
    counts and dates. Cells with no rows stay as they are. Tests green, push to main
    (this is a second deploy - re-run the D3 probe first, then the D4 checks), and
    confirm the Live Terminal shows the new statuses from the RUNNING process.
STRETCH, only if under 35 minutes and the branch handoff says green: merge 51.1's
dashboard branch and/or 51.2's NHL branch the same way (probe, merge, D4 checks, one at
a time). Otherwise leave them for the next wave.

OUT OF SCOPE - register and stop: any change to deploy.yml (operator decision GG-432),
any cron change, any kelly or sizing change, any status beyond SHADOW.

CLOSE: handoff with each merge SHA, each Deploy run id, VPS HEAD, and the cells flipped.
At 45 minutes stop at the nearest pushed boundary.
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

| Wave | Status | Outcome |
|---|---|---|
| 10-48 | CLOSED | see `ACTIVE_QUEUE_ARCHIVE.md` |
| **49-50** | **CLOSED** | Run inside harness sessions, not from this queue: NFL + MLB shadow code, dashboard fixes and the NHL pre-registration on main (49.x); process fixes on PR #157 (50.1); crons armed, tree synced, GG-430..432 (50.2). |
| **51** | **FIRING** | 51.1 kill-switch truth · 51.2 NHL silent drops · 51.3 land #157 + NHL SHADOW (after 8:30 PM PT). |

---

## THE ARC — renumbered (49-50 went to landing and cleanup)

| Wave | The question it answers |
|---|---|
| **51** | *Is what the operator sees true, and is everything built actually landed?* Kill switch vs dashboard; NHL silent drops; #157 landed; NHL labelled SHADOW. |
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

**NHL scoring readiness** (GG-401, GG-404, GG-405, GG-407) — before any NHL score is read. **NBA game markets.** **The board
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
