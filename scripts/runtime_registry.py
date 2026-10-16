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

  check --box   also compare against the installed crontab and units on the VPS (GG-753): installed-but-unmirrored and
          mirrored-but-not-installed are failures. Matching is on script + flags, never the schedule (PIPE-08 retimes jobs).
  live    one cached ssh round trip -> last-write age per component, running-code SHA per service, healthcheck, silent arms;
          prints the RUNTIME block and SURFACE BUDGET GREEN/RED (W76.4). Writes exp_output/RUNTIME_LIVE/runtime_live.json
          for the Visual Dashboard builder. On the box itself (dashboard) the same probe runs locally, no ssh.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import inspect
import json
import pathlib
import re
import subprocess
import sys
import time

try:  # python3.11+ (the VPS runs 3.12); local dev machines may be 3.9 (GG-753)
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on python<3.11
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:
        tomllib = None  # type: ignore

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


def _mini_toml(text: str) -> dict:
    """Minimal reader for this registry's flat shape ([[component]] + `k = <json-compatible value>`), used only where
    neither tomllib nor tomli exists. Tested for equality with tomllib (tests/test_runtime_registry.py)."""
    comps: list[dict] = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[[component]]":
            comps.append({})
            continue
        m = re.match(r"^([A-Za-z_][\w\-]*)\s*=\s*(.+)$", line)
        if not m or not comps:
            raise ValueError(f"RUNTIME_REGISTRY.toml:{n}: unsupported line for the fallback reader: {raw!r}")
        comps[-1][m.group(1)] = json.loads(m.group(2))
    return {"component": comps}


def _loads(text: str) -> dict:
    return tomllib.loads(text) if tomllib is not None else _mini_toml(text)


def load() -> list[dict]:
    if not REGISTRY.exists():
        return []
    return _loads(REGISTRY.read_text()).get("component", [])


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



# --------------------------------------------------------------------------------------------------------------------
# W76.4 (ADR-0074, GG-742/743/753): the registry measured against the box, and the live columns.
# --------------------------------------------------------------------------------------------------------------------
VPS_HOST = "prediction-market-vps"
BOX_ROOT = "/opt/prediction-market-bot"
BEHIND_RED_H = 6.0           # a service running code more than this far behind box HEAD is a budget reason
LIVE_CACHE_S = 300           # one ssh round trip per 5 minutes, however many consumers ask
# Vendor / platform units present on the droplet that are not the bot's (so "installed but unmirrored" stays meaningful).
VENDOR_UNITS = ("droplet-agent", "iscsi", "syslog", "vmtoolsd", "vpc-peering", "dbus-org.")


def _sig(key: str) -> str:
    """Schedule-free signature of a cron key: script + sorted flags (PIPE-08 retimes jobs, so the schedule is not identity)."""
    return re.sub(r"\|dup\d+$", "", key.split("|", 2)[2]) if key.count("|") >= 2 else key


def crontab_sigs(text: str) -> set:
    out = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or re.match(r"^[A-Z_]+=", line) or len(line.split()) < 6:
            continue
        out.add(_sig(_cron_key(line)[0]))
    return out


