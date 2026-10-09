"""W62.3: the preseason-cron removal script touches only its block, is date-gated, and is dry-run by default."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("rm", ROOT / "scripts" / "remove_nba_preseason_cron.py")
rm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rm)

CRON = "0 1 * * * a\n# BEGIN EXP-038 NBA\n5 * * * * b\n# END EXP-038 NBA\n# BEGIN EXP-038 NBA PRESEASON\n57 * * * * c\n# END EXP-038 NBA PRESEASON\n9 9 * * * d\n"


def _setup(tmp_path):
    ct = tmp_path / "ct"; ct.write_text(CRON)
    d = tmp_path / "deploy"; d.mkdir()
    (d / "cron.conf").write_text(CRON)
    (d / "cron.nba_shadow_preseason").write_text("x")
    return ct, d


def test_dry_run_changes_nothing(tmp_path, capsys):
    ct, d = _setup(tmp_path)
    assert rm.main(["--crontab-file", str(ct), "--deploy-dir", str(d), "--backup-dir", str(tmp_path / "b")]) == 0
    assert ct.read_text() == CRON and (d / "cron.nba_shadow_preseason").exists()


def test_apply_removes_only_block_and_backs_up(tmp_path):
    ct, d = _setup(tmp_path)
    assert rm.main(["--apply", "--crontab-file", str(ct), "--deploy-dir", str(d), "--backup-dir", str(tmp_path / "b")]) == 0
    want = "0 1 * * * a\n# BEGIN EXP-038 NBA\n5 * * * * b\n# END EXP-038 NBA\n9 9 * * * d\n"
    assert ct.read_text() == want and (d / "cron.conf").read_text() == want
    assert not (d / "cron.nba_shadow_preseason").exists()
    assert [p.read_text() for p in (tmp_path / "b").iterdir()] == [CRON]


def test_live_apply_refused_before_window(monkeypatch):
    assert rm.main(["--apply", "--now", "2026-10-21T09:59:00+00:00"]) == 2


def test_aborts_on_missing_block(tmp_path):
    ct = tmp_path / "ct"; ct.write_text("0 1 * * * a\n")
    try:
        rm.main(["--crontab-file", str(ct)])
    except SystemExit as e:
        assert "ABORT" in str(e)
    else:
        raise AssertionError
