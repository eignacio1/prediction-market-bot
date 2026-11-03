"""W98.3: picks_sheet_cron_install -- only the picks line, idempotent, foreign lines untouched, budget gate, uninstall."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import picks_sheet_cron_install as pci  # noqa: E402
import runtime_registry as rr  # noqa: E402

PICKS = "37 5,22 * * * cd /x && nice -n 10 /x/venv/bin/python scripts/build_picks_sheet.py >> logs/picks_sheet_cron.log 2>&1"
OTHER = "0 1 * * * cd $PROJ && $PYTHON scripts/other_job.py"
CONF = "# BEGIN W97.3 PICKS SHEET\n" + PICKS + "\n# END W97.3 PICKS SHEET\n"
GREEN = {"budget": "GREEN", "head": "h", "as_of": "t"}


def _reg():
    return [{"key": rr._cron_key(l)[0], "kind": "cron", "status": "live"} for l in (PICKS, OTHER)]


class Box:
    def __init__(self, text):
        self.text, self.writes = text, 0

    def read(self):
        return self.text

    def write(self, t):
        self.text, self.writes = t, self.writes + 1


def _run(box, live=GREEN):
    return pci.install(live_fn=lambda: live, read=box.read, write=box.write, backup=lambda c: Path("/tmp/bak"),
                       conf_text=CONF, reg=_reg())


def test_wanted_is_only_the_picks_line():
    assert [l for _, l in pci.wanted_lines(CONF + OTHER + "\n", _reg())] == [PICKS]


def test_installs_keeps_foreign_lines_idempotent_and_uninstalls():
    box = Box(OTHER + "\n")
    assert _run(box) == 0 and box.writes == 1
    assert box.text.splitlines()[0] == OTHER and PICKS in box.text and pci.BEGIN in box.text
    _run(box)
    assert box.writes == 1
    pci.uninstall(read=box.read, write=box.write, backup=lambda c: Path("/tmp/bak"))
    assert box.text == OTHER + "\n"


def test_red_budget_blocks_and_writes_nothing():
    box = Box(OTHER + "\n")
    _run(box, live={"budget": "RED", "reasons": ["healthcheck fault"]})
    assert box.writes == 0


def test_missing_backup_aborts():
    box = Box(OTHER + "\n")
    pci.install(live_fn=lambda: GREEN, read=box.read, write=box.write, backup=lambda c: None, conf_text=CONF, reg=_reg())
    assert box.writes == 0
