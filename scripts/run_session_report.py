#!/usr/bin/env python3
"""
Session-start self-assessment report.

Reads VPS logs and portfolio state via SSH and prints a structured
one-page summary: portfolio health, bet activity, cron errors, and
T4 evaluation throughput. Run at the start of every session.

Usage:
    python3 scripts/run_session_report.py
    python3 scripts/run_session_report.py --days 3
"""
import argparse
import json
import subprocess
import sys
from datetime import date, timedelta

VPS_HOST = "prediction-market-vps"
VPS_BASE = "/opt/prediction-market-bot"

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

SEP    = "=" * 70


def ssh(cmd: str) -> str:
    r = subprocess.run(
        ["ssh", VPS_HOST, cmd],
        capture_output=True, text=True, timeout=30,
    )
    return r.stdout.strip()


def _color(text, level="ok"):
    return {
        "ok":   GREEN  + text + RESET,
        "warn": YELLOW + text + RESET,
        "err":  RED    + text + RESET,
        "bold": BOLD   + text + RESET,
    }.get(level, text)


def _portfolio_summary(path: str, label: str) -> dict:
    raw = ssh(f"cat {VPS_BASE}/logs/{path} 2>/dev/null")
    if not raw:
        return {"label": label, "missing": True}
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        return {"label": label, "parse_error": True}
    bankroll = d.get("bankroll_usd", 0.0)
    initial  = d.get("initial_bankroll_usd", bankroll)
    pnl      = bankroll - initial
    pnl_pct  = (pnl / initial * 100) if initial else 0.0
    open_p   = d.get("open_positions", {})
    closed_p = d.get("closed_positions", [])
    open_cost = sum(
        p.get("size_usd", 0.0) for p in (open_p.values() if isinstance(open_p, dict) else open_p)
        if not p.get("aged_open")
    )
    drawdown = d.get("realized_drawdown_pct", abs(min(pnl_pct, 0)) / 100)
    return {
        "label":      label,
        "bankroll":   bankroll,
        "initial":    initial,
        "pnl":        pnl,
        "pnl_pct":    pnl_pct,
        "open_count": len(open_p),
        "open_cost":  open_cost,
        "closed_count": len(closed_p),
        "drawdown":   drawdown,
    }


def _log_tail_errors(log_file: str, lines: int = 50) -> list[str]:
    raw = ssh(f"tail -{lines} {VPS_BASE}/logs/{log_file} 2>/dev/null")
    if not raw:
        return []
    errors = []
    for line in raw.splitlines():
        if any(kw in line for kw in ("ERROR", "CRITICAL", "Traceback", "TypeError", "Exception", "FAIL")):
            errors.append(line.strip())
    return errors


def _log_recent_bets(log_file: str, label: str, lines: int = 100) -> list[str]:
    raw = ssh(f"tail -{lines} {VPS_BASE}/logs/{log_file} 2>/dev/null")
    bets = []
    for line in raw.splitlines() if raw else []:
        if "FIRED" in line or "OPEN" in line or "paper_bet_placed" in line:
            bets.append(line.strip())
    return bets[-10:]  # last 10


def _t4_throughput(days: int = 1) -> dict:
    result = {"evaluated": 0, "fired": 0, "cycles": 0}
    for i in range(days):
        d = (date.today() - timedelta(days=i)).strftime("%Y%m%d")
        raw = ssh(f"grep -c 'evaluated=' {VPS_BASE}/logs/t4_mlb_live_cron.log 2>/dev/null || echo 0")
        # Look for summary lines with total_evaluated
        summary = ssh(
            f"grep 'total_evaluated\\|T4-MLB session complete\\|evaluated=' "
            f"{VPS_BASE}/logs/t4_mlb_live_cron.log 2>/dev/null | tail -20"
        )
        for line in (summary or "").splitlines():
            if "total_evaluated" in line or "evaluated=" in line:
                try:
                    # extract evaluated=NNN from log lines
                    for part in line.split():
                        if part.startswith("evaluated="):
                            result["evaluated"] += int(part.split("=")[1])
                        if part.startswith("fired="):
                            result["fired"] += int(part.split("=")[1])
                except (ValueError, IndexError):
                    pass
    return result


