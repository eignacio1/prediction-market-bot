#!/usr/bin/env python3
"""READ-ONLY (W130.5 Part C): STATE_OF_THE_BOT - one page of what actually runs, measured on the box.

Every number is read from the box's own files, logs or read-only demo GETs at run time; nothing is written from memory. Each
section carries the source it was read from and the read time. A section that cannot be read says so and why: it is never
filled in.

Modes
  (default)        measure on the box, print the markdown page to stdout (the allowlisted box task `state_of_the_bot_read`).
  --ingest         copy the newest successful box result (BOX_TASKS/results/*_state_of_the_bot_read.md) into
                   04_EXECUTION/STATE_OF_THE_BOT.md, dated by the box's own `ran` time. Reads a file, writes one file.
Sections: header; per sport (arms logging 24h/7d, demo orders / fills / settled / P&L per filled bet, D6); installs pending;
last wave's verdicts; every red signal (silent arms, SURFACE BUDGET, health run, deploy truth).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE))

SPORTS = ("NBA", "NFL", "NHL", "MLB")
OUT_REL = "04_EXECUTION/STATE_OF_THE_BOT.md"
RES_DIR = "04_EXECUTION/BOX_TASKS/results"
FILLS_BUDGET_S = 240
PY = [sys.executable]

# arm key (silent_arms.SPECS) -> (sport, ledger globs relative to the repo whose rows it counts). Exact names, never a sport
# prefix glob (GG-892). A key with no entry is still reported (status from silent_arms) with rows "n/a".
ARM_SPORT = {
    "mlb_shadow": "MLB", "t1_mlb": "MLB", "t4_mlb": "MLB",
    "nfl_shadow": "NFL", "nfl_qb_challenger": "NFL", "nfl_passyds_snap": "NFL",
    "nhl_shadow": "NHL", "nhl_inplay_shadow": "NHL",
    "nba_engine_v1": "NBA", "nba_engine_v2": "NBA", "nba_engine_v3": "NBA", "nba_preseason_shadow": "NBA", "nba_shadow": "NBA",
    "nba_player_points_shadow": "NBA", "nba_player_points_minutes_shadow": "NBA", "nba_props_exp047": "NBA",
    "nba_props_exp047_c1": "NBA", "nba_props_exp047_c2": "NBA", "nba_props_exp047_s": "NBA", "nba_combo_shadow": "NBA",
    "ride_board": "ALL", "arm_orders": "ALL",
}
ARM_GLOBS = {
    "mlb_shadow": ["exp_output/PREGAME_SHADOW/MLB_MLB_*.jsonl"],
    "nfl_shadow": ["exp_output/PREGAME_SHADOW/NFL_NFL_*.jsonl"],
    "nfl_qb_challenger": ["exp_output/PREGAME_SHADOW_NFLQB/NFLQB_*.jsonl"],
    "nfl_passyds_snap": ["exp_output/PREGAME_SHADOW_PASSYDS/snap_*.jsonl"],
    "nhl_shadow": ["data/shadow/nhl/NHL_*.jsonl"],
    "nba_engine_v1": ["exp_output/NBA_ENGINE_LIVE/rows.jsonl"],
    "nba_engine_v2": ["exp_output/NBA_ENGINE_LIVE_V2/rows.jsonl"],
    "nba_engine_v3": ["exp_output/NBA_ENGINE_LIVE_V3/rows.jsonl"],
    "nba_preseason_shadow": ["exp_output/PREGAME_SHADOW_PRESEASON/NBA_NBA_*.jsonl"],
    "nba_shadow": ["exp_output/PREGAME_SHADOW/NBA_NBA_*.jsonl"],
    "nba_player_points_shadow": ["exp_output/PREGAME_SHADOW/NBA_NBA_PLAYER_POINTS_*.jsonl"],
    "nba_player_points_minutes_shadow": ["exp_output/PREGAME_SHADOW_EXP040/NBAMIN_*.jsonl"],
    "nba_props_exp047": ["exp_output/PREGAME_SHADOW_EXP047/NBAENG_*.jsonl"],
    "nba_props_exp047_c1": ["exp_output/PREGAME_SHADOW_EXP047_C1/NBAENG_*.jsonl"],
    "nba_props_exp047_c2": ["exp_output/PREGAME_SHADOW_EXP047_C2/NBAENG_*.jsonl"],
    "nba_props_exp047_s": ["exp_output/PREGAME_SHADOW_EXP047_S/NBAENG_*.jsonl"],
    "nba_combo_shadow": ["exp_output/COMBO_SHADOW/*.jsonl"],
    "nhl_inplay_shadow": ["data/shadow/nhl_inplay/*.jsonl"],
    "ride_board": ["logs/ride_board/decisions.jsonl"],
}
TS_KEYS = ("ts_utc", "ts", "timestamp", "logged_at")


def _parse(v) -> Optional[datetime]:
    if not isinstance(v, str):
        return None
    try:
        t = datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def count_rows(files: Iterable[Path], now: datetime) -> dict:
    """Streamed (one line in memory): rows with a timestamp in the last 24 h / 7 d, and the newest. Files whose mtime is older than
    7 d cannot hold a newer row and are skipped unread."""
    c24, c7, last = 0, 0, None
    lo24, lo7 = now - timedelta(hours=24), now - timedelta(days=7)
    for p in files:
        try:
            if datetime.fromtimestamp(p.stat().st_mtime, timezone.utc) < lo7:
                continue
            fh = p.open("r", encoding="utf-8", errors="ignore")
        except OSError:
            continue
        with fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(r, dict):
                    continue
                t = next((x for x in (_parse(r.get(k)) for k in TS_KEYS) if x), None)
                if t is None or t < lo7:
                    continue
                c7 += 1
                c24 += t >= lo24
                last = t if last is None or t > last else last
    return {"rows_24h": c24, "rows_7d": c7, "last_row": last.strftime("%Y-%m-%dT%H:%MZ") if last else None}


def arm_section(repo: Path, now: datetime) -> list[dict]:
    from prediction_market_bot.pregame_shadow import silent_arms as sa
    res = sa.compute(repo, now=now)
    out = []
    for a in res["arms"]:
        files = [Path(f) for pat in ARM_GLOBS.get(a["key"], []) for f in sorted(glob.glob(str(repo / pat)))]
        cnt = count_rows(files, now) if a["key"] in ARM_GLOBS else {"rows_24h": None, "rows_7d": None, "last_row": a.get("last_row")}
        out.append({"key": a["key"], "name": a["name"], "sport": ARM_SPORT.get(a["key"], "?"), "status": a["status"],
                    "games_in_window": a.get("games_in_window"), "text": a["text"], **cnt})
    return out


ORDER_KEYS = ("event", "ts", "arm", "sport", "reason", "order_id", "ticker", "ok", "side", "entry_price")
POST_EPOCH = datetime(2026, 11, 6, 1, 3, 42, tzinfo=timezone.utc)


def order_counts(path: Path, now: datetime) -> dict:
    """Stream the arm-order log once, counters only: per sport and arm, orders / would / skips / refused in 24 h, 7 d and since the
    data epoch; plus the placed order ids (post-epoch, ok) for the fills lookup."""
    per: dict = defaultdict(Counter)
    skip_reasons: dict = defaultdict(Counter)
    placed: list = []
    lo24, lo7 = now - timedelta(hours=24), now - timedelta(days=7)
    ev = {"arm_order": "orders", "arm_would_order": "would", "arm_skip": "skips"}
    total = 0
    try:
        fh = path.open("r", encoding="utf-8", errors="ignore")
    except OSError as e:
        return {"error": f"{type(e).__name__}: {path}"}
    with fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            k = ev.get(r.get("event")) if isinstance(r, dict) else None
            t = _parse(r.get("ts")) if k else None
            if k is None or t is None:
                continue
            total += 1
            if k == "orders" and not r.get("ok"):
                k = "refused"
            key = (str(r.get("sport") or "?").upper(), str(r.get("arm")))
            if t >= POST_EPOCH:
                per[key][k + "_epoch"] += 1
                if k == "skips":
                    skip_reasons[key][str(r.get("reason"))] += 1
                if k == "orders" and r.get("order_id"):
                    placed.append({kk: r.get(kk) for kk in ORDER_KEYS})
            if t >= lo7:
                per[key][k + "_7d"] += 1
            if t >= lo24:
                per[key][k + "_24h"] += 1
    return {"rows": total, "per": {f"{s}|{a}": dict(c) for (s, a), c in per.items()},
            "skip_reasons": {f"{s}|{a}": dict(c.most_common(3)) for (s, a), c in skip_reasons.items()}, "placed": placed}


def fills_by_sport(placed: list, fills_for: Optional[Callable]) -> dict:
    """Per sport, post-epoch placed demo orders: filled, settled, win rate and P&L per filled contract before fees (settle minus
    price). Only orders the (budgeted) lookup answered count; `looked_up` says how many that was."""
    out: dict = defaultdict(lambda: {"orders": 0, "looked_up": 0, "filled": 0, "settled": 0, "pnl": []})
    for r in placed:
        if r.get("side") != "yes":
            continue
        c = out[str(r.get("sport") or "?").upper()]
        c["orders"] += 1
        f = fills_for(r["order_id"], r.get("ticker")) if fills_for else None
        if f is None or f.get("status") == "unretrievable":
            continue
        c["looked_up"] += 1
        if (f.get("fills") or 0) > 0:
            c["filled"] += 1
            if f.get("settled") and f.get("won") is not None:
                c["settled"] += 1
                price = f.get("price") if f.get("price") is not None else r.get("entry_price")
                if price is not None:
                    c["pnl"].append((1.0 - float(price)) if f["won"] else -float(price))
    return {s: {**{k: v for k, v in c.items() if k != "pnl"},
                "pnl_per_filled_before_fees": (sum(c["pnl"]) / len(c["pnl"])) if c["pnl"] else None, "n_pnl": len(c["pnl"])}
            for s, c in out.items()}


def sh(cmd: str, timeout: int = 90) -> str:
    try:
        p = subprocess.run(cmd, shell=True, cwd=str(REPO), capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "PYTHONPATH": f"{REPO}/src:{REPO}"})
        return (p.stdout + (("\n" + p.stderr) if p.returncode else "")).strip()
    except subprocess.TimeoutExpired:
        return f"TIMEOUT after {timeout}s"
    except Exception as e:  # noqa: BLE001
        return f"{type(e).__name__}: {e}"


def installs_pending(repo: Path) -> list[dict]:
    """Registry components with status = paused: built, registered, not running. Each names the install task that starts it."""
    import tomllib
    reg = tomllib.loads((repo / "02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml").read_text(encoding="utf-8"))
    return [{"key": c["key"], "purpose": c.get("purpose", ""), "alarm": c.get("alarm", "")}
            for c in reg.get("component", []) if c.get("status") == "paused"]


def red_signals(arms: list[dict], health: str, budget: str, deploy: str, d6_err: Optional[str]) -> list[str]:
    out = []
    for a in arms:
        if a["status"] in ("silent", "unknown"):
            out.append(f"arm {a['status'].upper()}: {a['text']}")
    for line in health.splitlines():
        if line.startswith(("[FAIL]", "[WARN]")):
            out.append("health: " + line)
    for line in (budget + "\n" + deploy).splitlines():
        if re.search(r"\b(RED|ALARM|SILENT|UNKNOWN)\b", line):
            out.append("box: " + line.strip()[:240])
    if d6_err:
        out.append("D6 not computed: " + d6_err)
    return out


def verdicts(repo: Path) -> str:
    return sh(f"{sys.executable} scripts/first_look_verdicts_read.py", 60)


def fmt(v, nd=3):
    return "n/a" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))


def build(repo: Path = REPO, now: Optional[datetime] = None) -> str:
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    head = sh("git log -1 --format='%h %cI %s'", 20)
    arms = arm_section(repo, now)
    import arm_orders_read as aor
    import d6_read
    oc = order_counts(aor.LOG, now)
    fills_for, note, state, d6out, d6_err = None, "", None, None, None
    try:
        rows = d6_read.load_rows_slim(aor.LOG)
        fills_for, note = aor.make_fills_for(rows)
        if fills_for is not None:
            fills_for, state = d6_read.budgeted(fills_for, FILLS_BUDGET_S)
        from prediction_market_bot.decision_trees import coverage
        ledger = coverage.ledger_evidence(__import__("itertools").chain(
            d6_read.ledger_rows(now - timedelta(days=d6_read.LEDGER_DAYS)), d6_read.passyds_t1_rows(now - timedelta(days=d6_read.LEDGER_DAYS))))
        d6out = d6_read.build(rows, fills_for, note, str(aor.LOG), now, ledger)
        del rows
    except Exception as e:  # noqa: BLE001 - one broken section never blanks the page
        d6_err = f"{type(e).__name__}: {str(e)[:200]}"
    fills = fills_by_sport(oc.get("placed", []), fills_for) if "error" not in oc else {}
    health = sh("awk '/^=== VPS Health Check/{buf=\"\"} {buf=buf $0 \"\\n\"} END{printf \"%s\", buf}' logs/health.log | grep -E '^(=== |\\[FAIL\\]|\\[WARN\\])'", 20)
    budget = sh(f"{sys.executable} scripts/runtime_registry.py live --refresh", 90)
    deploy = sh("python3 scripts/ops/deploy_truth.py check", 60)
    L = [f"# STATE OF THE BOT - read {stamp}", "",
         f"Measured by `scripts/state_of_the_bot.py` (read-only) on host `{__import__('socket').gethostname()}` (the box when run by the box task). Checkout: `{head}`. No line below is written from memory;",
         "a section that could not be read says so. Data epoch for orders: 2026-11-06T01:03:42Z.", ""]
    d6s = (d6out or {}).get("d6", {}).get("by_sport", {})
    for sp in SPORTS + ("ALL",):
        L += [f"## {sp if sp != 'ALL' else 'Cross-sport arms (ride board, arm-order router)'}", "", "**Arms logging** (rows with a timestamp; silent-arms status)", "",
              "| arm | status | games in window | rows 24h | rows 7d | last row |", "|---|---|---|---|---|---|"]
        for a in [x for x in arms if x["sport"] == sp]:
            L.append(f"| {a['key']} | {a['status']} | {fmt(a['games_in_window'])} | {fmt(a['rows_24h'])} | {fmt(a['rows_7d'])} | {fmt(a['last_row'])} |")
        L += ["", "**Demo orders** (arm-order log, post-epoch, YES side for fills)", ""]
        per = {k.split("|", 1)[1]: v for k, v in oc.get("per", {}).items() if k.split("|", 1)[0] == sp}
        if "error" in oc:
            L.append(f"- not read: {oc['error']}")
        elif not per:
            L.append("- no arm-order rows for this sport")
        else:
            L += ["| arm | orders 24h/7d/epoch | would 7d | skips 7d | refused epoch |", "|---|---|---|---|---|"]
            for arm, v in sorted(per.items()):
                L.append(f"| {arm} | {v.get('orders_24h', 0)}/{v.get('orders_7d', 0)}/{v.get('orders_epoch', 0)} | {v.get('would_7d', 0)} | "
                         f"{v.get('skips_7d', 0)} | {v.get('refused_epoch', 0)} |")
        f = fills.get(sp)
        if f:
            L.append(f"- fills: {f['filled']} filled of {f['looked_up']} looked up ({f['orders']} placed YES-side); settled {f['settled']}; "
                     f"P&L per filled contract before fees {fmt(f['pnl_per_filled_before_fees'])} on {f['n_pnl']} settled")
        d = d6s.get(sp.lower())  # d6_read keys sports lowercase
        L.append(f"- **D6** {d['wired']}/{d['registered']} cells wired through 7 layers (cells per layer {'/'.join(map(str, d['per_layer']))})"
                 if d else f"- D6: not computed ({d6_err or 'sport not in read'})")
        L.append("")
    if state is not None:
        L.append(f"Fills lookup: {state['calls']} read-only GETs" + (" - BUDGET EXHAUSTED, fills may be understated" if state["exhausted"] else "") + ".")
    if d6out:
        L.append(f"D6 overall: **{d6out['d6']['wired']}/{d6out['d6']['registered']}** read {d6out['read_utc']} "
                 f"({d6out['arm_order_rows']} arm-order rows, {d6out['ledger_rows']} ledger rows).")
    L.append("")
    inst = installs_pending(repo)
    L += ["## Installs pending (registry status = paused: built, registered, not running)", ""]
    L += [f"- `{c['key']}` - {c['purpose'][:160]}" for c in inst] or ["- none"]
    L += ["", "## Last wave's verdicts (first_look_verdicts_read.py, newest engine JSON)", "", "~~~", verdicts(repo)[:3000] or "(no output)", "~~~", ""]
    reds = red_signals(arms, health, budget, deploy, d6_err)
    L += ["## Red signals", ""] + ([f"- {r}" for r in reds] or ["- none read red"]) + ["",
          "## Raw health / budget / deploy reads", "", "~~~", health[:1500], "", budget[:2500], "", deploy[:2000], "~~~"]
    return "\n".join(L) + "\n"


RAN_RE = re.compile(r"^- ran: (\S+)", re.M)
EXIT_RE = re.compile(r"^- exit code: (\d+)", re.M)


def newest_result(repo: Path) -> Optional[tuple[str, str, str]]:
    """(path, ran, markdown page) of the newest successful box state_of_the_bot_read, by the box's own `ran` time."""
    best = None
    for f in glob.glob(str(repo / RES_DIR / "*_state_of_the_bot_read.md")):
        t = Path(f).read_text(encoding="utf-8", errors="ignore")
        ran, ex = RAN_RE.search(t), EXIT_RE.search(t)
        m = re.search(r"(# STATE OF THE BOT.*)", t, re.S)
        if m:   # the page ends at the box's [stderr] marker or the closing fence, whichever comes first (inner blocks use ~~~)
            body = re.split(r"\n\[stderr\]|\n```\s*$", m.group(1))[0]
            m = re.match(r"(?s)(.*)", body)
        if ran and ex and ex.group(1) == "0" and m and (best is None or ran.group(1) > best[1]):
            best = (str(Path(f).relative_to(repo)), ran.group(1), m.group(1))
    return best


def ingest(repo: Path = REPO) -> int:
    got = newest_result(repo)
    if got is None:
        print("no successful box state_of_the_bot_read result to ingest", file=sys.stderr)
        return 2
    rel, ran, page = got
    (repo / OUT_REL).write_text(f"<!-- generated by scripts/state_of_the_bot.py --ingest from {rel} (box ran {ran}) -->\n{page}\n", encoding="utf-8")
    print(f"wrote {OUT_REL} from {rel} (box ran {ran})")
    return 0


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ingest", action="store_true")
    a = ap.parse_args(argv)
    if a.ingest:
        return ingest()
    print(build())
    return 0


if __name__ == "__main__":
    sys.exit(main())
