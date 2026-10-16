"""W78.1: the gap-agent burn-down parser (scripts/gg_burndown.py) and its three consumers."""
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import gg_burndown  # noqa: E402

BURN = """# GG burn-down ledger

## Per-tick totals
| Tick | Time (UTC) | OPEN before → after | Closed A / B / C | Triaged | PRs |
|---|---|---|---|---|---|
| 1 | 2026-10-16T00:25Z | log 186 → 185 exact-OPEN (note) | 1 / 0 / 0 | 7 | b |
| 2 | 2026-10-16T01:00Z | log 185 → 180 exact-OPEN | 2 / 1 / 0 | 25 | b |

## Ledger
| GG | Sev | Class | Evidence | Next owner | Tick |
|---|---|---|---|---|---|
| GG-1 | HIGH | L | 9 → 9 | x | 1 |
"""


def _root(tmp_path, ga_status):
    (tmp_path / "03_DECISIONS").mkdir()
    (tmp_path / "04_EXECUTION").mkdir()
    (tmp_path / "03_DECISIONS/GG_BURNDOWN.md").write_text(BURN)
    (tmp_path / "04_EXECUTION/ACTIVE_QUEUE.md").write_text(
        f"| GA | The governance gap agent (STANDING) | PLUMBING | {ga_status} | `/loop /gap` |\n")
    return tmp_path


def _now(h, m=0):
    return datetime(2026, 10, 16, h, m, tzinfo=timezone.utc)


def test_totals_ignore_ledger_table(tmp_path):
    s = gg_burndown.summary(_root(tmp_path, "running"), now=_now(1, 30))
    assert (s["ok"], s["ticks"], s["open_first"], s["open_now"], s["delta"]) == (True, 2, 186, 180, -6)
    assert s["closed"] == {"A": 3, "B": 1, "C": 0} and s["closed_total"] == 4 and s["triaged"] == 32
    assert s["last_tick"] == "2026-10-16T01:00Z" and s["age_h"] == 0.5


def test_stale_only_when_queue_says_running(tmp_path):
    r = _root(tmp_path, "running")
    assert gg_burndown.summary(r, now=_now(3, 30))["stale"] is True      # 2.5h old, running
    assert gg_burndown.summary(r, now=_now(2, 30))["stale"] is False     # 1.5h old
    (r / "04_EXECUTION/ACTIVE_QUEUE.md").write_text("| GA | agent | PLUMBING | relaunch | x |\n")
    s = gg_burndown.summary(r, now=_now(9))
    assert s["stale"] is False and s["running"] is False and "not ticking" in s["state_line"]


def test_missing_file_is_no_data_not_a_crash(tmp_path):
    s = gg_burndown.summary(tmp_path)
    assert s["ok"] is False and "unreadable" in s["error"]
    assert "no data" in gg_burndown.render_text(s)


def test_real_repo_file_parses():
    s = gg_burndown.summary(ROOT)
    assert s["ok"] and s["open_now"] is not None and s["ticks"] >= 1


def test_project_state_panel_renders_agent_line():
    import generate_project_state as g
    html = g._gg_agent_html(gg_burndown.summary(ROOT))
    assert "Gap agent" in html and "OPEN now" in html
    assert "no data" in g._gg_agent_html({"ok": False, "error": "x"})


def test_visual_dashboard_builder_embeds_agent(tmp_path):
    import build_visual_dashboard_html as b
    out = tmp_path / "vd.html"
    b.build(out)
    h = out.read_text()
    assert "__GAGENT__" not in h and 'id="gaOpen"' in h and "const GAGENT = {" in h
