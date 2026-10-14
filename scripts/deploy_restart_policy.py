#!/usr/bin/env python3
"""GG-432: decide whether a deploy may restart t4-mlb.

Called from .github/workflows/deploy.yml inside the deploy job. Stdlib only (the
deploy runner has no project venv). Two questions, in order:

1. Did this push change a file the running t4-mlb process actually imports?
   The set is derived, not hand-listed: the static import closure of
   src/prediction_market_bot/run_t4_mlb_live.py over the repo's own
   prediction_market_bot package. Docs-only or dashboard-only pushes do not
   restart t4-mlb. If the changed-file list is unknown (workflow_dispatch, a
   new-branch push), the answer is "yes" -- conservative, as before GG-432.
2. If yes: is an MLB game In Progress right now (MLB Stats API schedule)? If so,
   or if that cannot be determined, the code is pulled but t4-mlb is NOT
   restarted, and the job summary says so loudly. The skipped restart is done
   by the next deploy that changes a t4-mlb file outside a live game, or by
   hand (`systemctl restart t4-mlb`). No cron or timer is added (needs the
   operator's authorization).

pmbot-web-dashboard is not decided here; it keeps restarting on every deploy.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

PKG = "prediction_market_bot"
ENTRY = "src/prediction_market_bot/run_t4_mlb_live.py"
SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={start}&endDate={end}"

RESTART = "restart"
NOT_NEEDED = "not_needed"
SKIP_LIVE = "skip_live_game"
SKIP_UNKNOWN = "skip_game_state_unknown"


def _module_file(src_root: Path, dotted: str) -> Path | None:
    base = src_root.joinpath(*dotted.split("."))
    for cand in (base.with_suffix(".py"), base / "__init__.py"):
        if cand.is_file():
            return cand
    return None


def _package_inits(src_root: Path, dotted: str) -> list[Path]:
    parts = dotted.split(".")
    out = []
    for i in range(1, len(parts)):
        init = src_root.joinpath(*parts[:i], "__init__.py")
        if init.is_file():
            out.append(init)
    return out


def import_closure(repo_root: Path, entry: str = ENTRY) -> set[str]:
    """Repo-relative paths of every in-repo module the entry point can import.

    Every import statement counts, including ones inside functions -- a lazily
    imported module is still code the process runs.
    """
    src_root = repo_root / "src"
    entry_path = repo_root / entry
    seen: set[Path] = set()
    todo = [entry_path]
    while todo:
        path = todo.pop()
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        rel_mod = path.relative_to(src_root).with_suffix("")
        mod_parts = list(rel_mod.parts)
        if mod_parts[-1] == "__init__":
            mod_parts = mod_parts[:-1]
            pkg_parts = mod_parts
        else:
            pkg_parts = mod_parts[:-1]
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = pkg_parts[: len(pkg_parts) - (node.level - 1)]
                    mod = ".".join(base + ([node.module] if node.module else []))
                else:
                    mod = node.module or ""
                names = [mod] + [f"{mod}.{a.name}" for a in node.names]
            for name in names:
                if name != PKG and not name.startswith(PKG + "."):
                    continue
                f = _module_file(src_root, name)
                if f is not None:
                    todo.append(f)
                    todo.extend(_package_inits(src_root, name))
    return {str(p.relative_to(repo_root)) for p in seen}


def changed_files(repo_root: Path, before: str, after: str) -> list[str] | None:
    if not before or set(before) == {"0"} or not after:
        return None
    try:
        out = subprocess.run(["git", "diff", "--name-only", before, after], cwd=repo_root,
                             capture_output=True, text=True, check=True, timeout=60).stdout
    except (subprocess.SubprocessError, OSError):
        return None
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def live_games(schedule: dict) -> list[str]:
    """Games the MLB Stats API reports as currently live (abstractGameState 'Live')."""
    live = []
    for d in schedule.get("dates", []) or []:
        for g in d.get("games", []) or []:
            st = g.get("status", {}) or {}
            if st.get("abstractGameState") == "Live":
                teams = g.get("teams", {}) or {}
                away = ((teams.get("away") or {}).get("team") or {}).get("name", "?")
                home = ((teams.get("home") or {}).get("team") or {}).get("name", "?")
                live.append(f"{away} @ {home} ({st.get('detailedState', 'live')})")
    return live


def fetch_schedule(now: datetime | None = None, timeout: float = 15.0) -> dict | None:
    now = now or datetime.now(timezone.utc)
    # US evening games run past 00:00 UTC, so cover yesterday and today (UTC).
    url = SCHEDULE_URL.format(start=(now - timedelta(days=1)).date().isoformat(),
                              end=now.date().isoformat())
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": "pmbot-deploy-gate/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 - any failure means "game state unknown"
        return None


def decide(changed: list[str] | None, closure: set[str], schedule: dict | None) -> tuple[str, str]:
    if changed is not None:
        hits = sorted(set(changed) & closure)
        if not hits:
            return NOT_NEEDED, "no file imported by t4-mlb changed in this push"
        why = "t4-mlb imports changed: " + ", ".join(hits[:10]) + (" ..." if len(hits) > 10 else "")
    else:
        why = "changed-file list unknown (manual dispatch or new-branch push); assuming t4-mlb code changed"
    if schedule is None:
        return SKIP_UNKNOWN, why + "; MLB schedule could not be read, so a live game cannot be ruled out"
    games = live_games(schedule)
    if games:
        return SKIP_LIVE, why + "; MLB game(s) in progress: " + "; ".join(games)
    return RESTART, why + "; no MLB game in progress"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--before", default="")
    ap.add_argument("--after", default="")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--pending", action="store_true",
                    help="retry a previously skipped restart (GG-661): code is already pulled, only the "
                         "live-game check decides")
    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()
    closure = import_closure(repo)
    changed = None if args.pending else changed_files(repo, args.before, args.after)
    schedule = None
    if changed is None or set(changed) & closure:
        schedule = fetch_schedule()
    verdict, reason = decide(changed, closure, schedule)
    restart = "true" if verdict == RESTART else "false"
    print(f"t4-mlb restart decision: {verdict} -- {reason}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write(f"restart_t4={restart}\nverdict={verdict}\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            if verdict in (SKIP_LIVE, SKIP_UNKNOWN):
                fh.write("## :warning: t4-mlb NOT restarted (GG-432)\n\n"
                         f"{reason}.\n\nCode was pulled; the running t4-mlb still has the OLD code in memory. "
                         "It picks up the new code on the next deploy that changes a t4-mlb file outside a "
                         "live game, or by hand: `systemctl restart t4-mlb`.\n")
            else:
                fh.write(f"t4-mlb restart decision: **{verdict}** -- {reason}.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
