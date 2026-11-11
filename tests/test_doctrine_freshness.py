import importlib.util
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("doctrine_freshness", ROOT / "scripts" / "doctrine_freshness.py")
df = importlib.util.module_from_spec(spec)
spec.loader.exec_module(df)


def _mk(tmp, name, text):
    p = tmp / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def test_flags_stale_missing_and_unreviewed(tmp_path):
    _mk(tmp_path, "02_ARCHITECTURE_DESIGN/DOCTRINE.md",
        "x\n## Doctrine stack\n| File | a | b |\n|---|---|---|\n| `a.md` | x | y |\n| `b.md` | x | y |\n| `c.md` | x | y |\n| `d.md` | x | y |\n## end\n")
    _mk(tmp_path, "a.md", "**Last reviewed:** 2026-11-10\n")
    _mk(tmp_path, "b.md", "**Last reviewed:** 2026-07-02\n")
    _mk(tmp_path, "c.md", "no line\n")
    rows = {r[1]: r for r in df.check(tmp_path, date(2026, 11, 11), 14)}
    assert rows["a.md"][0] == "ok"
    assert rows["b.md"][0] == "RED"
    assert "no 'Last reviewed'" in rows["c.md"][2]
    assert rows["d.md"][2] == "missing"


def test_every_repo_stack_file_has_a_review_line():
    rows = df.check(ROOT, date.fromisoformat("2026-11-11"), 10_000)
    assert rows and all(r[0] == "ok" for r in rows), [r for r in rows if r[0] != "ok"]
