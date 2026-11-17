# W115.3 handoff - D6 one game end to end (B-091 + B-092) - PARTIAL, stopped on the operator's usage addendum (SW-9)
Branch `session/20261117T010353Z-w115-3-d6-one-game` @ 1ce79c5, PR #502, CI pending at stop (NOT merged). Nothing ran on the box.
vision_pillar: DEPTH (D6) | gap_measure: D6 wired on the box | gap_delta: 3 -> 3 (unmeasured; fixes unmerged) | surface_delta: 0
DONE in PR #502 (10 new tests + 65 neighbours green locally):
- GG-1940 NHL UNROUTED (5,513 skips): scripts/nhl_shadow_eval.py never called the router. Hook injected from scripts/run_nhl_shadow_staked.py (shadow_route.hook_for); NHL previous-mid now read from data/shadow/nhl.
- GG-1941 NFL layer 3 = 0: coverage.filter_layer_sports() tested default_supply().nfl_providers, set on no host. Now tests the providers. GG-1933 ("None on the box") is likely a misdiagnosis; the trace confirms.
- GG-1939 router ERROR rows (NBA 5,193 / NFL 197) logged only the exception type; shadow_route.router_fields now logs the message. Cause still unknown.
- scripts/d6_trace_read.py + allowlist line `d6_trace_read` (read-only): one game per sport through the seven layers, rule vs row.
HALF-DONE: (1) GG-1939..1941 are NOT yet written into GOVERNANCE_GAP_LOG.md. (2) NHL event store install task not written. Local dry run (2025+2026 seasons, scratch copy): store 73 MB + raw ~60 MB; compile 61 s at 2.0 GB peak RSS; filter_supply._nhl_state build 2.8 s at 885 MB peak RSS. NEITHER fits the 961 MB box: compile_store must go per-season / streamed, and _nhl_state must not load full events+shifts per cron run (precompute a small state file) BEFORE any install task. (3) row_sizing.row_decision is called by nothing; no decision taken. (4) Part C not started.
NEXT STEP, exactly: read CI on #502 -> merge on green -> deploy_truth_read (record t4-mlb) -> push request `task = "d6_trace_read"` -> write the three trace tables -> fix the ERROR cause from `error_row_rerun` -> shrink the NHL store memory -> then scripts/nhl_event_store_install.py (template scripts/ride_board_install.py).
pattern_sweep: writers that bypass router_fields: only scripts/nhl_shadow_eval.py found (pregame_shadow/runner.py covers NBA/NFL/MLB); not swept wider.
directive_conflicts: none. OPERATOR_DIRECTIVES.md was not read (budget). Interface change: shadow_route.router_fields gained ledger_path; new route_row, hook_for.
Operator decisions: none ready. No install task exists to approve.
