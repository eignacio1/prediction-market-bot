# VPS Deployment Guide — Prediction Market Bot (ENV-02)

**Purpose:** Step-by-step guide to provision the VPS for PIPE-02 pre-game inference (Phase 6 paper trading prep).  
**Environment:** ENV-02 — Paper Trading (market data read-only; no order submission)  
**Who:** Earl Ignacio (sole operator)  
**Last updated:** 2026-05-28  

---

## 1. VPS Selection

**Recommended:** DigitalOcean Basic Droplet — $6/month (1 vCPU, 1 GB RAM, 25 GB SSD)  
**Alternative:** Hetzner CX11 — ~€4/month (same specs, European datacenter)

Both providers use datacenter IP ranges (ASNs) that pass Kalshi's CloudFront WAF.
Work ISP is blocked (strict outbound security policy). Any other network passes — home ISP, hotel wifi, hotspot, etc.

**OS:** Ubuntu 22.04 LTS (recommended; scripts below written for Ubuntu/Debian)  
**Region:** US East (New York or Toronto) — closer to Kalshi's infrastructure

**Quick create (DigitalOcean CLI):**
```bash
doctl compute droplet create pred-market-bot \
  --region nyc3 \
  --size s-1vcpu-1gb \
  --image ubuntu-22-04-x64 \
  --ssh-keys <your-key-id>
```

---

## 2. One-Time Server Setup

SSH into the droplet and run `setup.sh`:

```bash
scp deploy/setup.sh root@<VPS_IP>:/tmp/
ssh root@<VPS_IP> bash /tmp/setup.sh
```

Or run manually:

```bash
ssh root@<VPS_IP>
bash -c "$(curl -fsSL https://raw.githubusercontent.com/.../setup.sh)"
# — or copy-paste contents of deploy/setup.sh —
```

---

## 3. Deploy Code

```bash
# On VPS — clone repo
git clone https://github.com/<your-repo>/prediction-market-bot.git /opt/prediction-market-bot
cd /opt/prediction-market-bot

# Install Python dependencies (must match training environment — see note below)
pip3.11 install -r 06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-base.txt
```

**sklearn version note:** The serialized model (`models/prod_model.joblib`) was trained with sklearn 1.4.2. Install the same version on the VPS to avoid version mismatch warnings:
```bash
pip3.11 install scikit-learn==1.4.2
```

If you prefer to retrain directly on the VPS (eliminating version mismatch entirely):
```bash
# Pull data on VPS (requires nba_api, ~3 min)
PYTHONPATH=src python3.11 src/prediction_market_bot/run_exp005.py --no-api  # if CSV was scp'd
# Or full pull:
PYTHONPATH=src python3.11 src/prediction_market_bot/run_exp005.py
# Then train:
PYTHONPATH=src python3.11 src/prediction_market_bot/train_and_save_model.py
```

---

## 4. Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
cp /opt/prediction-market-bot/.env.example /opt/prediction-market-bot/.env
nano /opt/prediction-market-bot/.env
```

Set at minimum:
```
BOT_ENV=paper
VENUE_API_KEY=<your-kalshi-read-only-key>
LOG_DIR=/opt/prediction-market-bot/logs
```

**Security:** `chmod 600 /opt/prediction-market-bot/.env` — restrict to owner only.

---

## 5. Deploy Serialized Model

The model must be deployed to the VPS. Two options:

**Option A — Copy from local (simplest):**
```bash
scp models/prod_model.joblib models/prod_model_meta.json \
    root@<VPS_IP>:/opt/prediction-market-bot/models/
```

**Option B — Retrain on VPS (eliminates sklearn version mismatch):**
```bash
ssh root@<VPS_IP>
cd /opt/prediction-market-bot
scp user@local:/path/to/exp_output/EXP-005/EXP-005_feature_matrix.csv exp_output/EXP-005/
PYTHONPATH=src python3.11 src/prediction_market_bot/train_and_save_model.py
```

---

## 6. Connectivity Health Check

Verify everything works before enabling cron:

```bash
ssh root@<VPS_IP>
cd /opt/prediction-market-bot
bash deploy/healthcheck.sh
```

Expected output:
```
[OK] Python 3.11 available
[OK] Model file present (models/prod_model.joblib)
[OK] Feature matrix present
[OK] VENUE_API_KEY set
[OK] Kalshi API reachable (exchange_active=True)
[OK] Environment: BOT_ENV=paper
All checks passed — VPS ready for PIPE-02 cron.
```

---

## 7. Install Cron Job

```bash
ssh root@<VPS_IP>
crontab -l > /tmp/existing_cron
cat /opt/prediction-market-bot/deploy/cron.conf >> /tmp/existing_cron
crontab /tmp/existing_cron
crontab -l  # verify
```

The cron job runs PIPE-02 at **21:30 UTC** (5:30pm ET) daily, ~90 min before 7pm ET games.

---

## 8. First Run Verification

Trigger a manual run to verify end-to-end:

```bash
ssh root@<VPS_IP>
cd /opt/prediction-market-bot
source .env
PYTHONPATH=src /usr/local/bin/python3.11 \
    src/prediction_market_bot/run_pregame.py
```

Check output:
```bash
cat logs/pregame_$(date +%Y%m%d).json | python3 -m json.tool | head -30
cat logs/audit.jsonl | tail -5
```

---

## 9. Ongoing Operations

**Check yesterday's report:**
```bash
ssh root@<VPS_IP> cat /opt/prediction-market-bot/logs/pregame_$(date -d yesterday +%Y%m%d).json
```

**Monitor audit log:**
```bash
ssh root@<VPS_IP> tail -f /opt/prediction-market-bot/logs/audit.jsonl
```

**Update model** (after new training run locally):
```bash
scp models/prod_model.joblib models/prod_model_meta.json root@<VPS_IP>:/opt/prediction-market-bot/models/
```

**Pull code updates:**
```bash
ssh root@<VPS_IP> "cd /opt/prediction-market-bot && git pull"
```

---

## 10. Security Reminders (NFR-05)

- `.env` file: never committed, `chmod 600`, accessible to operator only
- `VENUE_API_KEY`: read-only Kalshi key (market data only, no order submission)
- `BOT_C4_ACTIVE`: must NOT be set in ENV-02 (enforced by all runners)
- Audit log at `logs/audit.jsonl`: append-only per C6 policy
- No model retraining on VPS without local EXP + ADR amendment