def _recent_resolutions(pool: str = "mlb", lines: int = 200) -> dict:
    log = "resolve_mlb_cron.log" if pool == "mlb" else "resolve_cron.log"
    raw = ssh(f"tail -{lines} {VPS_BASE}/logs/{log} 2>/dev/null")
    wins = losses = aged = 0
    for line in (raw or "").splitlines():
        ll = line.lower()
        if "win" in ll or "✓" in ll or "resolved yes" in ll or "settled" in ll:
            wins += 1
        elif "loss" in ll or "✗" in ll or "resolved no" in ll:
            losses += 1
        elif "aged_open" in ll or "age-out" in ll:
            aged += 1
    return {"wins": wins, "losses": losses, "aged": aged}


def _pregame_freshness() -> dict:
    today = date.today().strftime("%Y%m%d")
    exists = ssh(f"test -f {VPS_BASE}/logs/pregame_mlb_{today}.json && echo YES || echo NO")
    mtime  = ssh(f"stat -c '%y' {VPS_BASE}/logs/pregame_mlb_{today}.json 2>/dev/null | cut -c1-19")
    size   = ssh(f"wc -c < {VPS_BASE}/logs/pregame_mlb_{today}.json 2>/dev/null || echo 0")
    count  = ssh(
        f"cat {VPS_BASE}/logs/pregame_mlb_{today}.json 2>/dev/null | "
        f"python3 -c \"import json,sys; d=json.load(sys.stdin); "
        f"players=[k for k in d if k not in ('session_id','game_date','game_date_iso','by_player_id')]; "
        f"print(len(d.get('by_player_id',d))-3 if 'session_id' in d else len(d))\" 2>/dev/null || echo 0"
    )
    return {"today": today, "exists": exists.strip() == "YES", "mtime": mtime, "players": count.strip()}


def _git_head() -> str:
    return ssh(f"git -C {VPS_BASE} log --oneline -1")


def _t4_kill_switch() -> bool:
    r = ssh(f"test -f {VPS_BASE}/logs/t4_mlb_kill_switch.flag && echo ARMED || echo clear")
    return "ARMED" in r


