# Active queue — the only prompt file to read

> **RULE: this file contains ONLY blocks that are currently firing.** Closed prompts move verbatim
> to `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md` BEFORE the queue rotates. Wave 48 is archived there.

**Verified against:** `origin/main = 7e808933` (2026-10-03 02:25 UTC, cloud block 50.1). *Facts below marked "not re-verified" could not be checked from a cloud session (no VPS).*

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | **GG-429** · **T-636** · **ADR-0070** (on main, PROPOSED) · **EXP-037** |
| Capital | **$0.** `kelly_fraction = 0.0` on every operating band. Demo venue only. SHADOW = evaluate and log. |
| Candles | **Validated** for archived-MLB market structure: EXP-035 Gate 2 PASSED 7/7 on KXMLBTOTAL (G7 by a floating-point margin). Part 1 stays FAILED. |
| NHL | **Flying.** Code, frozen model and cron on main/VPS. Pre-registration now **on main** (0902d326, merged unchanged by 49.3). |
| NFL + MLB postseason | **Code on main (49.1), not flying.** Shadow crons NOT armed: `scripts/arm_shadow_crons.sh` written, needs a LOCAL session (refuses 14 service-reachable files until reviewed with `--allow`). **NFL Week 5 kicks off Sunday 10-4.** |
| Dashboards | NOT LIVE fix + favicon 204 on main (49.2), proven in a real browser against fixtures only. **Not deployed.** |
| VPS | last recorded at `1e097e0`; `t4-mlb` keeps older code in memory. Not re-verified. |
| Test suite | Sandbox `pytest -q`: 3620 passed, 43 skipped (50.1). Live-network tests are opt-in via `PMBOT_NETWORK_TESTS=1` (GG-428); CI sets it. |

---

## ⬛ OPERATOR DIRECTIVE, 2026-10-02 17:03 PT — TIME-BOUNDED BLOCKS

> *"We added so many extra tasks to the windows that it was about to take over 2+ hours for each window to
> complete so I cut it short each way. I'm not letting windows run for hours on end — if there's a task that'll
> take that long, don't place it."*

> And minutes later, when this wave was first sized at ~75 minutes a block: *"Even 75 minutes is way too long —
> none of these tasks better take 75 minutes."*

**Every block is sized at about 30 minutes, hard stop at 45** — at the nearest pushed boundary, with a handoff
that names where the next session resumes. Scope is cut to fit the clock, never the reverse: one job per block,
done completely. Budget includes the one full test-suite run (~11 minutes) a block landing `src/` code needs.

**What does not belong in a window:** anything whose wall time is set by waiting rather than working — multi-hour
API back-captures at a rate cap, live samplers that must span hours, waiting for games to start or settle. Those
run unattended on the VPS (cron or a detached job, each under its own authorization) and a later block reads what
they produced. Wave 47's three overruns were all of this kind: a 1-hour fetch, a 2.5-hour sampler, and "hand-run
the slate as long as the session lasts."

---

## ⬛ WHAT 49.x FOUND

- **Everything Wave 48 stranded is on main; nothing is in the air.** NFL + MLB shadow code, the dashboard fixes and the
  NHL pre-registration landed from cloud. Arming and deploying need the VPS — a local session.
- **Process holes, closed by 50.1:** `claim_session.sh` landed 7 untested NFL commits on main by pushing HEAD (GG-419 —
  now refuses unless HEAD has nothing beyond origin/main); pyarrow / nba_api undeclared (GG-427 — declared); live-network
  tests made the sandbox suite red (GG-428 — `network` marker, opt-in); `scripts/lib/__pycache__/` un-ignored (fixed).
- **GG-400..GG-429 registered with severity from the source, not investigated** — triage owed.

---

## ⬛ FIRE NOW

| Paste | Block | Budget | One-line purpose |
|---|---|---|---|
| **1st — now, LOCAL** | **Arm + deploy** | **~30 min** | `bash scripts/arm_shadow_crons.sh` (review each refused file, `--allow <path>` per file; verify first-firing times); deploy the dashboard NOT LIVE fix, restart `pmbot-web-dashboard` only, re-run `browser_check_dashboard.py` + `browser_check_tunnel_drop.py` against the RUNNING process, verify `/api/data` `process.sha`. |
| 2nd | **GG-400..429 triage** | ~30 min | Read each, confirm or correct severity, close duplicates. No fixes in-block (Hard Rule 11). |

**Arm + deploy first:** NFL Week 5 T1 windows are open now; every hour unarmed is rows that will never exist.

---

## Read this first (standing)

