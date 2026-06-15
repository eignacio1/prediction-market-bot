# RUNBOOK — Dark-Period Close: T-174 deploy + live-book correction + T-171 untrack

**Status:** ⛔ GATED — requires operator OK **and** a DS retroactive-halt ruling before any step that writes the live VPS book or pushes to deploy.
**Owner:** Earl Ignacio (operator) + DS sign-off
**Prepared:** 2026-06-14 SESSION 63 (T-174 WS1/WS2 code-complete, all local; nothing deployed)

---

## Why these are one unit

Three changes are entangled and must be sequenced together:

1. **T-174 (GG-034)** — the code now derives `total_realized_pnl` and `bankroll_usd`
   from the ledger and reconciles on load. When this code runs against the live
   VPS book, `reconcile()` adopts the true ledger value and the next `_save()`
   persists it. **This surfaces the true −25.1% drawdown (−$251.21), which trips
   the 20% `max_drawdown_pct` kill switch and halts all bands.**
2. **DS ruling** — does the true −25.1% (or −30.3% clean) drawdown *retroactively*
   halt paper trading? What is the corrected G6 baseline of record? G6 must not be
   called until this number is ratified. (Updated in `G6_GATE_CHECKLIST.md`: T2-D
   and T3-B now correctly show FAILING on the true ledger figure.)
3. **T-171 (GG-033)** — the live book is git-tracked (`logs/paper_portfolio.json`),
   so `git pull` on deploy aborts on a dirty VPS tree. Untracking must ship with
   the T-174 deploy so the corrected book is not clobbered by git.

Deploying T-174 without operator OK would silently trip the kill switch in
production. Untracking without the backup dance would lose the live book. Hence: gated.

## Preconditions (verify before starting)

- [ ] G5 (game_date 2026-06-13) resolved; **zero open positions** on the live book.
      (At prep time G5 had 41 open — resolve first via `run_resolve_local.py` / GHA.)
- [ ] Operator explicitly authorizes surfacing the true drawdown (kill switch will trip).
- [ ] DS ruling recorded in DECISION_LOG: retroactive-halt decision + corrected G6 baseline.
- [ ] Local `main` is green (`.venv311/bin/python -m pytest tests/ -q`) and contains
      T-174 (WS1+WS2). Current: **951/951 pass.**

## Sequence

> Each step is one command, backup-first. Do not batch — verify between steps.

**0. Snapshot the live book (already pulled to `logs/.vps_portfolio_cache.json`).**
```bash
ssh prediction-market-vps "cp /opt/prediction-market-bot/logs/paper_portfolio.json /opt/prediction-market-bot/logs/paper_portfolio.json.bak_t174 && cp /opt/prediction-market-bot/logs/paper_portfolio_t4.json /opt/prediction-market-bot/logs/paper_portfolio_t4.json.bak_t174"
```

**1. T-171 clean VPS working tree (so deploy `git pull` will not abort).**
```bash
ssh prediction-market-vps "cd /opt/prediction-market-bot && git checkout HEAD -- logs/paper_portfolio.json logs/paper_portfolio_t4.json"
```

**2. Local: untrack the books + gitignore them, in the SAME commit as T-174.**
```bash
git rm --cached logs/paper_portfolio.json logs/paper_portfolio_t4.json
printf 'logs/paper_portfolio.json\nlogs/paper_portfolio_t4.json\n' >> .gitignore
git add -A
git commit -m "[T-174+T-171] GG-034 ledger-derived P&L/bankroll + untrack live books"
```

**3. Push → `deploy.yml` fires (GHA auto-deploy). VPS `git pull` deletes the (now
untracked) checked-out books from the working tree.**
```bash
git push origin main
```

**4. VPS restore the live books from the backup (git no longer manages them).**
```bash
ssh prediction-market-vps "cd /opt/prediction-market-bot && cp logs/paper_portfolio.json.bak_t174 logs/paper_portfolio.json && cp logs/paper_portfolio_t4.json.bak_t174 logs/paper_portfolio_t4.json"
```

**5. Trigger the correction + verify the desync is gone.** Any PaperTrader load now
runs `reconcile()` and logs a `portfolio_pnl_desync` C6 event; the next mutation
persists the ledger value. To force-correct without waiting for a cron mutation:
```bash
ssh prediction-market-vps "cd /opt/prediction-market-bot && .venv311/bin/python -c \"
from pathlib import Path
from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
t = PaperTrader(Path('logs/paper_portfolio.json'), AuditLogger(log_path=Path('logs/audit.jsonl')))
ok, rep = t.reconcile(); print('reconcile:', rep)
t._save()  # persist derived total_realized_pnl + bankroll_usd
print('summary:', t.summary())
\""
```
Expect: `total_realized_pnl ≈ −251.21`, `realized_drawdown_pct ≈ 25.1`, kill switch now sees the true figure.

**6. Apply the identical T4-book correction** (stored −$21.59 vs Σ −$47.25) — same
script against `logs/paper_portfolio_t4.json`.

**7. Verify deploy HEAD + book integrity.**
```bash
ssh prediction-market-vps "cd /opt/prediction-market-bot && git log -1 --oneline && .venv311/bin/python -c 'import json; p=json.load(open(\"logs/paper_portfolio.json\")); print(\"pnl:\", p[\"total_realized_pnl\"], \"bankroll:\", p[\"bankroll_usd\"], \"open:\", len(p[\"open_positions\"]))'"
```

## Rollback

Restore from `*.bak_t174` (step 0) on the VPS; `git revert` the untrack commit
locally. Backups are the recovery path for every write step.

## After completion

- Record DS ruling + corrected G6 baseline in DECISION_LOG and `G6_GATE_CHECKLIST.md`.
- Mark GG-034 RESOLVED (currently CODE-COMPLETE, NOT DEPLOYED) and T-171 COMPLETE.
- Re-run `scripts/build_clean_dataset.py` against the corrected book for the final
  frozen record.