def _cron_active_check() -> dict:
    raw = ssh("crontab -l 2>/dev/null")
    checks = {
        "T1_MLB (11:00)":         "run_mlb_paper_trade.py",
        "T2_MLB (19:30)":         "run_t2_mlb_sameday.py",
        "T4_MLB (22:00)":         "run_t4_mlb_live.py",
        "PIPE-06pre (16:30)":     "run_mlb_pregame.py",
        "PIPE-05R (06:30)":       "run_resolve_mlb.py",
        "PIPE-05FX (22:30)":      "generate_mlb_features.py",
        "T3_MLB (*/15)":          "run_t3_mlb_pretip.py",
    }
    result = {}
    for name, script in checks.items():
        active_lines = [l for l in (raw or "").splitlines()
                        if script in l and not l.strip().startswith("#")]
        # Check if T4_MLB_DRY_RUN is still present (should not be)
        dry = any("T4_MLB_DRY_RUN" in l for l in active_lines)
        result[name] = {"active": bool(active_lines), "dry_run": dry}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=1, help="Days of log history to scan")
    args = parser.parse_args()

    today = date.today().isoformat()
    print(f"\n{BOLD}{SEP}{RESET}")
    print(f"{BOLD}  SESSION SELF-ASSESSMENT REPORT — {today}{RESET}")
    print(f"{BOLD}{SEP}{RESET}\n")

    # --- GIT STATE ---
    head = _git_head()
    print(f"{BOLD}VPS GIT HEAD:{RESET} {head}")
    print()

    # --- CRON STATE ---
    print(f"{BOLD}CRON STATE:{RESET}")
    cron = _cron_active_check()
    for name, state in cron.items():
        if state["active"]:
            flag = _color("ACTIVE", "ok")
            if state.get("dry_run"):
                flag += _color(" [DRY-RUN]", "warn")
        else:
            flag = _color("PAUSED", "warn")
        print(f"  {name:<25} {flag}")
    ks = _t4_kill_switch()
    if ks:
        print(_color("  ⚠ T4 MLB KILL SWITCH IS ARMED", "err"))
    print()

    # --- PREGAME FRESHNESS ---
    print(f"{BOLD}PREGAME CONTEXT (MLB):{RESET}")
    pg = _pregame_freshness()
    if pg["exists"]:
        print(_color(f"  pregame_mlb_{pg['today']}.json — {pg['players']} players — {pg['mtime']}", "ok"))
    else:
        print(_color(f"  pregame_mlb_{pg['today']}.json — MISSING", "err"))
    print()

    # --- PORTFOLIO STATE ---
    print(f"{BOLD}PORTFOLIO STATE:{RESET}")
    portfolios = [
        ("paper_portfolio_mlb.json",    "MLB T1/T2"),
        ("paper_portfolio_mlb_t4.json", "MLB T4"),
        ("paper_portfolio.json",        "NBA T1"),
        ("paper_portfolio_t4.json",     "NBA T4"),
    ]
    for path, label in portfolios:
        p = _portfolio_summary(path, label)
        if p.get("missing"):
            print(f"  {label:<12} {_color('not yet created', 'warn')}")
            continue
        if p.get("parse_error"):
            print(f"  {label:<12} {_color('parse error', 'err')}")
            continue
        pnl_str = f"${p['pnl']:+.2f} ({p['pnl_pct']:+.1f}%)"
        pnl_col = "ok" if p['pnl'] >= 0 else "warn"
        dd_col  = "err" if p['drawdown'] > 0.15 else ("warn" if p['drawdown'] > 0.10 else "ok")
        print(
            f"  {label:<12}  BR=${p['bankroll']:.2f}  "
            f"P&L={_color(pnl_str, pnl_col)}  "
            f"Open={p['open_count']} (${p['open_cost']:.2f})  "
            f"Closed={p['closed_count']}  "
            f"DD={_color('{:.1f}%'.format(p['drawdown']*100), dd_col)}"
        )
    print()

    # --- T4 THROUGHPUT ---
    print(f"{BOLD}T4 MLB THROUGHPUT (last session):{RESET}")
    t4 = _t4_throughput(args.days)
    if t4["evaluated"] == 0:
        print(_color("  No T4 evaluation data yet — T4 may not have found live games", "warn"))
    else:
        print(f"  Evaluated: {t4['evaluated']}  |  Fired: {t4['fired']}")
    print()

    # --- RECENT BETS ---
    print(f"{BOLD}RECENT MLB BETS (last 10 fires):{RESET}")
    bets = _log_recent_bets("paper_mlb_cron.log", "T1") + _log_recent_bets("t4_mlb_live_cron.log", "T4")
    if bets:
        for b in bets[-10:]:
            print(f"  {b[:120]}")
    else:
        print(_color("  No bets fired yet", "warn"))
    print()

    # --- RECENT RESOLUTIONS ---
    print(f"{BOLD}RECENT RESOLUTIONS (MLB):{RESET}")
    res = _recent_resolutions("mlb")
    total = res["wins"] + res["losses"]
    if total == 0:
        print(_color("  No resolved positions yet", "warn"))
    else:
        win_rate = res["wins"] / total * 100 if total else 0
        wr_col = "ok" if win_rate >= 50 else "warn"
        print(f"  Wins: {res['wins']}  Losses: {res['losses']}  "
              f"Win rate: {_color(f'{win_rate:.0f}%', wr_col)}  "
              f"Aged-out: {res['aged']}")
    print()

    # --- ERRORS ---
    print(f"{BOLD}CRON ERRORS (last 50 log lines each):{RESET}")
    error_logs = [
        ("paper_mlb_cron.log",     "T1 MLB"),
        ("t2_mlb_cron.log",        "T2 MLB"),
        ("t4_mlb_live_cron.log",   "T4 MLB"),
        ("pregame_mlb_cron.log",   "PIPE-06pre"),
        ("resolve_mlb_cron.log",   "PIPE-05R"),
        ("mlb_feature_refresh.log","PIPE-05FX"),
        ("t3_mlb_cron.log",        "T3 MLB"),
    ]
    any_errors = False
    for log, label in error_logs:
        errs = _log_tail_errors(log)
        if errs:
            any_errors = True
            print(f"  {_color(label, 'err')}:")
            for e in errs[:3]:
                print(f"    {e[:110]}")
    if not any_errors:
        print(_color("  CLEAN — no errors in recent log tails", "ok"))
    print()

    # --- PRIORITY QUEUE REMINDER ---
    print(f"{BOLD}NEXT PRIORITIES:{RESET}")
    print("  1. Check T4 MLB throughput after first live game night")
    print("  2. Watch first MLB T1 bets (11:00 UTC) — verify Kalshi orders land")
    print("  3. Watch PIPE-05R resolution (06:30 UTC) — first MLB bet resolution")
    print("  4. GG-004 (EXP-017): commercial validation requires ≥150 resolved MLB bets")
    print()
    print(f"{BOLD}{SEP}{RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except subprocess.TimeoutExpired:
        print(_color("\nSSH timeout — is the VPS reachable?", "err"))
        sys.exit(1)
