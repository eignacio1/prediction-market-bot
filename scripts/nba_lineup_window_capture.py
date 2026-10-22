#!/usr/bin/env python3
"""W83.2: NBA lineup-window capture. CAPTURE ONLY -- feeds no model, adapter, sizing or run path.

Times every official NBA injury-report status change and snapshots the KXNBAPTS book for the affected game(s)
just before and just after it (GG-985: retrospective candles could not observe the report-to-price window).

  Cadence: every 15 minutes. The official report is published on a 15-minute grid (HH:00/15/30/45 ET) and the HTTP
  Last-Modified header times each publish to the second, so a 15-minute poll bounds detection latency to <= ~18 min
  while `published_utc` stays exact. Cron minutes :03/:18/:33/:48 (a few minutes after each slot).

    exp_output/NBA/LINEUP_WINDOW/
        events.jsonl        one row per report change: changes, published_utc, detected_utc, affected events,
                            book_before (prior run's book, flagged stale if old), book_after (this run's book)
        followups.jsonl     book snapshots of affected events at the next FOLLOWUP_RUNS runs after a change
        control_books.jsonl hourly compact book for events tipping within 6h (no-change control stream)
        checks.jsonl        heartbeat, one line per run
        state.json          last report rows + last book (the "before" for the next change)

Source limits (disclosed): the PDF text does not reliably tie a player to a team, so the game is resolved by matching
the absent player's name to the KXNBAPTS market titles; a player with no market is `event_unresolved` (counted).
Public unauthenticated GETs only. Python 3.9-compatible.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE = ROOT / "exp_output" / "NBA" / "LINEUP_WINDOW"
IR_URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_{d}_{hh}_{mm}{ap}.pdf"
KALSHI = "https://api.elections.kalshi.com/trade-api/v2/markets"
ESPN_SB = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
STATUSES = ("Out", "Doubtful", "Questionable", "Probable", "Available")
FOLLOWUP_RUNS = 2
STALE_BEFORE_MIN = 20
ESPN_TO_KALSHI = {"GS": "GSW", "NO": "NOP", "SA": "SAS", "UTAH": "UTA", "WSH": "WAS", "NY": "NYK"}

_ROW = re.compile(r"(?:^|\s{2,})([A-Z][\w'.\-]*(?: [\w'.\-]+)?),\s*([\w'.\-]+(?: [\w'.\-]+)?)\s{2,}("
                  + "|".join(STATUSES) + r")\b\s*(.*)$")
_HDR = re.compile(r"Injury\s+Report:\s*(\d{1,2}/\d{1,2}/\d{2,4})\s+(\d{1,2}:\d{2})\s*(AM|PM)", re.I)


def norm_name(s: str) -> str:
    return re.sub(r"[^a-z ]", "", s.lower().replace("-", " ")).strip()


def reason_category(reason: str) -> str:
    r = reason.lower()
    for key, cat in (("g league", "g_league"), ("rest", "rest"), ("personal", "personal"), ("suspension", "suspension"),
                     ("not with team", "not_with_team"), ("injury", "injury")):
        if key in r:
            return cat
    return "other" if r.strip(" -") else "none"


def parse_report_text(text: str) -> dict:
    """{'header': 'MM/DD/YY HH:MM AM|PM' | None, 'rows': {norm 'first last': {name,status,reason}}, 'n_status_tokens'}."""
    m = _HDR.search(re.sub(r"\s+", " ", text))
    header = "%s %s %s" % (m.group(1), m.group(2), m.group(3).upper()) if m else None
    rows: Dict[str, dict] = {}
    for line in text.splitlines():
        mm = _ROW.search(line)
        if not mm:
            continue
        last, first, status, reason = mm.groups()
        name = "%s %s" % (first.strip(), last.strip())
        rows[norm_name(name)] = {"name": name, "status": status, "reason_cat": reason_category(reason)}
    n_tokens = sum(len(re.findall(r"\s{2,}(?:%s)\b" % "|".join(STATUSES), l)) for l in text.splitlines())
    return {"header": header, "rows": rows, "n_status_tokens": n_tokens}


def diff_rows(prev: Dict[str, dict], cur: Dict[str, dict]) -> List[dict]:
    out = []
    for k, v in cur.items():
        if k not in prev:
            out.append({"key": k, "name": v["name"], "kind": "added", "to": v["status"]})
        elif prev[k]["status"] != v["status"]:
            out.append({"key": k, "name": v["name"], "kind": "changed", "from": prev[k]["status"], "to": v["status"]})
    for k, v in prev.items():
        if k not in cur:
            out.append({"key": k, "name": v["name"], "kind": "removed", "from": v["status"]})
    return sorted(out, key=lambda c: (c["kind"], c["key"]))


def slot_candidates(now_utc: datetime, n: int = 3) -> List[datetime]:
    """Latest n 15-minute ET slots at/before now, newest first (as tz-aware ET datetimes)."""
    from zoneinfo import ZoneInfo
    et = now_utc.astimezone(ZoneInfo("America/New_York"))
    base = et.replace(minute=(et.minute // 15) * 15, second=0, microsecond=0)
    return [base - timedelta(minutes=15 * i) for i in range(n)]


def slot_url(slot_et: datetime) -> str:
    h12 = slot_et.hour % 12 or 12
    return IR_URL.format(d=slot_et.strftime("%Y-%m-%d"), hh="%02d" % h12, mm="%02d" % slot_et.minute,
                         ap="AM" if slot_et.hour < 12 else "PM")


def pdf_text(content: bytes) -> str:
    from pypdf import PdfReader
    rd = PdfReader(io.BytesIO(content))
    return "\n".join(p.extract_text(extraction_mode="layout") or "" for p in rd.pages)


def fetch_report(now_utc: datetime, get=requests.get) -> Optional[dict]:
    for slot in slot_candidates(now_utc):
        url = slot_url(slot)
        r = get(url, timeout=30)
        if r.status_code != 200:
            continue
        lm = r.headers.get("Last-Modified")
        pub = None
        if lm:
            from email.utils import parsedate_to_datetime
            pub = parsedate_to_datetime(lm).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {"slot_et": slot.strftime("%Y-%m-%d %H:%M"), "url": url, "published_utc": pub, "content": r.content}
    return None


def fetch_book(get=requests.get) -> List[dict]:
    mk, cursor = [], None
    for _ in range(10):
        params = {"series_ticker": "KXNBAPTS", "status": "open", "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        r = get(KALSHI, params=params, timeout=30)
        r.raise_for_status()
        d = r.json()
        mk.extend(d.get("markets", []))
        cursor = d.get("cursor")
        if not cursor:
            break
    return mk


def compact_book(markets: List[dict]) -> Dict[str, List[dict]]:
    """event_ticker -> [{t, p (player), k (strike), yb, ya, lp, v, oi}]"""
    out: Dict[str, List[dict]] = {}
    for m in markets:
        sub = m.get("no_sub_title") or m.get("yes_sub_title") or ""
        player = sub.split(":")[0].strip()
        out.setdefault(m["event_ticker"], []).append({
            "t": m["ticker"], "p": player, "k": m.get("floor_strike"),
            "yb": m.get("yes_bid_dollars"), "ya": m.get("yes_ask_dollars"), "lp": m.get("last_price_dollars"),
            "v": m.get("volume_fp") or m.get("volume"), "oi": m.get("open_interest_fp")})
    return out


def event_teams(event_ticker: str) -> Tuple[str, str]:
    code = event_ticker.split("-")[-1]
    body = re.sub(r"^\d{2}[A-Z]{3}\d{2}", "", code)
    return body[:3], body[3:]


def resolve_events(changes: List[dict], book: Dict[str, List[dict]]) -> Tuple[Dict[str, List[str]], int]:
    """event_ticker -> [absent player names]; and the number of changes with no market (event_unresolved)."""
    by_player = {}
    for ev, ms in book.items():
        for m in ms:
            by_player.setdefault(norm_name(m["p"]), set()).add(ev)
    hit: Dict[str, List[str]] = {}
    unresolved = 0
    for c in changes:
        evs = by_player.get(c["key"])
        if not evs:
            unresolved += 1
            continue
        for ev in evs:
            hit.setdefault(ev, []).append(c["name"])
    return hit, unresolved


def tips(scoreboard: dict) -> Dict[Tuple[str, str], str]:
    out = {}
    for ev in scoreboard.get("events", []):
        comp = ev["competitions"][0]["competitors"]
        t = {c["homeAway"]: ESPN_TO_KALSHI.get(c["team"]["abbreviation"], c["team"]["abbreviation"]) for c in comp}
        out[(t.get("away"), t.get("home"))] = ev["date"]
    return out


def minutes_to_tip(event_ticker: str, tip_map: Dict[Tuple[str, str], str], now: datetime) -> Optional[int]:
    away, home = event_teams(event_ticker)
    iso = tip_map.get((away, home))
    if not iso:
        return None
    tip = datetime.strptime(iso, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
    return int((tip - now).total_seconds() // 60)


def append(path: Path, row: dict) -> None:
    with path.open("a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def load_state(store: Path) -> dict:
    p = store / "state.json"
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return {}


def run(store: Path, now: datetime, report: Optional[dict], book_markets: Optional[List[dict]],
        scoreboard: Optional[dict], text_fn=pdf_text) -> dict:
    store.mkdir(parents=True, exist_ok=True)
    ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    st = load_state(store)
    hb = {"ts": ts, "report": "none", "book_events": 0, "changes": 0}
    book = compact_book(book_markets) if book_markets else {}
    hb["book_events"] = len(book)
    tip_map = tips(scoreboard) if scoreboard else {}
    cur_book = {ev: ms for ev, ms in book.items()
                if (minutes_to_tip(ev, tip_map, now) is None or minutes_to_tip(ev, tip_map, now) > -5)}

    # queued follow-ups from earlier changes
    pend = []
    for f in st.get("followups", []):
        evs = {e: cur_book[e] for e in f["events"] if e in cur_book}
        append(store / "followups.jsonl", {"ts": ts, "change_id": f["change_id"], "run_offset": f["left_total"] - f["left"] + 1,
                                           "book": evs})
        if f["left"] > 1:
            pend.append(dict(f, left=f["left"] - 1))

    if report is not None:
        parsed = parse_report_text(text_fn(report["content"]))
        rows = parsed["rows"]
        hb.update({"report": report["slot_et"], "published_utc": report["published_utc"], "rows": len(rows),
                   "status_tokens": parsed["n_status_tokens"], "header": parsed["header"]})
        prev_rows = st.get("rows")
        same_day = st.get("header_date") == (parsed["header"] or "").split(" ")[0]
        if report["slot_et"] != st.get("slot_et") and prev_rows is not None:
            if not same_day:
                hb["day_rollover"] = True
            else:
                changes = diff_rows(prev_rows, rows)
                hb["changes"] = len(changes)
                if changes:
                    hit, unresolved = resolve_events(changes, cur_book)
                    cid = hashlib.sha1((ts + report["slot_et"]).encode()).hexdigest()[:10]
                    before = st.get("book")
                    before_age = None
                    if st.get("book_ts"):
                        before_age = int((now - datetime.strptime(st["book_ts"], "%Y-%m-%dT%H:%M:%SZ")
                                          .replace(tzinfo=timezone.utc)).total_seconds() // 60)
                    append(store / "events.jsonl", {
                        "change_id": cid, "slot_et": report["slot_et"], "published_utc": report["published_utc"],
                        "detected_utc": ts, "changes": changes, "affected": hit, "event_unresolved": unresolved,
                        "minutes_to_tip": {e: minutes_to_tip(e, tip_map, now) for e in hit},
                        "book_before_ts": st.get("book_ts"), "book_before_stale": (before_age is None or before_age > STALE_BEFORE_MIN),
                        "book_before": {e: (before or {}).get(e) for e in hit},
                        "book_after": {e: cur_book.get(e) for e in hit}})
                    if hit:
                        pend.append({"change_id": cid, "events": sorted(hit), "left": FOLLOWUP_RUNS, "left_total": FOLLOWUP_RUNS})
        st.update({"rows": rows, "slot_et": report["slot_et"],
                   "header_date": (parsed["header"] or "").split(" ")[0]})
    st["followups"] = pend

    # hourly control stream: events within 6h of tip
    if now.minute < 15:
        ctl = {e: ms for e, ms in cur_book.items() if (minutes_to_tip(e, tip_map, now) or 99999) <= 360}
        if ctl:
            append(store / "control_books.jsonl", {"ts": ts, "book": ctl})

    if book:
        st["book"], st["book_ts"] = cur_book, ts
    (store / "state.json").write_text(json.dumps(st, sort_keys=True))
    append(store / "checks.jsonl", hb)
    return hb


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default=str(DEFAULT_STORE))
    args = ap.parse_args(argv)
    now = datetime.now(timezone.utc)
    store = Path(args.store)
    rc = 0
    try:
        report = fetch_report(now)
    except Exception as e:  # noqa: BLE001 -- a source outage must not crash the cron; it is logged and exits 2
        print("report fetch failed: %r" % (e,))
        report, rc = None, 2
    try:
        book = fetch_book()
    except Exception as e:  # noqa: BLE001
        print("book fetch failed: %r" % (e,))
        book, rc = None, 2
    try:
        sb = requests.get(ESPN_SB, timeout=30).json()
    except Exception:  # noqa: BLE001
        sb = None
    try:
        hb = run(store, now, report, book, sb)
    except Exception as e:  # noqa: BLE001
        print("run failed: %r" % (e,))
        return 2
    print(json.dumps(hb, sort_keys=True))
    return rc


if __name__ == "__main__":
    sys.exit(main())
