"""W100.3 / B-040: no cron line is claimed by two installers (a marker that is a prefix of another's matched it).

Applies to the installers that pick lines out of a conf file by MARKERS (archive, nba_engine v1/v2, v3, picks sheet).
Does not cover the fragment installers (source/thin capture, lineup window, passyds), which own a BEGIN/END block."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archive_cron_install as aci  # noqa: E402
import nba_engine_cron_install as v1  # noqa: E402
import nba_engine_v3_cron_install as v3  # noqa: E402
import picks_sheet_cron_install as picks  # noqa: E402
import runtime_registry as rr  # noqa: E402

INSTALLERS = {"archive": aci, "nba_engine_v1v2": v1, "nba_engine_v3": v3, "picks_sheet": picks}


def _all_live(text):
    return [{"key": rr._cron_key(l.strip())[0], "kind": "cron", "status": "live"}
            for l in text.splitlines() if l.strip() and not l.strip().startswith("#") and len(l.split()) >= 6]


def test_marker_in_respects_identifier_boundary():
    assert aci.marker_in("python -m x.nba_engine.live --raw r", "x.nba_engine.live")
    assert not aci.marker_in("python -m x.nba_engine.live_v3 --raw r", "x.nba_engine.live")
    assert aci.marker_in("... x.nba_engine.live_v3", "x.nba_engine.live_v3")      # end of line
    assert aci.marker_in("sh -c 'x.nba_engine.live; y'", "x.nba_engine.live")      # punctuation ends the token


def test_v1_does_not_select_v3_line_and_vice_versa():
    v1l = "2 16 * * * cd /x && python -m prediction_market_bot.nba_engine.live --raw r >> l 2>&1"
    v3l = "3 16 * * * cd /x && python -m prediction_market_bot.nba_engine.live_v3 --raw r >> l 2>&1"
    conf = v1l + "\n" + v3l + "\n"
    reg = _all_live(conf)
    assert [l for _, l in v1.wanted_lines(conf, reg)] == [v1l]
    assert [l for _, l in v3.wanted_lines(conf, reg)] == [v3l]


def test_real_conf_every_cron_line_has_at_most_one_installer():
    text = "\n".join((ROOT / "deploy" / n).read_text() for n in ("cron.conf", "cron.picks_sheet"))
    reg = _all_live(text)
    owners = {}
    for name, mod in INSTALLERS.items():
        for _, line in mod.wanted_lines(text, reg):
            owners.setdefault(line, []).append(name)
    assert owners, "no installer selected any real line - the sweep is vacuous"
    clash = {l[:90]: o for l, o in owners.items() if len(o) > 1}
    assert not clash, clash
