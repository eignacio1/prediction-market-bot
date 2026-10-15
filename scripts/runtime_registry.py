#!/usr/bin/env python3
"""Runtime registry: one owned list of every running piece of the bot (ADR-0074, 2026-10-14).

Why: the project's recurring failure is that each session sees a slice of the running system and nobody owns the whole
(GG-740). Arms went silent unnoticed (GG-532, GG-163), services ran stale code (GG-661), fixes landed in one copy of a
check and not another (GG-122 -> GG-144). The registry makes "what runs" a single, CI-enforced list.

Sources of running components (the repo's mirrors of what is installed on the VPS / GitHub):
  * cron lines in deploy/cron.conf, deploy/cron.<name> and deploy/cron_*.conf (drafts excluded)
  * systemd units: deploy/*.service, deploy/*.timer, scripts/*.service
  * GitHub Actions workflows: .github/workflows/*.yml

Registry: 02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml - one [[component]] per running piece, keyed by `key`.

Commands:
  check   exit 1 if any mirrored component has no registry entry, or a `live` entry no longer exists in the mirrors.
          Unreviewed entries (reviewed = false) are reported as debt, not failures. Run by tests/test_runtime_registry.py.
  add     append skeleton entries for every unregistered component (reviewed = false) - use when adding a component,
          then fill purpose / pillar / writes / alarm by hand.
  render  write 02_ARCHITECTURE_DESIGN/RUNTIME_MAP.md (human view) from the registry.
  surface print the surface count (live components) and debt, for the sitrep's Surface row.

Live columns (code SHA running, last write, alarm state) need the VPS; the governance scan adds them (ADR-0074 block).
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "02_ARCHITECTURE_DESIGN" / "RUNTIME_REGISTRY.toml"
MAP = ROOT / "02_ARCHITECTURE_DESIGN" / "RUNTIME_MAP.md"

SCRIPT_RE = re.compile(r"(?:scripts|src|deploy)/[\w/.\-]+\.(?:py|sh)")
FLAG_RE = re.compile(r"(--[\w\-]+(?:[= ](?!-)[^\s>&|;]+)?)")
REQUIRED = ("key", "kind", "source", "status", "reviewed", "purpose", "pillar", "writes", "alarm")


def _cron_files() -> list[pathlib.Path]:
    d = ROOT / "deploy"
    files = [d / "cron.conf"] + sorted(d.glob("cron.*")) + sorted(d.glob("cron_*.conf"))
    out = []
    for f in files:
        if f.name in {"cron.conf"} and f in out:
            continue
        if "draft" in f.name or f in out:
            continue
        out.append(f)
    return out


def _cron_key(line: str) -> tuple[str, str]:
    parts = line.split()
    sched = " ".join(parts[:5])
    cmd = " ".join(parts[5:])
    scripts = SCRIPT_RE.findall(cmd)
    script = scripts[-1] if scripts else ""
    flags = " ".join(sorted(f.strip() for f in FLAG_RE.findall(cmd.split(">>")[0]) if f.strip()))
    sig = f"{script} {flags}".strip() or "cmd:" + hashlib.sha1(cmd.encode(), usedforsecurity=False).hexdigest()[:10]
    return f"cron|{sched}|{sig}", cmd


def discover() -> dict[str, dict]:
    """Every running component the repo mirrors declare, keyed by a stable signature."""
    found: dict[str, dict] = {}
    for f in _cron_files():
        lines = f.read_text().splitlines()
        # Fragment files installed by sed between "# BEGIN <name>" / "# END <name>" markers: only those blocks are
        # installed, so text outside them (install instructions that wrap onto a cron-looking line) is not a job.
        if f.name != "cron.conf" and any(l.startswith("# BEGIN") for l in lines):
            kept, inside = [], False
            for l in lines:
                if l.startswith("# BEGIN"):
                    inside = True
                elif l.startswith("# END"):
                    inside = False
                elif inside:
                    kept.append(l)
            lines = kept
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#") or re.match(r"^[A-Z_]+=", line):
                continue
            if len(line.split()) < 6:
                continue
            key, cmd = _cron_key(line)
            src = str(f.relative_to(ROOT))
            if key in found:
                if src not in found[key]["mirrors"]:  # the same job mirrored in cron.conf and an arm fragment
                    found[key]["mirrors"].append(src)
                    continue
                key = f"{key}|dup{len(found)}"  # genuinely repeated line inside one file
            found[key] = {"kind": "cron", "source": src, "mirrors": [src], "command": cmd}
    for pat in ("deploy/*.service", "deploy/*.timer", "scripts/*.service"):
        for f in sorted(ROOT.glob(pat)):
            found[f"systemd|{f.name}"] = {"kind": "systemd", "source": str(f.relative_to(ROOT)), "mirrors": [], "command": f.name}
    for f in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        found[f"workflow|{f.name}"] = {"kind": "workflow", "source": str(f.relative_to(ROOT)), "mirrors": [], "command": f.name}
    return found


def load() -> list[dict]:
    if not REGISTRY.exists():
        return []
    return tomllib.loads(REGISTRY.read_text()).get("component", [])


def _toml_str(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, list):
        return "[" + ", ".join(_toml_str(x) for x in v) + "]"
    s = str(v).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def _skeleton(key: str, meta: dict) -> str:
    script = SCRIPT_RE.findall(meta["command"])
    logs = re.findall(r">>\s*(\S+)", meta["command"])
    purpose = f"runs {script[-1]}" if script else f"{meta['kind']} {meta['command']}"
    fields = {
        "key": key, "kind": meta["kind"], "source": meta["source"], "status": "live", "reviewed": False,
        "purpose": purpose + " (auto - review)", "pillar": "UNSET", "writes": logs, "alarm": "UNSET",
        "schedule": key.split("|")[1] if meta["kind"] == "cron" else "", "mirrors": meta.get("mirrors", []),
        "command": meta["command"][:400],
    }
    return "[[component]]\n" + "\n".join(f"{k} = {_toml_str(v)}" for k, v in fields.items()) + "\n"


def check(verbose: bool = True) -> int:
    found, reg = discover(), load()
    by_key = {c.get("key"): c for c in reg}
    missing = sorted(k for k in found if k not in by_key)
    vanished = sorted(c["key"] for c in reg if c.get("status") == "live" and c.get("key") not in found)
    malformed = sorted(c.get("key", "?") for c in reg if any(f not in c for f in REQUIRED))
    dupes = sorted({c.get("key") for c in reg if [x.get("key") for x in reg].count(c.get("key")) > 1})
    debt = sorted(c["key"] for c in reg if c.get("status") == "live" and not c.get("reviewed"))
    if verbose:
        print(f"runtime registry: {len(found)} mirrored components, {len(reg)} registry entries, "
              f"{len(debt)} unreviewed (debt)")
        for label, items in (("UNREGISTERED (add with: python3 scripts/runtime_registry.py add)", missing),
                             ("LIVE IN REGISTRY BUT GONE FROM MIRRORS (mark status = \"retired\")", vanished),
                             ("MALFORMED (missing required fields)", malformed), ("DUPLICATE KEYS", dupes)):
            if items:
                print(f"  {label}: {len(items)}")
                for k in items:
                    print(f"    - {k}")
    return 1 if (missing or vanished or malformed or dupes) else 0


def add() -> int:
    found, reg = discover(), load()
    have = {c.get("key") for c in reg}
    new = [k for k in sorted(found) if k not in have]
    if not new:
        print("nothing to add")
        return 0
    head = "" if REGISTRY.exists() else (
        "# RUNTIME REGISTRY (ADR-0074). Every running piece of the bot, one entry each. CI fails on an unregistered\n"
        "# component (tests/test_runtime_registry.py). Fill purpose / pillar / writes / alarm and set reviewed = true.\n"
        "# pillar: BREADTH | DEPTH | EXECUTION | PROOF | PLUMBING.  alarm: what tells us it has stopped, or \"none\".\n"
        "# status: live | retired. Generated skeletons say \"(auto - review)\".\n\n")
    with REGISTRY.open("a") as fh:
        fh.write(head + "\n".join(_skeleton(k, found[k]) for k in new))
    print(f"added {len(new)} skeleton entries to {REGISTRY.relative_to(ROOT)}")
    return 0


def render() -> int:
    reg = [c for c in load() if c.get("status") == "live"]
    rows = ["# Runtime map (generated - do not hand-edit)",
            "",
            "Generated by `scripts/runtime_registry.py render` from `RUNTIME_REGISTRY.toml` (ADR-0074). Every running piece of the",
            "bot. Live columns (code SHA, last write, alarm state) are added by the governance scan where it can reach the VPS.",
            "",
            f"**Surface: {len(reg)} live components** · unreviewed: {sum(1 for c in reg if not c.get('reviewed'))}",
            "",
            "| Kind | When | What | Pillar | Writes | Alarm if it stops | Mirrored in | Reviewed |",
            "|---|---|---|---|---|---|---|---|"]
    for c in sorted(reg, key=lambda c: (c["kind"], c["source"], c["key"])):
        w = ", ".join(c.get("writes") or []) or "—"
        mir = ", ".join(f"`{m}`" for m in (c.get("mirrors") or [c["source"]]))
        when = f"`{c.get('schedule')}`" if c.get("schedule") else "—"
        rows.append(f"| {c['kind']} | {when} | {c['purpose']} | {c['pillar']} | {w} | {c['alarm']} | {mir} | "
                    f"{'yes' if c.get('reviewed') else 'no'} |")
    MAP.write_text("\n".join(rows) + "\n")
    print(f"wrote {MAP.name} ({len(reg)} live components)")
    return 0


def surface() -> int:
    reg = load()
    live = [c for c in reg if c.get("status") == "live"]
    print(f"SURFACE {len(live)} live components · {sum(1 for c in live if not c.get('reviewed'))} unreviewed · "
          f"{sum(1 for c in live if str(c.get('alarm', '')).startswith(('UNSET', 'none')))} with no alarm")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    sys.exit({"check": check, "add": add, "render": render, "surface": surface}[cmd]())
