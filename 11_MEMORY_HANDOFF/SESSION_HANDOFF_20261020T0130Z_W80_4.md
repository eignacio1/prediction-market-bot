# Session handoff - W80.4 foundation docs

**Status:** DONE (remainder named in GG-970) | **Branch @ SHA:** session/20261020T005049Z-w80-4-foundation-docs, squash-merged to main `750b895` + Part B | **PR + CI:** #294, `test` pass (5m36s)

vision_pillar: PLUMBING
gap_measure: foundation docs classified; LIVING docs contradicting the system; doc staleness alarm
gap_delta: classified 0 -> 83 registry entries (incl. 6 new READMEs); known-wrong LIVING docs 3 -> 0 (kill-switch, access, vendor rewritten) plus 2 superseded archived; alarm none -> live in governance scan (source: scripts/doc_registry.py check, 2026-10-20). Not moved: LIVING docs actually verified = 9 of ~54; the rest are registered with blank last_verified.
pattern_sweep: 01_SPEC and 08_MODEL_RISK_GOVERNANCE registered, not rewritten. Docs restating the old kill-switch (`bot.kill_switch`) were searched in the folders in scope; the rewritten runbook is canonical. Bannered, not verified: ENVIRONMENTS, RUN_INSTRUCTIONS, DATA_SNAPSHOTS_INDEX, ARTIFACT_REGISTRY, ONCALL, OBSERVABILITY, SLA_SLO_SLI, CAPACITY_PLANNING.
surface_delta: 0

Operator quote: "I'm not expecting we scour every damn folder and file and update everything every second - we've designed strict protocol for our logging. But I find it very very very hard to believe that our core foundation files for each directory folder has been pure deadweight for 5 months. That's ludicrous and quite honestly a waste of space."

**Files:** created `00_ADMIN/DOC_REGISTRY.toml`, `scripts/doc_registry.py`, `tests/test_doc_registry.py` (5 pass), READMEs in 06/07/09_INTEGRATION_PATCHES/09_SECURITY/10/ARCHIVE. Rewritten: RUNBOOK_kill-switch, ACCESS_CONTROL_MATRIX, VENDOR_RISK. Archived (git mv, stub left): KNOWN_ISSUES, PIPELINES_JOBS. Record headers added to RECORD .md files. Status banners on 8 stale LIVING docs. Edited: `.claude/hooks/governance_scan_full.sh` (one line), `00_ADMIN/README.md`, GG log (GG-970/971), DECISION_LOG, ACTIVE_QUEUE.

**Caveats:** PyPI "bandit/pinning" mitigation in VENDOR_RISK is carried over, not re-verified; VPS provider is not recorded. First staleness alarms for unverified docs fall around late Nov 2026 (180 d).
**Operator decisions:** none.
**Pending (one line):** gap agent verifies the LIVING docs with blank `last_verified` (GG-970), starting with 01_SPEC and 08_MODEL_RISK_GOVERNANCE.
