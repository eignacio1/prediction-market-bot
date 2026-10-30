"""W95.1: nba_engine_cron_install -- only the engine lines, idempotent, foreign lines untouched, budget gate, uninstall."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import nba_engine_cron_install as nci  # noqa: E402
import runtime_registry as rr  # noqa: E402
from prediction_market_bot.pregame_shadow.silent_arms import SPECS, ArmInput, evaluate_arm  # noqa: E402

REFRESH = ("33 12 * * * cd /x && python -m prediction_market_bot.c1_signal_ingestion.nba_current_season "
           ">> logs/nba_engine_live_cron.log 2>&1")
RUN = ("2,12,22,32,42,52 16-23,0-4 * * * cd /x && sh -c 'python -m prediction_market_bot.nba_engine.live --raw r --no-refresh; "
       "python -m prediction_market_bot.nba_engine.live_v2 --raw r --no-refresh' >> logs/nba_engine_live_cron.log 2>&1")
ARCH = "8,28,48 17-23 * * * cd $PROJ && $PYTHON scripts/archive_market_prices.py --series KXNBAGAME >> logs/x.log 2>&1"
OTHER = "0 1 * * * cd $PROJ && $PYTHON scripts/other_job.py"
CONF = "\n".join(["SHELL=/bin/bash", REFRESH, RUN, ARCH, OTHER]) + "\n"
GREEN = {"budget": "GREEN", "head": "h", "as_of": "t"}


def _reg():
    return [{"key": rr._cron_key(l)[0], "kind": "cron", "status": "live"} for l in (REFRESH, RUN, ARCH, OTHER)]


class Box:
    def __init__(self, text):
        self.text, self.writes = text, 0

    def read(self):
        return self.text

    def write(self, t):
        self.text, self.writes = t, self.writes + 1


def _run(box, live=GREEN, backup=lambda c: Path("/tmp/bak")):
    return nci.install(live_fn=lambda: live, read=box.read, write=box.write, backup=backup, conf_text=CONF, reg=_reg())


def test_wanted_is_only_the_engine_lines():
    assert [l for _, l in nci.wanted_lines(CONF, _reg())] == [REFRESH, RUN]


def test_installs_block_keeps_foreign_lines_and_is_idempotent():
    box = Box(OTHER + "\n" + ARCH + "\n")
    assert _run(box) == 0 and box.writes == 1
    assert box.text.splitlines()[:2] == [OTHER, ARCH]
    assert nci.BEGIN in box.text and REFRESH in box.text and RUN in box.text
    _run(box)
    assert box.writes == 1


def test_red_budget_blocks_and_writes_nothing():
    box = Box(OTHER + "\n")
    _run(box, live={"budget": "RED", "reasons": ["healthcheck fault"]})
    assert box.writes == 0


def test_backup_failure_aborts():
    box = Box(OTHER + "\n")
    _run(box, backup=lambda c: None)
    assert box.writes == 0


def test_uninstall_removes_only_the_block():
    box = Box(OTHER + "\n")
    _run(box)
    assert nci.uninstall(read=box.read, write=box.write, backup=lambda c: Path("/tmp/bak")) == 0
    assert box.text == OTHER + "\n"


def test_silent_arm_specs_alarm_when_a_game_tipped_with_no_row():
    now = datetime(2026, 10, 31, 4, 0, tzinfo=timezone.utc)
    tip = now - timedelta(hours=3)
    for k in ("nba_engine_v1", "nba_engine_v2"):
        assert evaluate_arm(ArmInput(SPECS[k], [tip], None), now)["status"] == "silent"
        assert evaluate_arm(ArmInput(SPECS[k], [tip], tip - timedelta(minutes=50)), now)["status"] == "ok"
        assert evaluate_arm(ArmInput(SPECS[k], [], None), now)["status"] == "idle"