def probe_local(payload: dict) -> dict:
    """Runs ON the box (shipped over ssh as source, or called in-process by the box's own dashboard). Self-contained,
    stdlib only, read-only. payload = {"root": str, "units": [str], "writes": [str]}."""
    import glob
    import json
    import os
    import subprocess
    import time
    from datetime import datetime, timezone

    root = payload.get("root", "/opt/prediction-market-bot")

    def run(cmd, timeout=20):
        try:
            r = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=timeout)
            return r.stdout
        except Exception:
            return ""

    now = time.time()
    out = {"ts": datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "epoch": now, "root": root}
    out["head"] = run(["git", "rev-parse", "HEAD"]).strip()
    out["head_ts"] = int(run(["git", "log", "-1", "--format=%ct"]).strip() or 0)
    out["crontab"] = run(["crontab", "-l"])
    uf = run(["find", "/etc/systemd/system", "-maxdepth", "1", "-type", "f", "(", "-name", "*.service", "-o", "-name", "*.timer", ")"])
    out["unit_files"] = sorted(os.path.basename(x) for x in uf.split())
    services = {}
    for u in payload.get("units", []):
        sh = run(["systemctl", "show", u, "-p", "LoadState,ActiveState,SubState,ActiveEnterTimestamp,NRestarts,Type"])
        d = dict(l.split("=", 1) for l in sh.splitlines() if "=" in l)
        since = d.get("ActiveEnterTimestamp", "")
        run_sha, behind_h, unapplied = "", None, 0
        if u.endswith(".service") and since and d.get("ActiveState") == "active":
            try:
                t = datetime.strptime(since, "%a %Y-%m-%d %H:%M:%S %Z").replace(tzinfo=timezone.utc)
                run_sha = run(["git", "rev-list", "-1", f"--before={int(t.timestamp())}", "HEAD"]).strip()
                if run_sha:
                    # W80P.1: "behind" = a file THIS service imports changed since run_sha -- the same import set
                    # the deploy restart policy uses (deploy_truth.unapplied_changes, one shared definition).
                    # An unrelated merge never makes a service behind (W79.1's false RED).
                    import sys
                    from pathlib import Path
                    sys.path.insert(0, os.path.join(root, "scripts", "ops"))
                    try:
                        import deploy_truth
                        hits, first = deploy_truth.unapplied_changes(Path(root), u[: -len(".service")], run_sha,
                                                                     out["head"])
                        unapplied = len(hits)
                        behind_h = round((now - first) / 3600, 2) if first else 0.0
                    finally:
                        sys.path.pop(0)
            except Exception:
                pass
        services[u] = {"load": d.get("LoadState"), "active": d.get("ActiveState"), "sub": d.get("SubState"), "since": since,
                       "restarts": d.get("NRestarts"), "run_sha": run_sha, "behind_h": behind_h, "unapplied_files": unapplied}
    out["services"] = services
    mt = {}
    for w in payload.get("writes", []):
        if not w or " " in w or "/" not in w:
            continue
        paths = glob.glob(w if os.path.isabs(w) else os.path.join(root, w)) or []
        times = [os.path.getmtime(x) for x in paths if os.path.exists(x)]
        mt[w] = max(times) if times else None
    out["writes"] = mt
    hl = run(["tail", "-n", "40", os.path.join(root, "logs", "health.log")])
    m = [l for l in hl.splitlines() if l.startswith("===")]
    out["health"] = {"line": m[-1] if m else "", "mtime": mt.get("logs/health.log") or None}
    try:
        out["deploy"] = json.load(open("/var/lib/pmbot-deploy/deploy_status.json"))
    except Exception:
        out["deploy"] = {}
    env = dict(os.environ, PYTHONPATH=os.path.join(root, "src"))
    try:
        r = subprocess.run([os.path.join(root, "venv", "bin", "python"), "-m", "prediction_market_bot.pregame_shadow.silent_arms", "--json"],
                           cwd=root, capture_output=True, text=True, timeout=45, env=env)
        out["silent"] = json.loads(r.stdout)
    except Exception as e:
        out["silent"] = {"error": f"{type(e).__name__}"}
    return out


def _payload(reg: list) -> dict:
    live = [c for c in reg if c.get("status") == "live"]
    units = sorted({c["key"].split("|", 1)[1] for c in live if c.get("kind") == "systemd"})
    writes = sorted({w for c in live for w in (c.get("writes") or [])} | {"logs/health.log"})
    return {"root": BOX_ROOT, "units": units, "writes": writes}


def _on_box() -> bool:
    return str(ROOT).startswith(BOX_ROOT) and pathlib.Path(BOX_ROOT, "venv").exists()


def fetch_probe(reg: list | None = None) -> dict:
    """One probe of the box: in-process when this code is running on the box, otherwise one ssh round trip."""
    reg = load() if reg is None else reg
    payload = _payload(reg)
    if _on_box():
        return probe_local(payload)
    src = "import json\n" + inspect.getsource(probe_local) + f"\nprint(json.dumps(probe_local({payload!r})))\n"
    r = subprocess.run(["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", VPS_HOST, "python3", "-"],
                       input=src, capture_output=True, text=True, timeout=90)
    if r.returncode != 0:
        raise RuntimeError(f"ssh probe failed rc={r.returncode}: {r.stderr.strip()[:200]}")
    return json.loads(r.stdout)


def check_box(probe: dict, reg: list | None = None) -> dict:
    """Registry vs the installed crontab and units (GG-753). Keys: unmirrored (installed, no entry), not_installed
    (live entry, nothing installed)."""
    reg = load() if reg is None else reg
    box = crontab_sigs(probe.get("crontab", ""))
    rsig = {c["key"]: _sig(c["key"]) for c in reg if c.get("kind") == "cron"}
    allsig = set(rsig.values())
    unmirrored = sorted(box - allsig)
    not_installed = sorted(k for k, sg in rsig.items() if sg not in box and next(c for c in reg if c["key"] == k).get("status") == "live")
    unit_files = set(probe.get("unit_files", []))
    reg_units = {c["key"].split("|", 1)[1]: c for c in reg if c.get("kind") == "systemd"}
    units_unmirrored = sorted(u for u in unit_files if u not in reg_units and not u.startswith(VENDOR_UNITS))
    units_not_installed = sorted(u for u, c in reg_units.items() if c.get("status") == "live" and u not in unit_files)
    return {"unmirrored": unmirrored, "not_installed": not_installed,
            "units_unmirrored": units_unmirrored, "units_not_installed": units_not_installed}


