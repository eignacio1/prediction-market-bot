#!/usr/bin/env python3
"""Pre-PR local check (CI-trim, 2026-11-05): run the fast tests that CI would run for the files this branch changed.
CI stays the gate; this makes it a confirmation instead of a discovery. Usage: python3 scripts/precheck_changed.py [base]
Runs: changed test files; tests whose name contains a changed module's name; the exploratory isolation fence when any
12_EXPLORATORY/*.py changed. Read-only apart from pytest. Exit code = pytest's."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def select(changed, all_tests):
    pick = set()
    for f in changed:
        p = Path(f)
        if f.startswith("tests/") and p.name.startswith("test_") and f.endswith(".py"):
            pick.add(f)
        elif f.endswith(".py") and p.name != "__init__.py":
            if f.startswith("12_EXPLORATORY/"):
                pick.add("tests/test_exploratory_isolation.py")
            stem = p.stem
            pick.update(t for t in all_tests if stem in Path(t).name)
    return sorted(pick)


def main(base="origin/main"):
    out = subprocess.run(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    changed = [l for l in out.splitlines() if l]
    all_tests = [str(p.relative_to(ROOT)) for p in (ROOT / "tests").glob("test_*.py")]
    tests = [t for t in select(changed, all_tests) if (ROOT / t).exists()]
    print(f"changed files: {len(changed)}; tests selected: {len(tests)}")
    for t in tests:
        print("  ", t)
    if not tests:
        print("nothing to run locally (no .py changed) - CI will decide")
        return 0
    return subprocess.call([sys.executable, "-m", "pytest", "-q", *tests], cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
