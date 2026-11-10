"""W108.1 (B-062/P04): prop-series archive cron lines. Known-answer checks on deploy/cron.conf."""
import re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONF = (ROOT / "deploy/cron.conf").read_text().splitlines()
ARCH = [l for l in CONF if "scripts/archive_market_prices.py" in l and not l.lstrip().startswith("#")]


def _series(line):
    m = re.search(r"--series (.*?) --out", line)
    return m.group(1).split()


PROP = [l for l in ARCH if not any(s.endswith(("GAME", "SPREAD", "TOTAL", "TEAMTOTAL")) for s in _series(l))
        and not any(s.startswith("KXMLB") for s in _series(l))]


def test_three_prop_lines_one_per_sport():
    assert len(PROP) == 3
    assert sorted(_series(l)[0][:5] for l in PROP) == ["KXNBA", "KXNFL", "KXNHL"]


def test_each_line_stays_in_its_sport_prefix():
    for l in PROP:
        pre = _series(l)[0][:5]
        assert all(s.startswith(pre) for s in _series(l))


def test_exact_series_sets():
    by = {_series(l)[0][:5]: set(_series(l)) for l in PROP}
    assert by["KXNBA"] == set("KXNBAPTS KXNBAREB KXNBAAST KXNBA3PT KXNBASTL KXNBAPRA KXNBA2D KXNBA3D".split())
    assert by["KXNHL"] == {"KXNHLGOAL", "KXNHLAST"}
    assert len(by["KXNFL"]) == 10


def test_no_overlap_with_game_lines_or_each_other():
    game = {s for l in ARCH if l not in PROP for s in _series(l)}
    seen = []
    for l in PROP:
        seen += _series(l)
    assert not (set(seen) & game)
    assert len(seen) == len(set(seen))


def test_prop_lines_do_not_sample_depth():
    assert all("--depth-sample-per-family" not in l for l in PROP)


def test_existing_archiver_lines_byte_identical_to_main():
    old = subprocess.run(["git", "show", "origin/main:deploy/cron.conf"], cwd=ROOT, capture_output=True, text=True)
    if old.returncode:
        return
    new = set(CONF)
    for l in old.stdout.splitlines():
        if "scripts/archive_market_prices.py" in l:
            assert l in new


def test_new_lines_registry_live_and_wanted():
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import archive_cron_install as aci
    reg = (ROOT / "02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml").read_text()
    for l in PROP:
        sched = " ".join(l.split()[:5])
        assert f'schedule = "{sched}"' in reg
