"""W99.3 / B-017: the NBA event store trailed by ~2 days because the only refresh (12:33Z) ran before the sources publish
the previous day (ESPN box ~13:28Z, nba_stats schedule+pbp ~15:15Z). A second refresh after the publish and before the
first runner window fixes the lag. Known answer: the refresh schedule must sit after the last publish and before 16:02Z,
collide with no other job's minute at that hour, be registered, and be picked up by the installer."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import nba_engine_cron_install as nec  # noqa: E402
import runtime_registry as rr  # noqa: E402

PUBLISH_LAST_UTC = (15, 15)   # nba_stats schedule + pbp (measured W99.3)
FIRST_RUNNER_UTC = (16, 2)
CONF = (ROOT / "deploy" / "cron.conf").read_text()


def _refresh_lines():
    return [l for l in CONF.splitlines()
            if l and not l.startswith("#") and "c1_signal_ingestion.nba_current_season" in l]


def _sched(line):
    m, h = line.split()[:2]
    return int(m), int(h)


def test_a_refresh_runs_after_the_last_source_publish_and_before_the_runner():
    after = [(m, h) for m, h in map(_sched, _refresh_lines()) if (h, m) > PUBLISH_LAST_UTC and (h, m) < FIRST_RUNNER_UTC]
    assert after, "no refresh between the 15:15Z source publish and the 16:02Z runner"


def test_original_1233_line_unchanged():
    assert any(l.startswith("33 12 * * * ") for l in _refresh_lines())


def test_second_refresh_minute_collides_with_no_other_job_at_its_hour():
    mins = {}
    for l in CONF.splitlines():
        if not l or l.startswith(("#", "SHELL", "PATH", "PYTHONPATH", "MAILTO")) or len(l.split()) < 6:
            continue
        mf, hf = l.split()[:2]
        if "nba_current_season" in l:
            continue
        hours = range(24) if hf == "*" else _expand(hf)
        if 15 in hours:
            mins.setdefault(frozenset(_expand(mf, 60)), l)
    assert not any(46 in k for k in mins), [v[:80] for k, v in mins.items() if 46 in k]


def _expand(field, top=24):
    out = set()
    for part in field.split(","):
        step = 1
        if "/" in part:
            part, st = part.split("/")
            step = int(st)
        if part == "*":
            lo, hi = 0, top - 1
        elif "-" in part:
            lo, hi = map(int, part.split("-"))
            if lo > hi:
                out |= set(range(lo, top)) | set(range(0, hi + 1))
                continue
        else:
            lo = hi = int(part)
        out |= set(range(lo, hi + 1, step))
    return out


def test_every_refresh_line_is_registered_live_and_installer_picks_it_up():
    reg = rr.load()
    wanted = nec.wanted_lines(CONF, reg)
    keys = [k for k, l in wanted if "nba_current_season" in l]
    assert len(keys) == len(_refresh_lines()) == 2
    assert any(re.match(r"cron\|46 15 \* \* \*\|", k) for k in keys)
