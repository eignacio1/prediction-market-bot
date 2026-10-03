"""Offline tests for scripts/arm_shadow_crons.py (allowlist guard + idempotent crontab merge)."""
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("arm", ROOT / "scripts" / "arm_shadow_crons.py")
arm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(arm)

CONF = (ROOT / "deploy" / "cron_exp037_pregame_shadow.conf").read_text()
EXISTING = "0 9 * * * /opt/x/run_t1_mlb.sh --include-postseason\n*/5 * * * * /opt/x/other.sh\n"


def test_allowlist_accepts_additive_paths():
    ok = [
        "src/prediction_market_bot/pregame_shadow/runner.py",
        "models/nfl_pregame_v1.json",
        "deploy/cron_exp037_pregame_shadow.conf",
        "tests/test_x.py",
        "scripts/run_pregame_shadow.py",
        "scripts/run_pregame_shadow_settle.py",
        "11_MEMORY_HANDOFF/x.md",
    ]
    assert arm.offenders(ok) == []


def test_allowlist_refuses_live_paths_and_lists_them():
    bad = ["src/prediction_market_bot/c5_execution/paper_trader.py", "scripts/run_paper_mlb.py"]
    assert arm.offenders(bad + ["models/a.json"]) == bad


def test_explicit_allow_overrides_single_path_only():
    p = "src/prediction_market_bot/c5_execution/market_type_registry.py"
    assert arm.offenders([p], (p,)) == []
    assert arm.offenders([p, "scripts/other.py"], (p,)) == ["scripts/other.py"]


def test_merge_appends_block_and_preserves_every_other_line():
    out = arm.merge_crontab(EXISTING, CONF)
    for ln in EXISTING.splitlines():
        assert ln in out.splitlines()
    assert out.count(arm.BEGIN) == 1 and out.count(arm.END) == 1


def test_merge_is_idempotent():
    once = arm.merge_crontab(EXISTING, CONF)
    assert arm.merge_crontab(once, CONF) == once


def test_merge_replaces_stale_block_in_place_without_touching_neighbours():
    stale = EXISTING + f"{arm.BEGIN}\n1 1 * * * old\n{arm.END}\n9 9 * * * after\n"
    out = arm.merge_crontab(stale, CONF).splitlines()
    assert "1 1 * * * old" not in out and "9 9 * * * after" in out
    assert out[:2] == EXISTING.splitlines()


def test_dry_commands_have_no_log_redirect_and_are_neutralised():
    lines = arm.cron_lines(CONF)
    assert len(lines) == 4
    for ln in lines:
        d = arm.dry_command(ln)
        assert ">>" not in d
        assert "--dry-run" in d or "mktemp" in d


def test_next_fire():
    now = datetime(2026, 10, 3, 1, 12, tzinfo=timezone.utc)
    assert arm.next_fire("*/10 * * * * x", now).strftime("%H:%M") == "01:20"
    assert arm.next_fire("5 */6 * * * x", now).strftime("%H:%M") == "06:05"
    assert arm.next_fire("30 9 * * * x", now).strftime("%d %H:%M") == "03 09:30"


def test_inert_records_allowed_but_service_reachable_files_still_refused():
    assert arm.offenders(["03_DECISIONS/GOVERNANCE_GAP_LOG.md", "04_EXECUTION/PLAN.md",
                          "exp_output/dashboard_checks/index.after.png"]) == []
    live = ["scripts/web_dashboard.py", "Live Terminal.html",
            "src/prediction_market_bot/c5_execution/market_type_registry.py"]
    assert arm.offenders(live) == live
