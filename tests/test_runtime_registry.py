"""ADR-0074: every running component the repo mirrors (cron fragments, systemd units, workflows) is in the runtime registry.

A new cron line, service or workflow without a registry entry fails CI - that is the point. Add it with
`python3 scripts/runtime_registry.py add`, fill purpose / pillar / writes / alarm, then `... render`.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import runtime_registry as rr  # noqa: E402


def test_every_mirrored_component_is_registered():
    assert rr.check(verbose=False) == 0, "run: python3 scripts/runtime_registry.py check"


def test_unregistered_component_fails(monkeypatch):
    real = rr.discover()
    fake = dict(real)
    fake["cron|0 0 * * *|scripts/brand_new_job.py"] = {"kind": "cron", "source": "deploy/cron.x", "mirrors": [], "command": "x"}
    monkeypatch.setattr(rr, "discover", lambda: fake)
    assert rr.check(verbose=False) == 1


def test_live_entry_missing_from_mirrors_fails(monkeypatch):
    real = rr.discover()
    gone = next(k for k in real if k.startswith("cron|"))
    monkeypatch.setattr(rr, "discover", lambda: {k: v for k, v in real.items() if k != gone})
    assert rr.check(verbose=False) == 1


def test_registry_entries_carry_required_fields():
    for c in rr.load():
        missing = [f for f in rr.REQUIRED if f not in c]
        assert not missing, (c.get("key"), missing)
        assert c["status"] in {"live", "paused", "retired"}, c["key"]
        assert c["pillar"] in {"BREADTH", "DEPTH", "EXECUTION", "PROOF", "PLUMBING"}, c["key"]


def test_runtime_map_is_current(tmp_path, monkeypatch):
    committed = rr.MAP.read_text()
    monkeypatch.setattr(rr, "MAP", tmp_path / "map.md")
    rr.render()
    assert (tmp_path / "map.md").read_text() == committed, "run: python3 scripts/runtime_registry.py render"


def test_begin_end_fragments_ignore_install_instructions(tmp_path, monkeypatch):
    d = tmp_path / "deploy"
    d.mkdir()
    (d / "cron.conf").write_text("")
    (d / "cron_x.conf").write_text("# Install: (crontab -l; sed -n '/^# BEGIN X/,/^# END X/p'\n"
                                   "1 1 * * * cd /p && python scripts/a.py >> logs/a.log 2>&1\n"
                                   "# BEGIN X\n2 2 * * * cd /p && python scripts/b.py >> logs/b.log 2>&1\n# END X\n")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    monkeypatch.setattr(rr, "ROOT", tmp_path)
    keys = [k for k in rr.discover() if k.startswith("cron|")]
    assert keys == ["cron|2 2 * * *|scripts/b.py"]


# ---- W76.4: review gate, box check, live evaluation, SURFACE BUDGET (GG-742/743/753) ----

def _c(**kw):
    base = {"key": "cron|0 1 * * *|scripts/x.py", "kind": "cron", "status": "live", "reviewed": True, "writes": ["logs/x.log"],
            "alarm": "staleness: x", "purpose": "p", "pillar": "PLUMBING"}
    base.update(kw)
    return base


def test_mini_toml_equals_tomllib():
    tl = rr.tomllib
    if tl is None:
        import pytest
        pytest.skip("no tomllib on this python")
    text = rr.REGISTRY.read_text()
    assert rr._mini_toml(text) == tl.loads(text)


def test_registry_fully_reviewed_and_every_no_alarm_has_a_reason():
    live = [c for c in rr.load() if c.get("status") == "live"]
    assert not [c["key"] for c in live if not c.get("reviewed")]
    assert not [c["key"] for c in live if rr._no_alarm(c) and rr._unexplained(c)]
    assert not [c["key"] for c in live if "(auto" in c["purpose"] or c["pillar"] == "UNSET"]


def test_unexplained_rejects_stubs():
    assert rr._unexplained({"alarm": "UNSET"})
    assert rr._unexplained({"alarm": "none known (auto)"})
    assert rr._unexplained({"alarm": "none"})
    assert not rr._unexplained({"alarm": "none: one-shot job read back by the block that installed it"})


def test_check_box_matches_on_script_and_flags_not_schedule():
    reg = [_c(key="cron|45 18 * * *|scripts/run_mlb_pregame.py")]
    probe = {"crontab": "45 22 * * * cd /opt/x && python scripts/run_mlb_pregame.py >> logs/a.log 2>&1\n", "units": []}
    out = rr.check_box(probe, reg)
    assert not out["unmirrored"] and not out["not_installed"]
    out = rr.check_box({"crontab": "", "units": []}, reg)
    assert out["not_installed"]


def test_evaluate_stale_goes_red_and_missing_box_is_not_red():
    reg = [_c(max_age_h=2)]
    probe = {"epoch": 1000000.0, "ts": "t", "head": "abcdef012", "writes": {"logs/x.log": 1000000.0 - 5 * 3600}, "services": {},
             "health": {"line": "HEALTHY: 0 faults"}}
    ev = rr.evaluate(reg, probe, now=1000000.0)
    assert ev["budget"] == "RED" and ev["counts"]["stale"] == 1
    probe["writes"] = {"logs/x.log": 1000000.0 - 3600}
    assert rr.evaluate(reg, probe, now=1000000.0)["budget"] == "GREEN"


def test_evaluate_registry_failure_and_silent_arm_are_reasons():
    reg = [_c()]
    probe = {"epoch": 1.0, "head": "a", "writes": {}, "services": {}, "silent": {"arms": [{"name": "nhl", "status": "silent", "text": "no rows"}]}}
    ev = rr.evaluate(reg, probe, now=1.0, registry_ok=False)
    assert ev["budget"] == "RED" and any("SILENT ARM" in r for r in ev["reasons"])


# ── W76.4 Part D: the live surfaces ────────────────────────────────────────────

def _fake_ev(budget="RED"):
    rows = [{"key": "k1", "kind": "cron", "purpose": "Settles the ledger", "pillar": "EXECUTION", "state": "STALE",
             "detail": "last write 40h ago", "age_h": 40, "max_age_h": 30, "no_alarm": False, "unexplained": False},
            {"key": "k2", "kind": "systemd", "purpose": "Serves things", "pillar": "PLUMBING", "state": "ok",
             "detail": "", "age_h": 0.1, "max_age_h": None, "no_alarm": False, "unexplained": False}]
    return {"rows": rows, "reasons": ["STALE: Settles the ledger"] if budget == "RED" else [], "budget": budget,
            "counts": {"live": 2, "stale": 1 if budget == "RED" else 0, "no_alarm_unexplained": 0,
                       "no_alarm_reasoned": 0, "unreviewed": 0},
            "head": "abc12345", "as_of": "2026-10-15T00:00:00Z"}


def test_project_panel_shows_red_stale_row_and_budget(monkeypatch):
    import generate_project_state as g
    sec = {"source": "s", "as_of": "t", "ev": _fake_ev("RED"), "werr": {"rows": [], "tally": []}}
    html = g._runtime_html(sec, lambda t, s: f"<h2>{t}</h2>")
    assert "SURFACE BUDGET RED" in html and "STALE: Settles the ledger" in html
    assert "<tr class='bad'>" in html and "Settles the ledger" in html


def test_project_panel_pending_is_awaiting_not_green():
    import generate_project_state as g
    html = g._runtime_html({"awaiting": "the first box probe", "werr": {"rows": [], "tally": []}}, lambda t, s: "<h2>x</h2>")
    assert "awaiting" in html and "GREEN" not in html


def test_terminal_strip_lists_red_components_by_name(monkeypatch):
    import web_dashboard as w
    monkeypatch.setattr(rr, "live_background", lambda: _fake_ev("RED"))
    strip = w._runtime_strip()
    assert strip["budget"] == "RED" and strip["bad"][0]["name"] == "Settles the ledger"
    monkeypatch.setattr(rr, "live_background", lambda: {"pending": True})
    assert "awaiting" in w._runtime_strip()


def test_live_background_never_blocks_and_returns_pending(monkeypatch, tmp_path):
    monkeypatch.setattr(rr, "live_cache_path", lambda: tmp_path / "none.json")
    started = []
    monkeypatch.setattr(rr, "live", lambda refresh=False, use_cache=True: started.append(1) or {})
    out = rr.live_background()
    assert out == {"pending": True}
    rr._BG["thread"].join(5)
    assert started


def test_visual_dashboard_reads_cached_probe(monkeypatch, tmp_path):
    import build_visual_dashboard_html as bvd
    cache = tmp_path / "c.json"
    cache.write_text(json.dumps(_fake_ev("RED")))
    monkeypatch.setattr(rr, "live_cache_path", lambda: cache)
    lv = bvd.runtime_live()
    assert lv["budget"] == "RED" and lv["rows"]["k1"]["state"] == "STALE"
    monkeypatch.setattr(rr, "live_cache_path", lambda: tmp_path / "missing.json")
    assert bvd.runtime_live() == {}
    assert all("key" in c for c in bvd.runtime())
