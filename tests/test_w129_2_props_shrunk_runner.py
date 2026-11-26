"""W129.2 Part C: PM_PROPS_SHRUNK is a default-on, shadow-only switch with its own ledger; C2 and v1 are untouched by it."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.joinpath("scripts", "run_nba_engine_props_shadow.py").read_text()


def test_shrunk_default_on_with_env_off_switch():
    m = re.search(r'os\.environ\.get\("PM_PROPS_SHRUNK", "(\w+)"\)\.lower\(\) (!=|==) "(\w+)"', SRC)
    assert m, "PM_PROPS_SHRUNK switch not found"
    default, op, token = m.groups()

    def on(env):
        v = (env if env is not None else default).lower()
        return (v != token) if op == "!=" else (v == token)
    assert on(None) and on("on") and not on("off") and not on("OFF")


def test_shrunk_branch_is_after_c2_has_its_own_ledger_and_no_orders():
    i_c2, i_s = SRC.index("C2 ledger_dir"), SRC.index("PM_PROPS_SHRUNK")
    assert i_s > i_c2
    tail = SRC[i_s:]
    assert "PREGAME_SHADOW_EXP047_S" in tail and "on_row=None" in tail
    assert "PREGAME_SHADOW_EXP047_C2" not in tail


def test_frozen_prev_table_is_2025_26_and_has_the_fields_the_model_reads():
    d = json.loads(ROOT.joinpath("data", "reference", "nba_prev_season_2025_26.json").read_text())
    assert d["season"] == "2025-26" and d["data_through"] == "2026-07-31" and d["games"] == 1230
    t = next(iter(d["players"].values()))
    assert {"min", "games", "points", "rebounds", "assists", "threes"} <= set(t)


def test_shrunk_runner_inputs_do_not_change_c2_or_v1_output():
    """Byte-identity: the shrunk branch only reads games/pl; the C2 and v1 forecasters take no shrunk input."""
    from prediction_market_bot.pregame_shadow import nba_engine_props_c2_forecaster as C2
    from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F
    import inspect
    assert "prev" not in inspect.signature(C2.NBAEnginePropsC2.__init__).parameters
    assert "prev" not in inspect.signature(F.NBAEngineProps.__init__).parameters
    assert C2.MODEL_ID == "nba_engine_v2_props_c2_w126_2"
