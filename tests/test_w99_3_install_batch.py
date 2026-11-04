"""W99.3 / B-036: the batch install gate. The 11-03 red set passes; the same set plus a healthcheck fault, another arm's
silence, or a foreign NOT INSTALLED blocks; a partial failure stops the batch and names the step; order is pinned."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import install_batch_w99 as ib  # noqa: E402
import runtime_registry as rr  # noqa: E402
from prediction_market_bot.pregame_shadow.silent_arms import SPECS  # noqa: E402

REFRESH = ("33 12 * * * cd /x && python -m prediction_market_bot.c1_signal_ingestion.nba_current_season "
           ">> logs/nba_engine_live_cron.log 2>&1")
RUN = ("2,12,22,32,42,52 16-23,0-4 * * * cd /x && sh -c 'python -m prediction_market_bot.nba_engine.live --raw r --no-refresh; "
       "python -m prediction_market_bot.nba_engine.live_v2 --raw r --no-refresh' >> logs/nba_engine_live_cron.log 2>&1")
V3 = ("3,13,23,33,43,53 16-23,0-4 * * * cd /x && python -m prediction_market_bot.nba_engine.live_v3 --raw exp_output/NBA_EVENTS/raw "
      "--no-refresh >> logs/nba_engine_live_cron.log 2>&1")
PICKS = "37 5,22 * * * cd /x && python scripts/build_picks_sheet.py >> logs/picks_sheet_cron.log 2>&1"
T3 = "9,19,29,39,49,59 * * * * cd $PROJ && $PYTHON scripts/run_nba_pregame_shadow.py --bands T3 >> logs/nba.log 2>&1"
OTHER = "0 1 * * * cd $PROJ && $PYTHON scripts/other_job.py"
CONF = "\n".join(["SHELL=/bin/bash", REFRESH, RUN, V3, PICKS, T3, OTHER]) + "\n"
V3_KEY = "cron|3,13,23,33,43,53 16-23,0-4 * * *|--no-refresh --raw exp_output/NBA_EVENTS/raw"
PICKS_KEY = "cron|37 5,22 * * *|scripts/build_picks_sheet.py"

# the exact 11-03 06:35Z set (20261103T063449Z_w_budget_read.md)
RED_1103 = [
    "NOT INSTALLED " + V3_KEY,
    "NOT INSTALLED " + PICKS_KEY,
    "SILENT ARM NBA engine v3 (EXP-044c): NBA engine v3 (EXP-044c) is SILENT: 15 game(s) started in the last 12h but no rows "
    "found (looked back 12h) (last row none found)",
]
EV_1103 = {"budget": "RED", "head": "9372f492", "as_of": "2026-11-03T06:35:10Z", "reasons": RED_1103}
GREEN = {"budget": "GREEN", "head": "h", "as_of": "t"}


def _reg():
    return [{"key": rr._cron_key(l)[0], "kind": "cron", "status": "live"} for l in (REFRESH, RUN, V3, PICKS, T3, OTHER)]


class Box:
    def __init__(self, text, fail_write_on=None):
        self.text, self.writes, self.fail_on = text, 0, fail_write_on

    def read(self):
        return self.text

    def write(self, t):
        self.writes += 1
        if self.fail_on == self.writes:
            return  # a write that silently does not land -> the step's readback verify must fail
        self.text = t


# 11-03 box state: refresh+runner installed, T3 unwrapped, v3 + picks absent
BOX_1103 = "\n".join(["# BEGIN W95.1 NBA ENGINE LINES", REFRESH, RUN, "# END W95.1 NBA ENGINE LINES", T3, OTHER]) + "\n"


def _pending():
    return ib.pending(BOX_1103, CONF, _reg())


def test_keys_match_the_11_03_reds():
    p = _pending()
    assert p["nba_engine_v3"] == [V3_KEY] and p["picks_builder"] == [PICKS_KEY] and p["nba_events_refresh"] == []


def test_arm_names_are_real_spec_names():
    names = {s.name for s in SPECS.values()}
    for _step, _mod, arms in ib.STEPS:
        assert set(arms) <= names


def test_1103_red_set_passes():
    blocking, exempt = ib.gate_batch(EV_1103, _pending())
    assert blocking == [] and sorted(exempt) == sorted(RED_1103)


def test_plus_healthcheck_fault_blocks():
    ev = dict(EV_1103, reasons=RED_1103 + ["healthcheck: UNHEALTHY: 2 faults"])
    blocking, _ = ib.gate_batch(ev, _pending())
    assert blocking == ["healthcheck: UNHEALTHY: 2 faults"]


def test_plus_other_arms_silence_blocks():
    other = "SILENT ARM NHL shadow: NHL shadow is SILENT: 3 game(s) started"
    nbap = "SILENT ARM NBA player points shadow: NBA player points shadow is SILENT: 4 game(s)"
    blocking, _ = ib.gate_batch(dict(EV_1103, reasons=RED_1103 + [other, nbap]), _pending())
    assert blocking == [other, nbap]


def test_foreign_not_installed_blocks_and_prefix_lookalike_does_not_pass():
    foreign = "NOT INSTALLED cron|0 3 * * *|scripts/some_other_job.py"
    lookalike = "SILENT ARM NBA engine v3 (EXP-044c) extra: x"   # no ': ' right after the exact name
    blocking, _ = ib.gate_batch(dict(EV_1103, reasons=RED_1103 + [foreign, lookalike]), _pending())
    assert blocking == [foreign, lookalike]


def test_arm_exempt_only_when_its_step_has_a_line_to_install():
    # v3 already installed -> its step installs nothing -> a v3 silence is a real problem, not batch state
    box = BOX_1103.replace("# END W95.1 NBA ENGINE LINES", V3 + "\n# END W95.1 NBA ENGINE LINES")
    todo = ib.pending(box, CONF, _reg())
    assert todo["nba_engine_v3"] == []
    blocking, _ = ib.gate_batch(dict(EV_1103, reasons=[RED_1103[2]]), todo)
    assert blocking == [RED_1103[2]]


def test_red_with_no_reasons_blocks_and_green_passes():
    assert ib.gate_batch({"budget": "RED", "reasons": []}, _pending())[0]
    assert ib.gate_batch(GREEN, _pending()) == ([], [])


def _run(box, ev):
    return ib.install(live_fn=lambda: ev, read=box.read, write=box.write, backup=lambda c: Path("/tmp/bak"),
                      conf_text=CONF, reg=_reg())


def test_full_batch_on_the_1103_state_installs_in_order(capsys):
    box = Box(BOX_1103)
    assert _run(box, EV_1103) == 0
    out = capsys.readouterr().out
    order = [out.index("== step %s ==" % s) for s in ("t3_lock", "nba_engine_v3", "picks_builder")]
    assert order == sorted(order)
    assert "BATCH COMPLETE: t3_lock, nba_events_refresh, nba_engine_v3, picks_builder" in out
    lines = box.text.splitlines()
    assert V3 in lines and PICKS in lines and OTHER in lines and REFRESH in lines
    assert all("flock -n 9" in l for l in lines if "run_nba_pregame_shadow.py" in l)


def test_blocked_batch_still_applies_t3_only(capsys):
    box = Box(BOX_1103)
    ev = dict(EV_1103, reasons=RED_1103 + ["healthcheck: UNHEALTHY: 1 faults"])
    assert _run(box, ev) == 0
    out = capsys.readouterr().out
    assert "REFUSED" in out and "healthcheck: UNHEALTHY: 1 faults" in out and "were NOT attempted" in out
    assert V3 not in box.text and PICKS not in box.text and "flock -n 9" in box.text


def test_partial_failure_stops_and_names_the_step(capsys):
    box = Box(BOX_1103, fail_write_on=2)   # write 1 = T3 (lands), write 2 = first gated install that writes (v3) fails verify
    assert _run(box, EV_1103) == 1
    out = capsys.readouterr().out
    assert "BATCH STOPPED at step 'nba_engine_v3'" in out
    assert "Completed before it: t3_lock, nba_events_refresh" in out
    assert "Not attempted: picks_builder" in out
    assert PICKS not in box.text


def test_budget_read_error_refuses_after_t3(capsys):
    box = Box(BOX_1103)
    assert _run(box, {"error": "boom"}) == 0
    assert "could not be read" in capsys.readouterr().out and V3 not in box.text


def test_box_tasks_allowlist_has_the_batch():
    import box_tasks as bt
    for k in ("install_batch_w99_install", "install_batch_w99_readback", "install_batch_w99_uninstall"):
        assert k in bt.TASKS or k in getattr(bt, "ALLOW", {}) or any(k in str(v) for v in vars(bt).values() if isinstance(v, dict))


def test_each_step_reads_its_own_deploy_conf(tmp_path, monkeypatch):
    """11-04 03:16Z on the box: with no override, the batch read deploy/cron.conf for every step, so the picks step (whose
    line lives only in deploy/cron.picks_sheet) saw nothing to install and its NOT INSTALLED red blocked the batch."""
    engine_conf = tmp_path / "cron.conf"
    engine_conf.write_text("\n".join(["SHELL=/bin/bash", REFRESH, RUN, V3, T3, OTHER]) + "\n")
    picks_conf = tmp_path / "cron.picks_sheet"
    picks_conf.write_text(PICKS + "\n")
    for _name, mod, _arms in ib.GATED:
        monkeypatch.setattr(mod, "CRON_CONF", picks_conf if mod is ib.psi else engine_conf)
    todo = ib.pending(BOX_1103, None, _reg())
    assert todo["picks_builder"] == [PICKS_KEY]
    assert todo["nba_engine_v3"] == [V3_KEY]
    blocking, _exempt = ib.gate_batch(EV_1103, todo)
    assert blocking == []
