> **DO NOT RUN. ARCHIVED 2026-10-14 (W72.2, GG-660).** This is the May-2026 first-time provisioning script. Run today it
> would APPEND `deploy/cron.conf` to the live crontab (every job, incl. `vps_deploy.sh`, runs twice; shadow arms write
> every row twice), `scp` the model over the box's model, and pin old deps. Kept for history only. Use `/deploy-audit`
> (read-only) to check the box; deploys happen via `vps_deploy.sh` on push to main.

# /vps — VPS Deployment / Re-Deployment (T-059 ✅ COMPLETE 2026-05-29)

**Current VPS:** `157.230.91.33` — DigitalOcean NYC3, Ubuntu 24.04, Python 3.12, sklearn 1.8.0. Use this guide for re-deployment, new-droplet migration, or model pushes. Read `deploy/DEPLOYMENT_GUIDE.md` in full before starting.

---

## Pre-Deployment Checklist

Before touching the VPS, confirm all of these locally:

```bash
# 1. Run full hygiene check first
# (use /hygiene command)

# 2. Confirm production model is current
python3.11 -c "
import json
m = json.load(open('models/prod_model_meta.json'))
print(f'Model: {m[\"model_version\"]} | Features: {m[\"feature_count\"]} | Trained: {m[\"trained_at\"]}')
"

# 3. Verify env.template has no real secrets
grep "REPLACE_WITH" deploy/env.template  # should show placeholder text

# 4. Confirm BOT_C4_ACTIVE is NOT in env.template
grep "BOT_C4_ACTIVE" deploy/env.template  # should show commented-out warning only

# 5. Confirm cron schedule
cat deploy/cron.conf  # 21:30 UTC + 01:30 UTC
```

---

## Step-by-Step Deployment

### 1. Provision VPS

```bash
# DigitalOcean NYC3 — datacenter IP bypasses Kalshi CloudFront WAF
# IMPORTANT: Use ubuntu-24-04-x64 (24.04 LTS) — original droplet confirmed on this image
doctl compute droplet create pred-market-bot \
  --region nyc3 \
  --size s-1vcpu-1gb \
  --image ubuntu-24-04-x64 \
  --ssh-keys <your-key-id>
```

### 2. One-Time Server Setup

```bash
scp deploy/setup.sh root@<VPS_IP>:/tmp/
ssh root@<VPS_IP> bash /tmp/setup.sh
```

### 3. Deploy Code

```bash
ssh root@<VPS_IP>
git clone <your-repo-url> /opt/prediction-market-bot
cd /opt/prediction-market-bot
# Use project venv (Python 3.12) — setup.sh creates /opt/prediction-market-bot/venv/
source /opt/prediction-market-bot/venv/bin/activate
pip install scikit-learn==1.8.0  # must match training environment
pip install -r 06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-base.txt
```

### 4. Deploy Model

```bash
# Current VPS IP: 157.230.91.33 (replace with new IP for fresh droplet)
scp models/prod_model.joblib models/prod_model_meta.json \
    root@157.230.91.33:/opt/prediction-market-bot/models/
```

### 5. Configure Environment

```bash
# On VPS:
cp deploy/env.template .env
nano .env  # fill in VENUE_API_KEY (read-only Kalshi key from ACC-0002)
chmod 600 .env

# CRITICAL: verify BOT_C4_ACTIVE is NOT in .env
grep "BOT_C4_ACTIVE" .env  # must return nothing
```

### 6. Health Check

```bash
ssh root@<VPS_IP>
cd /opt/prediction-market-bot
bash deploy/healthcheck.sh
```

Expected: All [OK] lines. Any [FAIL] = stop and diagnose.

### 7. Install Cron

```bash
ssh root@<VPS_IP>
crontab -l > /tmp/existing_cron
cat /opt/prediction-market-bot/deploy/cron.conf >> /tmp/existing_cron
crontab /tmp/existing_cron
crontab -l  # verify 3 jobs: 21:00 UTC health | 21:30 UTC PIPE-02 | 01:30 UTC PIPE-03
```

### 8. First Manual Run

```bash
ssh root@<VPS_IP>
cd /opt/prediction-market-bot
source .env
PYTHONPATH=src /opt/prediction-market-bot/venv/bin/python src/prediction_market_bot/run_pregame.py

# Verify outputs:
cat logs/pregame_$(date +%Y%m%d).json | python3 -m json.tool | head -30
tail -10 logs/audit.jsonl
# Also check paper portfolio if PIPE-03 has run:
cat logs/paper_portfolio.json | python3 -m json.tool | tail -20
```

---

## Post-Deployment Verification

Report after first successful run:
- Number of KXNBAPTS markets found
- Edge values for top markets (from pregame JSON)
- Any ERROR entries in audit.jsonl
- Confirmation: C4 status = REJECTED (phase_gate_not_reached) for all forecasts

---

## Security Reminders

- `.env` on VPS: `chmod 600`, never in git, never in logs
- Kalshi API key: read-only (ACC-0002); no order submission in ENV-02
- BOT_C4_ACTIVE: must be absent — if ever accidentally set, stop cron immediately
- Audit log: append-only; never delete entries

---

## Update After Completion

When T-059 is complete:
1. Mark T-059 ✅ COMPLETE in `04_EXECUTION/TODO_NEXT.md`
2. Update MEMORY_BANK.md — Phase 6 status
3. Update PLAN.md — T-059 complete, T-060 unblocked
4. Record VPS IP (non-secret) in ENVIRONMENTS.md under ENV-02
