"""W130.5: every live RUNTIME_REGISTRY writer of forecast or order rows has a silent-arms probe (GG-163 class)."""
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src")]

from prediction_market_bot.pregame_shadow import silent_arms as sa  # noqa: E402

REG = tomllib.loads((ROOT / "02_ARCHITECTURE_DESIGN" / "RUNTIME_REGISTRY.toml").read_text())["component"]


def _live():
    return [c for c in REG if c.get("status") == "live"]


def test_every_live_component_is_classified():
    bad = [c["key"] for c in _live() if not sa.classify_component(c["key"], c.get("writes"))]
    assert not bad, "live registry components with no silent-arms classification (add a probe or an exempt reason): %s" % bad


def test_every_probe_a_live_writer_names_exists_in_specs_and_loader(tmp_path):
    keys = {i.spec.key for i in sa.load_inputs(tmp_path, tmp_path / "logs")}
    missing = []
    for c in _live():
        for t in sa.classify_component(c["key"], c.get("writes")):
            kind, val = sa.WRITER_COVERAGE[t]
            if kind == "probe":
                missing += [(c["key"][:60], k) for k in val if k not in sa.SPECS or k not in keys]
    assert not missing, missing


def test_exempt_entries_carry_a_reason():
    assert all(v[0] in ("probe", "exempt") and v[1] for v in sa.WRITER_COVERAGE.values())


def test_props_writer_is_probed_by_all_four_arms():
    c = [x for x in _live() if "run_nba_engine_props_shadow.py" in x["key"]]
    assert c, "EXP-047 props cron missing from the registry"
    probes = {k for t in sa.classify_component(c[0]["key"], c[0].get("writes")) for k in sa.WRITER_COVERAGE[t][1]}
    assert {"nba_props_exp047", "nba_props_exp047_c2", "nba_props_exp047_s"} <= probes


def test_unprobed_live_writer_would_fail():
    assert sa.classify_component("cron|1 * * * *|scripts/brand_new_forecaster.py", ["exp_output/X/rows.jsonl"]) == []


def test_paused_writers_are_idle_not_silent_until_installed(tmp_path):
    from datetime import datetime, timezone
    now = datetime(2026, 11, 26, 3, 0, tzinfo=timezone.utc)
    res = {a["key"]: a for a in sa.silent_arms(sa.load_inputs(tmp_path, tmp_path / "logs", now), now)["arms"]}
    assert res["nba_combo_shadow"]["status"] == "idle" and res["nhl_inplay_shadow"]["status"] == "idle"
    assert res["nba_props_exp047_c1"]["status"] == "idle"