- **Three blocks per wave. Not four.** Operator directive 2026-09-15.
- **Every block: ~30 minutes, hard stop at 45.** Operator directives 2026-10-02 17:03 and 17:09. One job per block, done completely. Waiting is not work: long fetches, samplers and slate-watching go to the VPS, not the window.
- **Deliverable 0 in every block: land any un-landed predecessor and confirm your base.**
- **Claim IDs at run time and re-verify after ANY release or retry** (GG-322). Claim real ranges, never "TBD".
- **A premise written in a block is a claim to verify, not a fact.** Including every number in this file.
- **Never bypass, disable, or work around a permission control.** Record the exact command and refusal text, then hand back.
- **Pre-register before scoring.** Frozen pre-registrations stay frozen. No scoring before a cell's judged n; between looks, counts only.
- **SHADOW means evaluate and log.** No order, position, paper fill, stake or `kelly_fraction` change.
- **A merge is a deployment here.** Production updates by `git pull` in `/opt/prediction-market-bot`. Before any pull: paste `HEAD..origin/main` on the VPS and confirm every runtime file reachable from `t4-mlb` or a cron job is additive and covered by the green suite. Never restart `t4-mlb`.
- **Paper and shadow work is plumbing** (operator's standing framing): landing green, tested shadow code to main needs no further go-ahead. Real capital is his.
- **The Live Terminal and the project view move with the bot.** Any block that adds a cell, ledger, data source or verdict makes it visible in the same block.
- **No background process outlives its session unrecorded.** And per the directive above: none should need to.
- Register-and-stop on any gap outside scope (Hard Rule 11) — registration goes to 48.2 via your results summary.

---

## Sequencing track

| Wave | Status | Outcome |
|---|---|---|
| 10-47 | CLOSED | see `ACTIVE_QUEUE_ARCHIVE.md` |
| **48** | **CLOSED — all three cut short** | Nothing landed from 48.1; 48.2 landed `vps_job.py` + record; 48.3's fixes on a branch. |
| **49.1-49.3** | **CLOSED (cloud)** | NFL + MLB shadow, dashboard fixes, NHL pre-registration landed on main; GG-400..429 registered; nothing deployed. |
| **50.1** | **CLOSED on its branch (cloud)** | GG-419, GG-427, GG-428 and the `.gitignore` hole fixed; queue rotated. |

---

## THE ARC — Waves 48 through 51

| Wave | The question it answers |
|---|---|
| **48** | *Are all 33 pre-game cells logging unattended, and can the operator see them?* NFL + MLB armed before Sunday; long jobs moved to the VPS; dashboards proven in a browser. |
| **49** | **NHL hardening** (team codes, T1 abstentions, contract switch, pre-registration landed). **NBA (opens 10-20)** — split into ~30-minute blocks. **The board survey** on the completed history store (now a read, not a fetch). Backtests of NFL/NHL cells against validated market history. EXP-034 verdict if its job ran. |
| **50** | First looks as cells reach judged n (NFL first: 60 games ≈ late October). A **flat-stake paper ADR** for SHADOW cells — yours to accept — so evidence becomes countable paper P&L. |
| **51** | In-play arms only where C5 / ADR-0068 shows speed is measured. Sizing only for a cell that cleared its gate and its capacity question. |

What should reorder this, and what should stop it:

- **A shadow path that reaches an order, position or sizing function** stops everything shadow until fixed.
- **A dashboard that shows a number it did not read live** is a defect of the same severity — it is the operator's instrument.
- **Per cell, the pre-registered rules decide.** RULED_OUT at judged n is a completed cell.
- **If every cell in a sport is RULED_OUT at its judged n**, the next question for that sport is the information set, not more cells.
- **Board-survey stop condition — pre-registered in Wave 45, carried unchanged:** if the survey finds nothing
  CANDIDATE-PENDING-CAPACITY and no surviving multi-leg cell, Kalshi is efficient net of cost and fee at the cadence
  measured, and the off-Kalshi question opens alongside the cell work.

---

## Queued next — not yet fired

**NHL hardening** (Wave 49): verify Kalshi team codes for all 32 teams, investigate T1 abstentions, switch to `contract.py`, land the pre-registration branch unchanged. **NBA game markets** (Wave 49). **The board survey** (after the history store completes). **MLB winter disposition**
after the World Series. **Step 4 season-awareness** (GG-343..345). **PIPE-08 406s.** **T4M-PROJ and T3 disposition**
(both MISFILED). **The branch estate** (33+ unmerged). **9 aged T4 and 17 aged T1/T2 open paper positions** and the T4
resolved ledger unwritten since 09-28 (47.2's findings — 48.2 registers them). **Test-suite runtime** (10m41s full).

---

## Needs your decision

**Nothing in Wave 48 is gated on a line here.** Three deliverables *expand* if you write one.

> **AUTHORIZATION — SHADOW-EVALUATION CRON JOBS (operator, 2026-10-02 15:22 PT: "Yes permission granted").**
> Blocks may install the cron entries that run their NFL, NHL and MLB **shadow-evaluation cron jobs** for the
> T1/T2/T3 pre-game bands, plus the settlement join for those shadow ledgers. Allowed: read-only market and sports
> data reads within each block's rate cap, model evaluation, appends to shadow ledgers. Not covered: any order,
> position, fill, stake or `kelly_fraction` change; any EXISTING cron line, capture window or service; the
> settlement/depth capture writers, the NFL pre-kickoff capture and the price archiver. Dry-run first; commit the
> lines in the same commit that is installed; verify from the live crontab and the first scheduled firing.

> **AUTHORIZATION — LIVE TERMINAL DEPLOY AND RESTART (operator, 2026-10-02 15:44 PT: *"I need this dashboard updated
> as the bot continues to get updated"*).** Standing. Any block that changes the dashboards may deploy and restart
> **`pmbot-web-dashboard` only**: suite green; VPS `HEAD..origin/main` pasted and runtime files reachable from `t4-mlb`
> or a cron job confirmed additive before pulling; restart; verify `/`, `/api/data` and `process.sha` from the
> RUNNING process. Not covered: restarting `t4-mlb` or any other service, any cron change, any order or sizing.

| Item | Plain English | What it costs while it waits |
|---|---|---|
| **NEW — detached read-only VPS jobs** | Long *read-only* work (the history back-capture, EXP-034's sampler) runs unattended on the VPS through `scripts/vps_job.py` instead of in a terminal: no cron, no orders, rate-capped, logged, stoppable. A line naming *detached read-only VPS jobs* lets 48.2 launch them. | The board survey and NFL/NHL market backtests stay blocked on a store no window can finish inside two hours. |
| **NEW — T1 MLB postseason flag** | Adds `--include-postseason` to the **existing** T1 MLB cron line so the player-hits run sees playoff games (0 players matched since 9-27). An edit to an existing cron line, so the shadow authorization does not cover it. | T1 stays blind for the rest of the playoffs. |
| **NEW — EXP-034 (non-sports control arm)** | Its corrected run needs a ≥2.5-hour live sampler. Run it as a VPS job, or **park** it while the sports cells fly? Window's recommendation: **park** — Gate 2 already validated candles, and the sports cells are the priority. | Nothing urgent either way. |
| **ADR-0070** | Model-class deviation from ADR-0004 (probit-Platt for NFL/MLB; NHL's bivariate Poisson is the same question). Shadow-only today; acceptance needed before any of these models touches a paper stake. | Nothing until Wave 50's flat-stake question. |
| **Who restarted t4-mlb?** | Unattributed manual restarts on 10-1 and 10-2 (GG-347/348). If it was you or a session you ran, that closes it. | An unexplained actor on the one live service. |
| **MLB winter** | After the World Series: stand T1/T4 MLB down, or let them idle all winter? | Daily false alarms in Step 4 until spring. |
| **Settlement + depth capture schedules · Polymarket KYC · odds feed · provenance allowlist · APR-0035 · ADR-0068 · ADR-0067 · 39.3 triage · ADR-0063/0064/0065/0066 · APR-0034/0036** | Unchanged. | — |

**Status after 49.x** (one line per item above; no item decided):
- *Detached read-only VPS jobs* — `scripts/vps_job.py` landed (b11bf62, 48.2); still no authorization line; nothing launched.
- *T1 MLB postseason flag* — still unauthorized; not applied; T1 still blind to playoff games (not re-verified from cloud).
- *EXP-034* — neither run nor parked.
- *ADR-0070* — landed on main as PROPOSED (49.x); not accepted.
- *Who restarted t4-mlb?* — still unattributed; not investigated (cloud has no VPS access).
- *MLB winter* — unchanged; World Series not yet over.
- *Settlement + depth capture schedules … APR-0034/0036* — unchanged.

---

## DO NOT — standing

- **Never bypass, disable, or work around a permission control.** Record the exact command and the exact refusal text, then hand back. Absolute; no operator approval in a block overrides it — an approval authorizes a CHANGE, never a bypass.
- **Submit no order against the production Kalshi account or with real funds. Demo only, always.**
- Touch sizing or any `kelly_fraction` without an ADR, including T1.
- Promote `assert_ledger_invariants.py` to `--strict`.
- Repair or backfill a DERIVED field without establishing provenance first (GG-228). Re-capturing a raw source from its own upstream is a different act — say which one you are doing.
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- Recommend against a sport, band or market family on one finding — and do not assume the rest of the board behaves like the cells that happened to be measurable.
- Modify or re-time an existing price-capture window. Additive sibling writers only.
- Rotate, truncate or clear a VPS log or journal.
- Restart a production service without a scoped, written authorization.
- Add a cron entry without explicit operator authorization, including for read-only capture writers.
- Pre-assign T-/GG-/ADR- numbers. Claim at run time; verify uniqueness across `git log --all`; **re-verify after any release or retry** (GG-322).
- Report a live fix RESOLVED without proving the RUNNING process contains it, not the file on disk.
- Manufacture a position, a row, a cohort member, a price, a fill, or a final score.
- Assume a fill the data cannot evidence.
- Revive `exchange_index` propagation — T-558 tested and disproved it.
- Delete, truncate or rewrite a live pool file. Work on copies.
- Weaken a predicate, or widen an allowlist without citation, to raise a count.
- Modify `p_hits_gte_threshold` — 1,694 rows' provenance citation rests on its source hash.
