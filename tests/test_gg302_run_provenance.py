"""GG-302: runtime run-provenance on T1 NFL rows and audit events.

Proves (a) the captured sha is the sha of the tree the code runs from, not a
static epoch marker, (b) a manual run is distinguishable from an attested
scheduled run, (c) the fields reach BOTH the position row and every audit
event (including events emitted by RiskEngine/PaperTrader), (d) a caller that
supplies no provenance gets the literal "UNKNOWN", never a static marker.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

os.environ["BOT_ENV"] = "paper"
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from prediction_market_bot.c4_risk_engine.risk import RiskEngine  # noqa: E402
from prediction_market_bot.c5_execution.paper_trader import PaperTrader  # noqa: E402
from prediction_market_bot.logic_epoch import CURRENT_APPROVAL_COMMIT  # noqa: E402
from prediction_market_bot.run_provenance import (  # noqa: E402
    ProvenanceAuditLogger,
    capture_run_provenance,
)
from prediction_market_bot.run_t1_nfl_game_market import (  # noqa: E402
    StubNFLForecastModel,
    evaluate_and_maybe_trade,
)
from tests.test_run_t1_nfl_game_market import _make_market  # noqa: E402


def _git(cwd, *a):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def test_sha_matches_tree_it_ran_from(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "a")
    sha1 = _git(tmp_path, "rev-parse", "HEAD")
    assert capture_run_provenance(code_root=tmp_path, env={})["runtime_git_sha"] == sha1
    _git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "b")
    sha2 = _git(tmp_path, "rev-parse", "HEAD")
    assert sha2 != sha1
    assert capture_run_provenance(code_root=tmp_path, env={})["runtime_git_sha"] == sha2


def test_sha_is_not_the_static_epoch_marker():
    prov = capture_run_provenance(env={})
    assert prov["runtime_git_sha"] == _git(_REPO_ROOT, "rev-parse", "HEAD")


def test_non_git_tree_is_unknown_not_a_marker(tmp_path):
    prov = capture_run_provenance(code_root=tmp_path, env={})
    assert prov["runtime_git_sha"] == "UNKNOWN"
    assert prov["runtime_git_sha"] != CURRENT_APPROVAL_COMMIT


def test_manual_distinguishable_from_scheduled():
    manual = capture_run_provenance(env={})
    unattested_junk = capture_run_provenance(env={"PMBOT_RUN_TRIGGER": "yolo"})
    cron = capture_run_provenance(env={"PMBOT_RUN_TRIGGER": "cron"})
    assert manual["run_trigger"] == "manual" and manual["run_trigger_attested"] is False
    assert unattested_junk["run_trigger"] == "manual"
    assert cron["run_trigger"] == "cron" and cron["run_trigger_attested"] is True
    assert manual["run_id"] != cron["run_id"]


def _run(tmp_path, prov):
    audit = ProvenanceAuditLogger(tmp_path / "audit.jsonl", prov)
    engine = RiskEngine(logger=audit, snapshot_id="SNAP-TEST", bankroll=1000.0, min_bet_usd=1.0)
    trader = PaperTrader(portfolio_path=tmp_path / "pf.json", logger=audit, kalshi_client=None)
    outcome = evaluate_and_maybe_trade(
        _make_market(),
        snapshot_unparsed_count=0, model=StubNFLForecastModel(fixed_p=0.65),
        engine=engine, trader=trader, audit=audit, run_provenance=prov,
    )
    events = [json.loads(l) for l in (tmp_path / "audit.jsonl").read_text().splitlines()]
    positions = json.loads((tmp_path / "pf.json").read_text())["open_positions"]
    return outcome, events, positions


def test_rows_and_every_audit_event_carry_provenance(tmp_path):
    prov = capture_run_provenance(run_id="RUN-TEST", env={"PMBOT_RUN_TRIGGER": "cron"})
    outcome, events, positions = _run(tmp_path, prov)
    assert outcome == "OPENED"
    assert len(positions) == 1
    p = positions[0]
    assert p["runtime_git_sha"] == prov["runtime_git_sha"] != "UNKNOWN"
    assert p["run_trigger"] == "cron" and p["run_id"] == "RUN-TEST"
    assert p["run_host"] == prov["run_host"]
    assert p["approval_commit"] == CURRENT_APPROVAL_COMMIT  # untouched epoch marker
    assert events and all(e["payload"]["run_provenance"]["run_id"] == "RUN-TEST" for e in events)
    # events emitted by RiskEngine (C4) and PaperTrader (C5-PAPER) -- components
    # that know nothing about provenance -- are stamped by the logger.
    assert {e["component"] for e in events} >= {"C4", "C5-PAPER"}


def test_absent_provenance_is_unknown_not_static(tmp_path):
    audit = ProvenanceAuditLogger(tmp_path / "a.jsonl", {})
    engine = RiskEngine(logger=audit, snapshot_id="S", bankroll=1000.0, min_bet_usd=1.0)
    trader = PaperTrader(portfolio_path=tmp_path / "pf.json", logger=audit, kalshi_client=None)
    evaluate_and_maybe_trade(
        _make_market(),
        snapshot_unparsed_count=0, model=StubNFLForecastModel(fixed_p=0.65),
        engine=engine, trader=trader, audit=audit,
    )
    p = json.loads((tmp_path / "pf.json").read_text())["open_positions"][0]
    assert p["runtime_git_sha"] == p["run_trigger"] == p["run_id"] == p["run_host"] == "UNKNOWN"