def _no_alarm(c: dict) -> bool:
    return str(c.get("alarm", "")).startswith(("UNSET", "none")) and not c.get("max_age_h")


def _unexplained(c: dict) -> bool:
    """A no-alarm component must say why (GG-743): `alarm = "none: <reason>"` with a real sentence, not an auto-stub."""
    a = str(c.get("alarm", ""))
    if a.startswith("UNSET"):
        return True
    if not a.startswith("none"):
        return False
    why = a.split(":", 1)[1].strip() if ":" in a else ""
    return len(why) < 15 or "(auto" in a


def evaluate(reg: list, probe: dict, now: float | None = None, registry_ok: bool = True) -> dict:
    """Rows (one per live component) + SURFACE BUDGET from a probe. Pure: no I/O."""
    now = probe.get("epoch", time.time()) if now is None else now
    rows, reasons = [], []
    for c in reg:
        if c.get("status") != "live":
            continue
        name = c["key"].split("|", 1)[1] if c["kind"] == "systemd" else None
        ages = [now - probe["writes"][w] for w in (c.get("writes") or []) if probe.get("writes", {}).get(w)]
        age_h = round(min(ages) / 3600, 2) if ages else None
        svc = probe.get("services", {}).get(name) if name else None
        row = {"key": c["key"], "kind": c["kind"], "purpose": c["purpose"], "pillar": c["pillar"], "alarm": c["alarm"],
               "schedule": c.get("schedule", ""), "reviewed": bool(c.get("reviewed")), "age_h": age_h,
               "max_age_h": c.get("max_age_h"), "no_alarm": _no_alarm(c), "unexplained": _no_alarm(c) and _unexplained(c),
               "state": "ok", "detail": ""}
        if c["kind"] == "workflow":
            row["state"] = "github"
        if svc is not None:
            row.update(active=f"{svc.get('active')}/{svc.get('sub')}", since=svc.get("since"), run_sha=(svc.get("run_sha") or "")[:8],
                       behind_h=svc.get("behind_h"), restarts=svc.get("restarts"))
            if svc.get("active") != "active":
                row["state"], row["detail"] = "DOWN", f"{svc.get('active')}/{svc.get('sub')}"
            elif (svc.get("behind_h") or 0) > BEHIND_RED_H:
                row["state"], row["detail"] = "BEHIND", f"running {svc['run_sha'][:8]}, {svc['behind_h']}h behind box HEAD"
        if row["state"] == "ok" and c.get("max_age_h"):
            if age_h is None:
                row["state"], row["detail"] = "STALE", "no write found"
            elif age_h > float(c["max_age_h"]):
                row["state"], row["detail"] = "STALE", f"last write {age_h}h ago (limit {c['max_age_h']}h)"
        if row["state"] == "ok" and row["no_alarm"]:
            row["state"] = "NO ALARM" if row["unexplained"] else "no alarm (reason given)"
        if row["state"] in ("DOWN", "BEHIND", "STALE"):
            reasons.append(f"{row['state']} {c['key']}: {row['detail']}")
        rows.append(row)
    h = probe.get("health", {}).get("line", "")
    m = re.search(r"(\d+) faults?", h)
    faults = int(m.group(1)) if m else None
    if faults:
        reasons.append(f"healthcheck: {h.strip('= ')}")
    silent = probe.get("silent") or {}
    for a in silent.get("arms", []):
        if a.get("status") == "silent":
            reasons.append(f"SILENT ARM {a.get('name')}: {a.get('text')}")
    if not registry_ok:
        reasons.append("registry check failing")
    return {"rows": rows, "reasons": reasons, "budget": "RED" if reasons else "GREEN",
            "counts": {"live": len(rows), "stale": sum(r["state"] in ("STALE", "DOWN", "BEHIND") for r in rows),
                       "no_alarm_unexplained": sum(r["unexplained"] for r in rows),
                       "no_alarm_reasoned": sum(r["no_alarm"] and not r["unexplained"] for r in rows),
                       "unreviewed": sum(not r["reviewed"] for r in rows)},
            "head": probe.get("head", "")[:8], "as_of": probe.get("ts"), "health": h.strip("= "),
            "deploy": probe.get("deploy", {}), "silent_text": [a.get("text") for a in silent.get("arms", [])]}


def live_cache_path() -> pathlib.Path:
    base = pathlib.Path(__import__("os").environ.get("XDG_CACHE_HOME") or pathlib.Path.home() / ".cache")
    return base / "pmbot" / "runtime_live.json"


