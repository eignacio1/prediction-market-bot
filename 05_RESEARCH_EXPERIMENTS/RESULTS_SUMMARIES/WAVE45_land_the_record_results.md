# Wave 45 land-the-record — results (PARTIAL: D2 landing, D3 test column, D1(b/c) open)

## D0 snapshot (shared tree, before any change)
HEAD 9f2b837, 140 behind origin/main. md5: ACTIVE_QUEUE 9b10ee2e…, ARCHIVE e5315da2…, CARRY_FORWARD 83e75f82…, PASTE_IN 5994bf1c…. Copies in session scratch `d0/` (md5s match).

## D1
- (a) LANDED `fa99794` on origin/main (claim 0a6edf0 before it). Blob hashes worktree == origin/main for all four (queue a3c47aba, archive fcd9b788, carry-forward 1387c43d, paste-in 24a2c0fe). Push attempt 1 hit a transient remote error; attempt 2 ok; re-verified.
- (b) NOT DONE. `git pull --ff-only` refused: `.git/index.lock` (0 bytes, Sep 29 17:09, open FD held by pid 33525 com.apple.Virtualization.VirtualMachine.xpc). Not removed. Shared tree unchanged; also 6 dirty tracked files with upstream changes and untracked `Live Terminal.html` tracked upstream — pull would refuse on those too. Operator decision needed.
- (c) Shared tree HEAD != origin/main (140 behind). `_w33_recovered.md` vs archive: NOT compared this session; file not deleted.

## D2 (ADR-0067 / t4-ledger-durability, tip 447c5df; de94172)
Production = manual `git pull` in /opt/prediction-market-bot; main reaching prod = deploy. Land docs only: ADR-0067 (PROPOSED), T589 results, SESSION_HANDOFF_20260930_0045. Runtime (paper_trader.py + 3 tests, bench script) stays on branch. de94172: superseded (digest/handoff already on main; only stale nav bumps unlanded). Full-merge candidate conflicts (UU) on PLAN/TODO_NEXT/MEMORY_BANK. Docs-only candidate = origin/main + 3 files; full pytest was at ~43% (all dots, no failures) at close-out; NOT LANDED because result not final. Log: scratchpad/cand_pytest.log.

## D3 (33 unmerged remote branches; no deletions; tests NOT run per branch)
Unlanded = `git cherry` "+" count. Most are session-end nav/handoff/digest commits conflicting with current nav files; stale snapshots must not be merged wholesale.
| branch (session/…) | last | unlanded | runtime? | disposition |
|---|---|---|---|---|
| 20260824T233617Z-t484-phase2-input | 08-24 | 3 | no | review; likely stale nav |
| 20260825T043355Z-t493-adr0058-t1-reopen | 08-24 | 2 | no | docs/ADR; operator review |
| 20260826T045926Z-t497-t1-flat-stake-wrapper | 08-26 | 1 | src+test | runtime; keep, needs sizing review |
| 20260903T002904Z-record-signoffs-20260903 | 09-03 | 8 | no | sign-off records; verify vs main |
| 20260903T184908Z-apr0033-accept-and-reroute | 09-03 | 0 | no | content landed; ref stale |
| 20260904T000244Z-rerecord-adr-signoffs | 09-03 | 6 | no | verify vs main |
| 20260904T000252Z-gg242-filename-sweep | 09-03 | 1 | 1 | likely stale |
| 20260905T162347Z-hyp011-moneyline-lr-run | 09-05 | 2 | no | docs |
| 20260905T221723Z-t500-nfl-price-capture | 09-05 | 1 | no | docs |
| 20260905T221739Z-nfl-readiness-audit | 09-05 | 4 | no | docs |
| 20260905T221746Z-t4-nfl-nhl-scaffolding | 09-05 | 5 | src+test | runtime; keep |
| 20260909T153928Z-gg255-mlb-t1-game-market-run-script | 09-09 | 4 | src+test | runtime; keep |
| 20260910T012346Z-gg267-per-row-model-provenance | 09-11 | 3 | src+test | runtime; keep |
| 20260915T003401Z-nfl-capture-gap-0912 | 09-14 | 3 | 1 | content merged, GG-276 resolved |
| 20260918T142928Z-gg291-threshold-backfill | 09-21 | 6 | 4 | runtime; keep |
| 20260918T142949Z-install-closeout-fix | 09-18 | 1 | no | superseded by -v2 |
| 20260918T142949Z-install-closeout-fix-v2 | 09-21 | 4 | no | scripts/process; review |
| 20260923T005837Z-vig-grounding-from-archive | 09-22 | 1 | 1 | review |
| 20260924T045012Z-clv-harness | 09-23 | 0 | 1 | content landed |
| 20260924T045227Z-resolved-filter | 09-24 | 7 | 2 | review |
| 20260929T050111Z-exp027-epa-splits | 09-28 | 0 | 3 | content landed |
| 20260929T052125Z-gg312-parity-checker | 09-28 | 0 | 2 | content landed |
| 20260930T001333Z-evidence-boundary | 09-29 | 1 | 2 | stale nav |
| 20260930T001343Z-t4-ledger-durability | 09-29 | 7 | 2 | D2 above |
| 20260930T001400Z-gap-ledger-triage | 09-29 | 2 | no | stale nav |
| 20260930T005212Z-provenance-allowlist | 09-29 | 1 | 1 | review |
| 20260930T050102Z-nfl-ingestion-widen | 09-29 | 1 | 1 | review |
| 20260930T053611Z-t4-structure-enhancer | 09-29 | 0 | no | content landed |
| 20260930T053614Z-reality-reconciliation | 09-29 | 0 | no | content landed |
| 20261001T012448Z-live-terminal-landing | 09-30 | 1 | 1 | stale nav |
| 20261001T015004Z-multileg-coherence | 09-30 | 0 | 1 | content landed |
| 20261001T015005Z-archive-self-sufficiency | 09-30 | 0 | 4 | content landed |
| 20261002T192711Z-kalshi-nonsports-control | 10-02 | 1 | 1 | active sibling wave; do not touch |

## D4 verdict
NEW PAGE RUNNING. Served HTML, VPS-disk `_HTML` and origin/main `_HTML` all sha256 fc68e5b5…daa62c (59,130 B); file blob 9f0b81d8 equal on disk and main; process.sha d8d5850. Starts at 2026-10-01 02:25:19Z and 02:52:01Z were MANUAL restarts ("Deactivated successfully", NRestarts/oom-kill 0). No restart performed; no authorization checked (none needed).

## GAPS FOUND -- FOR REGISTRATION BY 45.1 OR WAVE 46
1. Stale `.git/index.lock` in shared tree held open by a Virtualization VM process; blocks all shared-tree git writes.
2. Shared tree 140 behind with 6 conflicting dirty tracked files; untracked `Live Terminal.html` collides with a tracked upstream path.
3. Q7 invariants vacuous in a fresh worktree (no ledger data).
4. Step 4 anomalies undiagnosed: SemanticFloorViolation=1; two T1 runs with 0 players matched; T4 cycle-log age 16h.
5. Compass OS Health line 5159 chars.
6. Manual dashboard restarts unrecorded; ssh poller from 73.231.159.158 seen.
7. Transient GitHub push failure ("unable to write file …pack").
8. macOS has no `timeout`; protocol/test snippets using it fail with exit 127 silently.
9. Claim rows with ID range "TBD" give no collision protection.
10. Full test suite exceeds 10 min foreground; no documented fast subset.
11. 33 unmerged remote branches; ~8 are content-landed under other SHAs and read unlanded forever.
