"""W69.2: NBA game cells flip to SHADOW by themselves on valid regular-season rows; preseason crons retire by date guard."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(name):
    sp = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


af, rm = _load("nba_cell_autoflip"), _load("remove_nba_preseason_cron")
SHA = json.loads((ROOT / "models" / "nba_pregame_v1.json").read_text())["sha256"]
ROW = {"model_sha256": SHA, "p_yes": 0.6, "mid": 0.5, "start_time_source": "espn"}


def _led(tmp, name, rows):
    d = tmp / "led"; d.mkdir(exist_ok=True)
    (d / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return d


def test_noop_before_regular_season(tmp_path):
    d = _led(tmp_path, "NBA_NBA_MONEYLINE_T1", [ROW])
    assert af.main(["--ledger-dir", str(d), "--today", "2026-10-19"]) == 0
    assert not (d / "nba_promotions.jsonl").exists()


def test_flips_only_valid_cells_and_idempotent(tmp_path):
    d = _led(tmp_path, "NBA_NBA_MONEYLINE_T1", [ROW])
    _led(tmp_path, "NBA_NBA_SPREAD_T1", [dict(ROW, excluded_from_judged_n=True), dict(ROW, model_sha256="x")])
    af.main(["--ledger-dir", str(d), "--today", "2026-10-21"])
    af.main(["--ledger-dir", str(d), "--today", "2026-10-22"])
    recs = [json.loads(l) for l in (d / "nba_promotions.jsonl").read_text().splitlines()]
    assert [(r["market_type"], r["band"]) for r in recs] == [("nba_moneyline", "T1_MULTI_DAY")]


def test_registry_applies_records_and_ignores_garbage(tmp_path, monkeypatch):
    from prediction_market_bot.c5_execution import market_type_registry as reg
    p = ROOT / "exp_output" / "PREGAME_SHADOW" / "nba_promotions.jsonl"
    assert not p.exists()
    reg.MARKET_TYPE_REGISTRY  # seeded NOT_IMPLEMENTED
    k = (reg.MarketType.NBA_TEAM_TOTAL, reg.ExecutionBand.T3_PRE_TIP)
    assert reg.MARKET_TYPE_REGISTRY[k].status is reg.CellStatus.NOT_IMPLEMENTED
    from pathlib import Path as P
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('garbage\n{"market_type":"nfl_moneyline","band":"T1_MULTI_DAY","superseding_reference":"EXP-038"}\n'
                 '{"market_type":"nba_team_total","band":"T3_PRE_TIP","superseding_reference":"EXP-038"}\n')
    try:
        reg._apply_nba_game_promotions()
        assert reg.MARKET_TYPE_REGISTRY[k].status is reg.CellStatus.SHADOW
        assert reg.MARKET_TYPE_REGISTRY[(reg.MarketType.NFL_MONEYLINE, reg.ExecutionBand.T1_MULTI_DAY)].citing_decision != "EXP-038"
    finally:
        p.unlink()
        reg.promote_cell_status(*k, reg.CellStatus.NOT_IMPLEMENTED)


CRON = ("0 1 * * * a\n# BEGIN EXP-038 NBA PRESEASON\n57 * * * * c\n# END EXP-038 NBA PRESEASON\n"
        "# BEGIN EXP-039 NBA PLAYER POINTS PRESEASON\n58 * * * * e\n# END EXP-039 NBA PLAYER POINTS PRESEASON\n"
        "# BEGIN W69.2 NBA PRESEASON RETIRE\n5 * * * * r\n# END W69.2 NBA PRESEASON RETIRE\n9 9 * * * d\n")


def test_auto_retire_date_guard_idempotent(tmp_path):
    ct = tmp_path / "ct"; ct.write_text(CRON)
    args = ["--auto", "--crontab-file", str(ct), "--backup-dir", str(tmp_path / "b")]
    rm.main(args + ["--now", "2026-10-21T09:00:00+00:00"])
    assert ct.read_text() == CRON
    rm.main(args + ["--now", "2026-10-21T10:05:00+00:00"])
    assert ct.read_text() == "0 1 * * * a\n9 9 * * * d\n"
    rm.main(args + ["--now", "2026-10-22T10:05:00+00:00"])
    assert ct.read_text() == "0 1 * * * a\n9 9 * * * d\n"


def test_frozen_sha_is_the_models_identity_and_preseason_shaped_rows_are_valid():
    """GG-890: flip scripts hashed the file bytes, the runner writes the artifact's internal sha256 -> no row ever valid."""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from w59_3_nba_flip_check import frozen_model_sha, valid
    from prediction_market_bot.pregame_shadow.nba_model import NBAPregameModel
    sha = frozen_model_sha()
    assert sha == NBAPregameModel.load(ROOT / "models" / "nba_pregame_v1.json").sha256
    row = {"model_sha256": sha, "p_yes": 0.61, "mid": 0.55, "start_time_source": "espn_scoreboard_start_time"}
    assert valid(row, sha)
    assert not valid({**row, "excluded_from_judged_n": True}, sha)
