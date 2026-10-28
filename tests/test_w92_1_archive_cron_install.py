"""W92.1: archive_cron_install -- idempotence, foreign lines untouched, backup-or-abort, budget gate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import archive_cron_install as aci  # noqa: E402
import runtime_registry as rr  # noqa: E402

NBA = ("8,28,48 17-23 * * * cd $PROJ && PYTHONPATH=$PYTHONPATH $PYTHON scripts/archive_market_prices.py "
       "--series KXNBAGAME --out exp_output/PRICE_ARCHIVE >> logs/x.log 2>&1")
NBA2 = NBA.replace("8,28,48 17-23", "8,28,48 0-5")  # same signature, different schedule
OTHER = "0 1 * * * cd $PROJ && $PYTHON scripts/other_job.py"
CONF = "\n".join(["SHELL=/bin/bash", NBA, NBA2, OTHER]) + "\n"


def _reg(status="live"):
    out = []
    for line in (NBA, NBA2):
        key, _ = rr._cron_key(line)
        out.append({"key": key, "kind": "cron", "status": status})
    return out


GREEN = {"budget": "GREEN", "head": "h", "as_of": "t"}


class Box:
    def __init__(self, text):
        self.text, self.writes = text, 0

    def read(self):
        return self.text

    def write(self, t):
        self.text, self.writes = t, self.writes + 1


def _run(box, live=GREEN, backup=lambda c: Path("/tmp/bak"), reg=None):
    return aci.install(live_fn=lambda: live, read=box.read, write=box.write, backup=backup,
                       conf_text=CONF, reg=_reg() if reg is None else reg)


def test_installs_exact_missing_lines_only():
    box = Box("# foreign\n" + OTHER + "\n")
    assert _run(box) == 0
    assert NBA in box.text and NBA2 in box.text and aci.BEGIN in box.text
    assert box.text.startswith("# foreign\n" + OTHER + "\n")
    assert OTHER not in aci.merged_crontab("", []).splitlines()  # the conf's non-archiver line is never copied


def test_second_run_is_idempotent():
    box = Box("# foreign\n")
    _run(box)
    once = box.text
    assert _run(box) == 0 and box.text == once and box.writes == 1


def test_same_signature_other_schedule_still_installed():
    box = Box(NBA + "\n")  # one of the two same-signature lines is already there
    _run(box)
    assert NBA2 in box.text and box.text.count(NBA) == 1


def test_foreign_line_never_modified():
    foreign = "*/5 * * * * echo keep   me   exactly"
    box = Box(foreign + "\n")
    _run(box)
    assert foreign in box.text.splitlines()


def test_missing_backup_aborts_before_write():
    box = Box("# foreign\n")
    assert _run(box, backup=lambda c: None) == 0
    assert box.writes == 0 and box.text == "# foreign\n"


def test_non_live_entries_not_installed():
    box = Box("")
    _run(box, reg=_reg("retired"))
    assert box.writes == 0


def test_red_budget_refuses_and_blank_reasons_block():
    box = Box("")
    assert _run(box, live={"budget": "RED", "reasons": ["DOWN foo"]}) == 0 and box.writes == 0
    assert _run(box, live={"budget": "RED", "reasons": []}) == 0 and box.writes == 0


def test_own_not_installed_reason_is_exempt_others_block():
    key, _ = rr._cron_key(NBA)
    ok, ex = aci.gate({"budget": "RED", "reasons": ["NOT INSTALLED " + key]}, {key})
    assert ok == [] and len(ex) == 1
    bad, _ = aci.gate({"budget": "RED", "reasons": ["NOT INSTALLED " + key, "DOWN svc"]}, {key})
    assert bad == ["DOWN svc"]
    other, _ = aci.gate({"budget": "RED", "reasons": ["NOT INSTALLED cron|x|y"]}, {key})
    assert other == ["NOT INSTALLED cron|x|y"]


def test_uninstall_removes_only_block():
    box = Box("# foreign\n" + OTHER + "\n")
    _run(box)
    aci.uninstall(read=box.read, write=box.write, backup=lambda c: Path("/tmp/bak"))
    assert box.text == "# foreign\n" + OTHER + "\n"
