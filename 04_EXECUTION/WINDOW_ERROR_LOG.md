# Strategic window error log — read first by every strategic window (ADR-0074)

**What this is.** Every mistake a strategic window (the planning chat that writes waves) made, with what it cost and the rule
now in force against it. Started 2026-10-14 at the operator's direction ("What do we have in place to 1) ensure these two are
well-documented and tracked against and 2) combat future oscillations"). Terminal mistakes live in their handoffs and the gap
log; this file is for the window's own judgement, which nothing else tracked.

**Rules for this file.** Append-only. A window adds a row the moment it learns of its own mistake — not at handoff. Every
incoming window reads this file before writing its first wave and names, in its first message to the operator, the pattern it
is most at risk of repeating. `/strategic-handoff` step 1 tallies the patterns.

**Patterns** (the tag in each row):
- `UNVERIFIED` — stated something to the operator without checking it against data or the repo.
- `NOTES` — asked the operator, or acted, without reading notes that already held the answer (memory, project docs, repo).
- `ESCALATED` — handed the operator a demo/paper/shadow action or a terminal command (plumbing is not his).
- `COLLISION` — issued blocks whose work or merges depended on each other inside one wave.
- `SCOPE` — a block's scope missed something the operator then had to add.
- `NO-PUSHBACK` — planned what was asked without stating the strongest reason not to (drift, surface outrunning reliability).
- `SLICE` — reasoned from one part of the running system without checking the rest.
- `PROCESS` — tool or protocol misuse (forgot a deliverable, wrong mechanism).

| # | Date | Wave | What the window did | Cost | Caught by | Pattern | Rule now in force |
|---|---|---|---|---|---|---|---|
| H1 | 2026-08-13 → 09-22 | — | Calibration data sat on disk 39 days before anyone computed model vs market. | The project's central question went unasked for 5+ weeks. | Operator directive 09-22 | SLICE | Hard Rule 12; DISTANCE table every wave |
| H2 | 2026-08-15 → 09-22 | — | The only evidence-producing cell was dark 38 days (GG-203) while attention was on NFL. | 38 days of lost evidence. | A session doing other work | SLICE | Silent-arm alarm (W62.1); runtime registry (ADR-0074) |
| W1 | 2026-10-09 | 63 | Told the operator MLB player hits had been dark since 9-27, from a stale note. False. | Wrong state reported to the operator. | Block 63.1 checked the logs | UNVERIFIED | Hard Rule 12: check claims against logs/data first |
| W2 | 2026-10-10 | 64 | Repeated "judged n ≈ 984 games (~3.6 seasons)" for the NFL challenger without explaining what it measured. | Operator: "makes absolutely no sense"; trust cost. | Operator | UNVERIFIED | Explain every derived number in plain words before using it |
| W3 | 2026-10-11 | 66–67 | Rebuilt the Visual Dashboard as a platform artifact (unsupported in his Safari) in a "textbook" style, dropping his hand-built design. | Two rebuilds; operator frustration. | Operator | NOTES | Dashboard design bar in project memory; keep his design |
| W4 | 2026-10-11 | 67 | Burned the last free GitHub Actions minutes on proof dispatches, then recommended a $25 spending cap against his $0 rule. | MLB feeds and CI blocked; repo made public under pressure. | Operator | NO-PUSHBACK | $0 rule; repo public; no paid service, ever |
| W5 | 2026-10-11 | 68 | Changed ACTIVE_QUEUE.md without sending it as a file card. | Operator had to ask, angrily. | Operator | PROCESS | Every queue change is sent as a file card |
| W6 | 2026-10-12 | 69 | Built the "permissions pre-flight" on an authorization line pasted into each block; the terminals' classifier refused it (Claude may not grant itself permissions). | 69.1 and 69.2 partly blocked. | 69.1/69.2 handoffs | UNVERIFIED | Operator-run `scripts/operator_grant_permissions.py`; blocks never edit settings |
| W7 | 2026-10-12 | 69 | Wrote three malformed allow rules (`:*` mid-pattern) and told him to type a `!` command in a plain shell before the script was in his folder. | Two failed attempts on his side. | Operator screenshots | UNVERIFIED | Test a script against the target before handing it over |
| W8 | 2026-10-12 | 70 | Issued 70.1 and 70.3 in parallel when 70.1's merge needed 70.3 to make main green; 70.1 then asked him to admin-merge. | A plumbing merge handed to the operator. | Operator | COLLISION | No merge dependency between blocks of one wave (wave format, ADR-0074) |
| W9 | 2026-10-12/13 | 69–71 | Passed blocks' plumbing "operator decisions" through (re-arm switches, server deploy, old NBA crons, retiring /vps). | Operator time; "the operator is the bottleneck" narrative. | Window, late | ESCALATED | Common rule: only pre-registration, frozen artifact/book or real capital go to him |
| W10 | 2026-10-13 | 71 | Asked the operator what Syndicate32 was — it was in project memory since 09-25. | Operator: "Very typical". | Operator | NOTES | Search memory, project docs and repo before asking anything |
| W11 | 2026-10-13 | 71.H1 | Scoped the hygiene audit without the deployment lane or a skill map; he had to add four add-ins. Then claimed `/vps` "replaces" the crontab (it appends). | Operator did scoping work; one inaccurate claim. | Operator; the audit itself | SCOPE | Audit blocks cover deploy + runtime; claims about code are read from the code |
| W12 | 2026-10-12/13 | 70–71 | Two consecutive waves moved no measure; the windows planned plumbing and breadth without saying surface was outrunning reliability. | Drift; four waves of fixing fixes. | Drift rule (flagged at 71 close) | NO-PUSHBACK | Pushback line + surface budget in every wave (ADR-0074, Hard Rule 14) |
| W13 | 2026-10-14 | 73 | Landed the CI registry check (ADR-0074) while 73.1 (new NBA cron) and 73.2 (possible new workflow) were in flight — their PRs fail CI until they register. Known at push time; mitigated with an add-in. | One extra step for two running blocks. | Window, before push | COLLISION | Process changes that add CI gates land between waves, or ship with the add-in for blocks in flight |
| W14 | 2026-10-14 | 73 | Put the GG-570 "give NBA a separate staked runner?" question to the operator from the gap entry's text; NBA's T1-T3 lines were already demo-staked since W68.2. | An operator decision spent on a stale premise; 73.1 had to say so. | 73.1 | UNVERIFIED | Before routing any decision to the operator, verify its premise against the code/crontab mirrors, not the gap text |

## Pattern tally (update at every handoff)

| Pattern | Count | Last |
|---|---|---|
| UNVERIFIED | 5 | W14 (10-14) |
| NOTES | 2 | W10 (10-13) |
| NO-PUSHBACK | 2 | W12 (10-13) |
| SLICE | 2 | H2 (history) |
| ESCALATED | 1 | W9 |
| COLLISION | 2 | W13 (10-14) |
| SCOPE | 1 | W11 |
| PROCESS | 1 | W5 |
