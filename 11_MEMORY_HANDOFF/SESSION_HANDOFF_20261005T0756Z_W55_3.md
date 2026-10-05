# W55.3 handoff
Status: BLOCKED (D2) | branch session/20261005T075443Z-w55-mlb-shadow-source | no PR, no code | ESPN cannot supply home_sp/away_sp (MLBAM vs ESPN id namespaces); all other fields match; model input not substituted.
Operator must decide: option 1 (local refresh + sync to VPS) recommended; see 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W55_3_mlb_shadow_source_results.md.
t4-mlb: no deploy, no restart. GG-470/GG-453 remain OPEN. Resume: implement option 1 (a sync script + cron/hand step) once chosen.
Not run: scripts/close_session_claim.sh (GG-451 hazard); claim closed by a manual row.
