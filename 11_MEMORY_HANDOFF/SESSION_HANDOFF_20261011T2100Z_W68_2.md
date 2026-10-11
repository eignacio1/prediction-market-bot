# Session Handoff — 2026-10-11T21:00Z

<!-- session-meta
task_id: T-821
tier: MEDIUM
timestamp: 2026-10-11T21:00:00Z
commit: see PR
one_line_summary: W68.2 Part A (demo-only guard + demo_fill.env on NBA/NHL shadow crons) merged PR #228; Part B (daily forward-test report job, gov-scan line, /project panel) built and merged; VPS activation unverified (ssh denied).
gg_touched: GG-570, GG-571 (stay OPEN), GG-586, GG-587
adr_touched: none (ADR-0072 parameters unchanged)
plan_deliverable_moved: no
vision_pillar: EXECUTION
gap_measure: E1
gap_delta: E1 unchanged: 0 shadow-arm fills accrued (source: none observable; VPS log unreachable). Mechanism now in code; measure moves only after crons carry it and NHL/NBA orders fill.
-->

Part A: PR #228 (aba80af). Part B: this PR. Both local-pytest verified.

Open, for the next session / operator:
1. VPS install unverified. ssh read was refused by the classifier: `ssh prediction-market-vps "cd /opt/prediction-market-bot && git log --oneline -1 && crontab -l"`. GG-570/571 remain OPEN until cron lines carry the change and one NHL accepted demo order is observed. NBA regular season starts 10-20.
2. Step 4 (run report on existing orders) not done: needs the VPS log. Command: `cd /opt/prediction-market-bot && BOT_ENV=paper venv/bin/python scripts/demo_fill_forward_report.py`. The 11:25 UTC cron will do it once deployed.
3. GG-586: SHADOW control arm places no order, so the ADR-0072 treatment-minus-control verdict cannot be formed for shadow cells; needs an operator/ADR decision.
4. GG-587: turn-off edits tracked `deploy/demo_fill.env` on the VPS, which trips `vps_deploy.sh` dirty-tree guard; the edit must be committed to main or the guard taught the path. Markout (30 min) and non-demo-host conditions are not evaluable by the job (reported NOT_EVALUABLE / GUARDED).
5. t4-mlb deploy decision: read `logs/vps_deploy_decisions.jsonl` on the VPS; not readable from here.

No order/stake/kelly/ledger change beyond the block's authorization.
