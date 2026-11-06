"""W105.5: the ride_board cron line is ONE line, lock-wrapped, game windows only, demo env, escaped; installer is wired."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def _lines():
    return [l for l in (ROOT / "deploy/cron.ride_board").read_text().splitlines() if l.strip() and not l.startswith("#")]


def test_exactly_one_cron_line_locked_and_game_window():
    ls = _lines()
    assert len(ls) == 1
    l = ls[0]
    assert l.startswith("9,29,49 17-23,0-2 * * * ")
    assert "flock -n 9" in l and "9>/tmp/ride_board.lock" in l and "SKIP_LOCKED" in l
    assert "scripts/run_ride_board.py" in l and "demo_fill.env" in l
    assert not re.search(r"(?<!\\)%", l)  # every % escaped for cron


def test_box_tasks_wired_and_installer_importable():
    import box_tasks as bt
    import ride_board_cron_install as rb
    for n in ("install", "readback", "uninstall"):
        assert bt.TASKS["ride_board_" + n].endswith("ride_board_cron_install.py " + n)
    assert rb.MARKERS == ("scripts/run_ride_board.py",)
    assert "logs/ride_board" in (ROOT / "scripts/ride_board_cron_install.py").read_text()
