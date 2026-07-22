# Runbook: Deploy to VPS — Dirty-Tree Guard Failures (GG-073/GG-102/GG-104/GG-117/GG-130)

**Purpose:** Diagnose and resolve `.github/workflows/deploy.yml` "deploy" job failures caused by the pre-pull dirty-tree guard, and explain the GG-130 (2026-07-22) structural fix that should make this failure class rare going forward.
**Owner (role):** Infrastructure Operator (IO)
**Last reviewed:** 2026-07-22
**Next review:** If the `deploy` job fails again for a reason not covered here, or if `deploy/cron.conf` adds a scheduled job that writes into a tracked path outside `exp_output/`, `data/`, `logs/`, `models/`
**Staleness triggers:** `deploy.yml`'s Deploy step changes; a new cron job is added that writes to a git-tracked path; `REGEN_ROOTS` in the guard needs to grow
**Upstream links:** `.github/workflows/deploy.yml`, `deploy/cron.conf`, `03_DECISIONS/GOVERNANCE_GAP_LOG.md` (GG-073, GG-102, GG-104, GG-117, GG-130)
**Downstream links:** `10_INFRA_OPERATIONS/INCIDENTS_POSTMORTEMS/`
**Decision references:** T-171 (original dirty-tree guard), GG-130 (this runbook's fix)
**Confidence:** 7/10 — the fix is verified against synthetic test cases (see GG-130 entry) but not yet observed against a real production failure, since this runbook was written from a Cowork session with no VPS/GitHub Actions access to confirm live

---

## Read this first: what actually broke, and what didn't

The "Deploy to VPS" workflow has two jobs: `approval-path-tests` (a fast pytest gate, GG-087/GG-077 property suite + golden-replay) and `deploy` (SSH into the VPS, `git pull --ff-only`, restart services, verify). **The vast majority of `deploy` job failures since this pipeline went live (2026-06-15) have been the same root cause, not a new one each time:** a scheduled job on the VPS (see `deploy/cron.conf`) writes new content into a file that is *also* tracked in git. The next `git status --porcelain` the deploy guard runs sees that file as locally modified, and — before GG-130 — hard-failed the entire deploy to avoid a `git pull --ff-only` silently clobbering it.

This has happened at least four times with four different specific files:

| Gap | File that tripped the guard | Resolved by |
|---|---|---|
| GG-073 | `data/data_contracts_state.json` + others (100% failure streak, ~30 consecutive pushes) | gitignored + `git rm --cached` |
| GG-102 | Guard itself regressed to blocking on *any* untracked file, not just modified tracked ones | guard rewritten to `--untracked-files=no` |
| GG-104 | (Different failure mode — see below) | services restart added |
| GG-117 | `exp_output/T255-BAND-MONITOR/band_monitor_summary.json` (sibling of a file GG-102 had already fixed) | gitignored |

Each fix above was correct but scoped to the one file that broke that day — a whack-a-mole pattern. **GG-130 (2026-07-22) replaces the whack-a-mole with a general rule:** any tracked file modified under `exp_output/`, `data/`, `logs/`, or `models/` is now automatically reset to the committed version before the guard even looks for problems, because every one of these incidents lived under one of those four roots. See "The GG-130 fix" below.

**GG-104 is a different failure mode and is unaffected by this runbook's fix.** It's about the `deploy` step succeeding (code pulled) while the long-running `t4-mlb` / `pmbot-web-dashboard` systemd services kept running stale code — already fixed by the unconditional `systemctl restart` step that runs after every pull. If a future failure happens in the "Restart persistent services" or "Verify HEAD and service freshness" step rather than the "Deploy" step, it is **not** this runbook's failure class — check service logs on the VPS directly (`journalctl -u t4-mlb -n 100`).

---

## The GG-130 fix (2026-07-22)

`deploy.yml`'s Deploy step now pipes a real, readable bash script to the VPS via `ssh ... 'bash -s' <<'REMOTE_DEPLOY'` instead of embedding the guard as a single escaped SSH command string. The logic:

1. Run `git status --porcelain --untracked-files=no` on the VPS (unchanged from T-171 — only modified *tracked* files count as dirty; new untracked cron output never blocks a deploy).
2. For every modified tracked file, check whether its path starts with one of `exp_output/`, `data/`, `logs/`, `models/` (`REGEN_ROOTS` in the script).
3. If it does: `git checkout -- <file>` (discard the VPS-local drift, reset to the committed version) and log it as **AUTO-HEALED**. These roots are exclusively written by scheduled jobs per `deploy/cron.conf` — the VPS is never the source of truth for anything tracked under them, so resetting is always safe. If a file under these roots genuinely needs new committed content, that change should land through a normal commit, not by mutating in place on the box.
4. If it does not (i.e., a source file, config, doc, or anything outside those four roots was hand-edited on the VPS): still hard-fail with `exit 1`, exactly as before. This preserves the original T-171 protection — a real, unexpected edit to tracked source on the VPS is still a genuine problem and should still block the deploy.
5. Only after the above resolves cleanly does `git pull --ff-only origin main` run.

This was verified against three synthetic test cases before being shipped (mixed regen + real-source drift → auto-heal the regen file, still hard-fail on the source file; pure regen-root drift across multiple roots including a nested directory → full auto-heal, clean exit; no drift → immediate pass). It has **not** yet been observed against a live VPS run, since the session that wrote this fix had no SSH/GitHub Actions access to confirm end-to-end (see "Session provenance" in the GG-130 log entry).

### Why this file was NOT split into a separate `deploy/deploy_guard.sh`

GG-128 (2026-07-20, this same repo) found that duplicating the same parsing logic across two scripts (`session_delta.sh` and `governance_scan.sh`) let one get fixed while the other silently kept the bug. A separate `deploy_guard.sh` would also have a bootstrapping problem: the very first deploy after shipping the fix would need the VPS to already have pulled the script that gates the pull. Keeping the guard as the single source of truth inside `deploy.yml`, piped fresh via heredoc every run, avoids both problems.

---

## Diagnosis: is a `deploy` failure this failure class or something else?

Open the failed run in GitHub Actions (`https://github.com/eignacio1/prediction-market-bot/actions`) and expand the "Deploy" step's log.

- **Log shows `AUTO-HEALED (GG-130): ...` followed by success** → not a failure at all, this is the new guard working as intended (informational only, does not fail the step).
- **Log shows `ERROR: VPS has local modifications to TRACKED files outside known cron-output roots ...` and lists a file** → a real, unexpected edit. Check that specific file on the VPS (`ssh root@157.230.91.33 "cd /opt/prediction-market-bot && git diff -- <path>"`) to see what changed and why. If it's legitimate work-in-progress, commit and push it from the VPS or discard it (`git checkout -- <path>`) depending on intent. If it's actually regenerable output that should have been added to `REGEN_ROOTS` or gitignored, do that and register a new gap entry — do not just silently discard and move on, per this log's own Invariant (register the gap before remediation).
- **Log shows a `fatal:` from `git pull` itself (e.g. non-fast-forward, diverged history)** → different problem: the VPS's local `main` has commits `origin/main` doesn't know about (someone committed directly on the VPS). This is not the dirty-tree guard; investigate via `git log --oneline -5` on both sides and reconcile manually. Do not force-push without following this project's own git-safety protocol (confirm with the operator, per the force-push precedent in `DECISION_LOG.md` 2026-07-21).
- **SSH connection itself fails (`Permission denied`, `Connection timed out`)** → check whether `VPS_SSH_KEY` secret is still valid and whether the VPS is reachable (reboot, firewall change, IP change). Unrelated to this runbook's fix.
- **"Restart persistent services" or "Verify HEAD and service freshness" step fails** → GG-104 territory, not this runbook. Check `journalctl -u t4-mlb` / `journalctl -u pmbot-web-dashboard` on the VPS directly.

---

## If `REGEN_ROOTS` needs to grow

If a *fifth* incident happens under a path not covered by `exp_output/`, `data/`, `logs/`, `models/`, do not just gitignore the one file (that reintroduces the whack-a-mole pattern this fix exists to end). Instead:

1. Check `deploy/cron.conf` for every job that writes into that path — confirm it's genuinely a scheduled-job output, not a file a human is expected to hand-edit.
2. Add the new root (or the specific subdirectory, if the root is too broad to be safe) to `REGEN_ROOTS` in `deploy.yml`'s Deploy step.
3. Register the incident as its own gap in `GOVERNANCE_GAP_LOG.md` (per the log's own Invariant), noting it as a sibling of GG-130 rather than a wholly new category.

---

## On the inbox-noise complaint that prompted this runbook

GitHub emails on every workflow-run failure by default, with no repo-level way to distinguish "known, auto-healed, non-issue" from "genuinely blocking." The GG-130 fix reduces *false-positive* failure emails to near zero (the auto-heal case no longer fails the step at all), but any *real* failure will still correctly email — that's appropriate signal, not noise. If email volume is still a problem after this fix lands and is observed for a few weeks:

- **Account-level lever (fastest, no code change):** GitHub → Settings → Notifications → Actions has a setting to only notify when a previously-passing workflow starts failing (rather than on every failing run of an already-red workflow) — worth checking if it's not already on.
- **Repo-level lever:** a Gmail filter on `from:notifications@github.com subject:"Deploy to VPS"` routing to a label instead of the inbox is a reasonable middle ground if the operator wants to keep the signal but stop the interrupt.

Neither of these was applied as part of GG-130 — they're account/mail-client settings, not something this session had access to change.
