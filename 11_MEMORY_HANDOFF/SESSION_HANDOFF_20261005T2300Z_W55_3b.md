# W55.3b handoff
Status: DONE (with standing dependency) | PR #164 bf1afb0 merged, CI green | 69 T1 MLB shadow rows written; t4-mlb restart not_needed.
Operator must: run scripts/sync_mlb_games_cache.sh at least daily from the Mac (GG-482); otherwise all MLB shadow cells fail closed after 26h. Decide on a scheduler (launchd / GH Actions / non-throttled egress).
Resume: GG-472 (MLB settle script) and GG-482 scheduler. close_session_claim.sh not run (GG-451).
