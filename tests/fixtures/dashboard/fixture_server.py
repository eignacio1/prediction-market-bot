"""FIXTURE-ONLY dashboard server (T-49.2). Never on the live path.

Builds a throwaway repo-shaped tree in a temp dir — every real top-level entry symlinked
EXCEPT logs/, data/, exp_output/, which are synthetic — and serves scripts/web_dashboard.py
against it. All numbers on the page therefore come from this fixture and are labelled
FIXTURE in tickers/notes. Usage: python tests/fixtures/dashboard/fixture_server.py PORT
"""
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from http.server import HTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SNAP = REPO / "tests" / "fixtures" / "SNAP-2026-07-11-001_t1_regression_anchor_mlb_portfolio.json"


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def build(root: Path, now: datetime) -> None:
    for e in REPO.iterdir():
        if e.name in ("logs", "data", "exp_output", "__pycache__"):
            continue
        (root / e.name).symlink_to(e)
    logs, shadow, pg = root / "logs", root / "data" / "shadow" / "nhl", root / "exp_output" / "PREGAME_SHADOW"
    for d in (logs, shadow, pg / "nfl", pg / "mlb"):
        d.mkdir(parents=True)
    port = json.loads(SNAP.read_text())
    port["last_updated"] = iso(now - timedelta(minutes=3))
    port["note"] = "FIXTURE — derived from tests/fixtures SNAP, not a live ledger"
    (logs / "paper_portfolio_mlb.json").write_text(json.dumps(port))
    t4 = dict(port, open_positions=port["open_positions"][:2], closed_positions=port["closed_positions"][:20],
              rejected_positions=[], last_updated=iso(now - timedelta(minutes=1)))
    (logs / "paper_portfolio_mlb_t4.json").write_text(json.dumps(t4))
    nfl = dict(port, open_positions=[], closed_positions=[], rejected_positions=[],
               last_updated=iso(now - timedelta(days=1)))
    (logs / "paper_portfolio_t1_nfl_game_market.json").write_text(json.dumps(nfl))
    audit = [{"timestamp": iso(now - timedelta(minutes=i)), "event_id": f"EVT-FIXTURE{i}", "component": "C6",
              "event_type": "fixture_event", "severity": "INFO", "session_id": "SES-FIXTURE",
              "payload": {"fixture": True}} for i in range(5)]
    (logs / "audit_mlb.jsonl").write_text("\n".join(json.dumps(r) for r in audit) + "\n")
    cyc = [{"ts": iso(now - timedelta(seconds=45 * i)), "cycle_id": 100 - i, "fixture": True} for i in range(5)]
    (logs / "t4_mlb_cycle_log.jsonl").write_text("\n".join(json.dumps(r) for r in cyc) + "\n")

    def rows(path, sport, mt, band, n):
        with open(path, "w") as f:
            for i in range(n):
                f.write(json.dumps({"ts_utc": iso(now - timedelta(minutes=10 * i)), "sport": sport,
                                    "market_type": mt, "band": band, "market_ticker": f"FIXTURE-{sport}-{i}",
                                    "p_yes": 0.55 + 0.01 * i, "mid": 0.60, "e_net_yes_k007": -0.07 + 0.005 * i,
                                    "e_net_no_k007": -0.02}) + "\n")
    rows(shadow / "NHL_MONEYLINE_T3.jsonl", "NHL", "NHL_MONEYLINE", "T3", 6)
    rows(pg / "nfl" / "NFL_MONEYLINE_T1.jsonl", "NFL", "NFL_MONEYLINE", "T1", 4)
    rows(pg / "mlb" / "MLB_MONEYLINE_T1.jsonl", "MLB", "MLB_MONEYLINE", "T1", 3)


def main() -> None:
    port = int(sys.argv[1])
    sys.path.insert(0, str(REPO / "scripts"))
    sys.path.insert(0, str(REPO / "src"))
    import web_dashboard as wd
    root = Path(tempfile.mkdtemp(prefix="dash_fixture_"))
    try:
        build(root, datetime.now(timezone.utc))
        wd._REPO_ROOT = root
        wd._log_dir = root / "logs"
        srv = HTTPServer(("127.0.0.1", port), wd.DashboardHandler)
        print(f"FIXTURE dashboard http://127.0.0.1:{port} root={root}", flush=True)
        srv.serve_forever()
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