def live(refresh: bool = False, use_cache: bool = True) -> dict:
    """Evaluation dict (see evaluate) from a cached-or-fresh probe; on failure {"error": ...}, never an exception."""
    cache = live_cache_path()
    try:
        if use_cache and not refresh and cache.exists() and time.time() - cache.stat().st_mtime < LIVE_CACHE_S:
            return json.loads(cache.read_text())
    except Exception:
        pass
    try:
        reg = load()
        probe = fetch_probe(reg)
        ev = evaluate(reg, probe, registry_ok=check(verbose=False) == 0)
        ev["box"] = check_box(probe, reg)
        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(ev))
        except Exception:
            pass
        return ev
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


_BG = {"thread": None}


def live_background() -> dict:
    """For web requests: never blocks. Returns the cached evaluation (even a stale one) and, if it is older than
    LIVE_CACHE_S, refreshes it on a daemon thread. {"pending": True} until the first probe lands."""
    import threading
    cache = live_cache_path()
    ev, age = None, None
    try:
        if cache.exists():
            ev, age = json.loads(cache.read_text()), time.time() - cache.stat().st_mtime
    except Exception:
        ev = None
    if ev is None or age is None or age >= LIVE_CACHE_S:
        t = _BG["thread"]
        if t is None or not t.is_alive():
            _BG["thread"] = threading.Thread(target=lambda: live(refresh=True), daemon=True)
            _BG["thread"].start()
    if ev is None:
        return {"pending": True}
    ev["cache_age_s"] = int(age or 0)
    return ev


def print_runtime_block(ev: dict) -> None:
    if "error" in ev:
        print(f"  UNKNOWN - box probe failed ({ev['error']}); SURFACE BUDGET cannot be computed from here")
        return
    c, b = ev["counts"], ev.get("box", {})
    print(f"  as of {ev['as_of']} · box HEAD {ev['head']} · {c['live']} live components · {c['unreviewed']} unreviewed · "
          f"{c['stale']} stale/down/behind · no alarm: {c['no_alarm_unexplained']} unexplained, {c['no_alarm_reasoned']} with a written reason")
    print(f"  registry vs box: {len(b.get('unmirrored', []))} installed-but-unmirrored · {len(b.get('not_installed', []))} mirrored-but-not-installed"
          f" · units {len(b.get('units_unmirrored', []))}/{len(b.get('units_not_installed', []))}")
    for k in b.get("unmirrored", []) + b.get("units_unmirrored", []):
        print(f"    UNMIRRORED (installed on box, no entry): {k}")
    for k in b.get("not_installed", []) + b.get("units_not_installed", []):
        print(f"    NOT INSTALLED (live entry, nothing on box): {k}")
    print(f"  healthcheck: {ev.get('health') or 'no summary line'} · deploy: {ev.get('deploy', {}).get('outcome', '?')} @ {ev.get('deploy', {}).get('ts', '?')}")
    for r in ev["rows"]:
        if r["kind"] == "systemd":
            print(f"  {r['key']:<38} {r.get('active', '?'):<16} run {r.get('run_sha') or '?'} · {r.get('behind_h')}h behind HEAD · restarts {r.get('restarts')}"
                  f"{'  <<< ' + r['state'] if r['state'] in ('DOWN', 'BEHIND', 'STALE') else ''}")
    for r in sorted(rows_bad := [r for r in ev["rows"] if r["state"] in ("STALE", "DOWN", "BEHIND", "NO ALARM") and r["kind"] != "systemd"],
                    key=lambda r: r["key"]):
        print(f"  {r['state']:<9} {r['key'][:90]}  {r['detail']}")
    print(f"  SURFACE BUDGET {ev['budget']}" + ("" if ev["budget"] == "GREEN" else ": " + "; ".join(ev["reasons"][:6])))


def cli_check_box() -> int:
    rc = check()
    try:
        probe = fetch_probe()
    except Exception as e:
        print(f"  box unreachable ({e}); cannot compare against the box")
        return 1
    b = check_box(probe)
    for label, items in (("INSTALLED ON BOX, NOT IN REGISTRY (register a GG)", b["unmirrored"] + b["units_unmirrored"]),
                         ("LIVE IN REGISTRY, NOT INSTALLED ON BOX (mark paused/retired with a reason)", b["not_installed"] + b["units_not_installed"])):
        print(f"  {label}: {len(items)}")
        for k in items:
            print(f"    - {k}")
    return 1 if (rc or any(b.values())) else 0


def cli_live() -> int:
    ev = live(refresh="--refresh" in sys.argv)
    if "--json" in sys.argv:
        print(json.dumps(ev))
    else:
        print_runtime_block(ev)
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check" and "--box" in sys.argv:
        sys.exit(cli_check_box())
    sys.exit({"check": check, "add": add, "render": render, "surface": surface, "live": cli_live}[cmd]())
