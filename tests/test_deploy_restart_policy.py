"""GG-432: path-scoped, game-aware t4-mlb restart decision (scripts/deploy_restart_policy.py)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import deploy_restart_policy as drp  # noqa: E402

CLOSURE = drp.import_closure(ROOT)
NO_GAMES = {"dates": [{"games": [{"status": {"abstractGameState": "Final", "detailedState": "Final"}}]}]}
LIVE = {"dates": [{"games": [{"status": {"abstractGameState": "Live", "detailedState": "In Progress"},
                              "teams": {"away": {"team": {"name": "NYY"}}, "home": {"team": {"name": "BOS"}}}}]}]}


def test_closure_contains_entry_and_core_imports_only():
    for f in ("src/prediction_market_bot/run_t4_mlb_live.py",
              "src/prediction_market_bot/c5_execution/paper_trader.py",
              "src/prediction_market_bot/c4_risk_engine/risk.py",
              "src/prediction_market_bot/c5_execution/market_type_registry.py"):
        assert f in CLOSURE
    assert "scripts/web_dashboard.py" not in CLOSURE
    assert not any(p.startswith("src/prediction_market_bot/pregame_shadow/") for p in CLOSURE)


def test_closure_matches_runtime_imports():
    code = ("import sys, os, prediction_market_bot.run_t4_mlb_live\n"
            "print('\\n'.join(sorted(os.path.relpath(m.__file__, sys.argv[1]) for k, m in list(sys.modules.items())"
            " if k.startswith('prediction_market_bot') and getattr(m, '__file__', None))))")
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    out = subprocess.run([sys.executable, "-c", code, str(ROOT)], capture_output=True, text=True,
                         env=env, check=True, cwd=ROOT).stdout.split()
    assert set(out) == CLOSURE


def test_docs_or_dashboard_only_push_does_not_restart():
    v, _ = drp.decide(["03_DECISIONS/DECISION_LOG/DECISION_LOG.md", "scripts/web_dashboard.py"], CLOSURE, LIVE)
    assert v == drp.NOT_NEEDED


def test_t4_file_change_no_game_restarts():
    v, why = drp.decide(["src/prediction_market_bot/c5_execution/paper_trader.py"], CLOSURE, NO_GAMES)
    assert v == drp.RESTART and "paper_trader.py" in why


def test_t4_file_change_during_live_game_skips_loudly():
    v, why = drp.decide(["src/prediction_market_bot/c4_risk_engine/risk.py"], CLOSURE, LIVE)
    assert v == drp.SKIP_LIVE and "NYY @ BOS" in why


def test_unknown_schedule_skips():
    v, _ = drp.decide(["src/prediction_market_bot/c4_risk_engine/risk.py"], CLOSURE, None)
    assert v == drp.SKIP_UNKNOWN


def test_unknown_changed_set_is_treated_as_t4_change():
    assert drp.decide(None, CLOSURE, NO_GAMES)[0] == drp.RESTART
    assert drp.decide(None, CLOSURE, LIVE)[0] == drp.SKIP_LIVE
    assert drp.changed_files(ROOT, "0" * 40, "HEAD") is None
    assert drp.changed_files(ROOT, "", "HEAD") is None


def test_live_games_parsing():
    assert drp.live_games(NO_GAMES) == []
    assert drp.live_games({}) == []
    assert len(drp.live_games(LIVE)) == 1


def test_main_writes_outputs(tmp_path, monkeypatch):
    out, summ = tmp_path / "out", tmp_path / "sum"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summ))
    monkeypatch.setattr(drp, "fetch_schedule", lambda *a, **k: LIVE)
    drp.main(["--repo", str(ROOT)])  # no before/after -> unknown changes -> live game -> skip
    assert "restart_t4=false" in out.read_text() and "verdict=skip_live_game" in out.read_text()
    assert "NOT restarted" in summ.read_text()


def test_workflow_gates_t4_restart_on_policy_and_keeps_approval_gate():
    wf = yaml.safe_load((ROOT / ".github/workflows/deploy.yml").read_text())
    jobs = wf["jobs"]
    assert jobs["deploy"]["needs"] == "approval-path-tests"
    gate = " ".join(s.get("run", "") for s in jobs["approval-path-tests"]["steps"])
    assert "tests/test_approval_path_invariants.py tests/test_golden_replay.py" in gate
    steps = {s.get("name"): s for s in jobs["deploy"]["steps"]}
    assert steps["Decide t4-mlb restart (GG-432)"]["id"] == "policy"
    restart = steps["Restart persistent services (T-328/GG-104)"]
    assert restart["env"]["RESTART_T4"] == "${{ steps.policy.outputs.restart_t4 }}"
    assert 'SERVICES="pmbot-web-dashboard"' in restart["run"]
    assert "systemctl restart t4-mlb" not in restart["run"]
