#!/usr/bin/env python3
"""Operator-only: add the terminals' standing allow rules to .claude/settings.local.json (main tree).

Run by the OPERATOR, once, by typing in any Claude Code terminal:
    ! python3 scripts/operator_grant_permissions.py
(The leading "!" runs it as you, not as Claude. Claude sessions may not edit their own permissions;
Waves 68-69 showed that an authorization line in a block prompt is refused every time.)

Idempotent: keeps every rule already in the file, adds the missing ones, prints what it added.
Edit RULES below to change the standing list; every rule is narrow (auto mode drops broad ones like Bash(*)).
"""
import json
import pathlib

RULES = [
    "Bash(ssh prediction-market-vps *)", "Bash(scp * prediction-market-vps*)", "Bash(scp prediction-market-vps*)",
    "Bash(rsync * prediction-market-vps*)",
    "Bash(gh pr *)", "Bash(gh api *)", "Bash(gh run *)", "Bash(gh workflow *)",
    "Bash(git fetch *)", "Bash(git pull *)", "Bash(git push *)", "Bash(git commit *)", "Bash(git add *)",
    "Bash(git rebase *)", "Bash(git merge *)", "Bash(git checkout *)", "Bash(git switch *)", "Bash(git worktree *)",
    "Bash(git status *)", "Bash(git log *)", "Bash(git diff *)", "Bash(git -C *)",
    "Bash(pytest *)", "Bash(python3 -m pytest *)", "Bash(python3 scripts/*)", "Bash(bash scripts/*)",
    "Bash(scripts/new_session_worktree.sh *)", "Bash(scripts/claim_session.sh *)", "Bash(bash .claude/hooks/*)",
]

# Malformed rules from earlier versions (":*" mid-pattern never matches; Claude Code warns at startup). Removed on run.
BAD = ["Bash(scp * prediction-market-vps:*)", "Bash(scp prediction-market-vps:* *)", "Bash(rsync * prediction-market-vps:*)"]

ROOT = pathlib.Path(__file__).resolve().parents[1]
path = ROOT / ".claude" / "settings.local.json"
data = json.loads(path.read_text()) if path.exists() and path.read_text().strip() else {}
allow = data.setdefault("permissions", {}).setdefault("allow", [])
removed = [r for r in allow if r in BAD]
allow[:] = [r for r in allow if r not in BAD]
added = [r for r in RULES if r not in allow]
allow.extend(added)
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(data, indent=2) + "\n")
print(f"{path}: {len(added)} rule(s) added, {len(removed)} malformed removed, {len(allow)} total.")
for r in removed:
    print("  -", r)
for r in added:
    print("  +", r)
print("Takes effect in terminals started after this (restart running ones to pick it up).")
