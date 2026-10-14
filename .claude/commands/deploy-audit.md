# /deploy-audit — READ-ONLY box vs repo audit (W72.2, replaces /vps)

Changes nothing. Every command below is a read. Report PASS/FAIL per line; do not fix inline — register a GG.

```bash
# 1. Box HEAD vs origin/main
git fetch -q origin && echo "origin/main: $(git rev-parse --short origin/main)"
ssh prediction-market-vps 'cd /opt/prediction-market-bot && echo "box HEAD: $(git rev-parse --short HEAD)" && git status --porcelain | head'
# 2. Restart-policy decisions (last 20 deploys: expect deployed/docs_only/skip_live_game; flag gate_red/verify_failed/policy_failed/dirty_tree_abort)
ssh prediction-market-vps 'tail -n 20 /opt/prediction-market-bot/logs/vps_deploy.log 2>/dev/null'
# 3. Live crontab vs repo mirror (job count + any duplicate line)
ssh prediction-market-vps 'crontab -l | grep -v "^#" | grep -v "^$" | sort | uniq -d | head; crontab -l | grep -vc "^#\|^$"'
# 4. Secrets permissions: .env must be 600 and no .env.bak* copies
ssh prediction-market-vps 'cd /opt/prediction-market-bot && stat -c "%a %n" .env; ls .env.bak* 2>&1 | head'
# 5. Running t4-mlb vs disk
ssh prediction-market-vps 'systemctl is-active t4-mlb; systemctl show t4-mlb -p ActiveEnterTimestamp'
# 6. Healthcheck
ssh prediction-market-vps 'bash /opt/prediction-market-bot/deploy/healthcheck.sh | tail -15'
```

Never print key values. Never run the archived `.claude/commands/_archive/vps_DO_NOT_RUN.md`.
