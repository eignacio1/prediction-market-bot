#!/usr/bin/env python3
"""W83.1: weekly NFL source-card capture (Sharp Football Analysis static tables). CAPTURE ONLY.

Fetches each CAPTURABLE static card's public page (anonymous GET), parses the table and
writes a dated, never-overwritten snapshot:

    exp_output/SOURCE_CAPTURE/<card>/<UTCstamp>.json      parsed rows + provenance
    exp_output/SOURCE_CAPTURE/<card>/<UTCstamp>.html.gz   raw HTML (audit copy)
    exp_output/SOURCE_CAPTURE/checks.jsonl                one line per page per run (heartbeat / gaps)

Semantics
  * as_of = the page's own JSON-LD dateModified where printed; fetched_at is always recorded.
  * A snapshot is written only when the table content changed vs the latest snapshot for that
    card (content hash over columns+rows); otherwise only a checks.jsonl line is appended.
  * Bounded: response cap MAX_BYTES per page, DAILY_BYTES_CAP written per UTC day.
  * PFR advanced passing is NOT captured: Cloudflare 403s a plain GET (W83.1 finding); it stays
    a browser one-off. Browser-only cards (NGS) likewise.
  * Feeds no model, adapter, sizing or run path.
"""
from __future__ import annotations

import argparse
import fcntl
import gzip
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE = ROOT / "exp_output" / "SOURCE_CAPTURE"
UA = ("Mozilla/5.0 (compatible; prediction-market-bot source-capture; "
      "+https://github.com/eignacio1/prediction-market-bot)")
BASE = "https://www.sharpfootballanalysis.com/stats-nfl/"
MAX_BYTES = 2_000_000
DAILY_BYTES_CAP = 5_000_000
# card -> (slug, parser kind)
CARDS = {
    "sharp-coverage-schemes": ("nfl-coverage-schemes", "wpdt"),
    "sharp-defensive-tendencies": ("nfl-defensive-tendencies", "wpdt"),
    "sharp-defensive-line-stats": ("nfl-defensive-line-stats", "wpdt"),
    "sharp-offensive-line-stats": ("nfl-offensive-line-stats", "wpdt"),
    "sharp-offensive-personnel": ("nfl-offensive-personnel", "personnel"),
}


class _Cell:
    __slots__ = ("text", "abbr_title")

    def __init__(self):
        self.text = []
        self.abbr_title = None


class TableParser(HTMLParser):
    """Collects <table> elements as {attrs, caption, headers, rows[[cell text]]}."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self._t = None
        self._row = None
        self._cell = None
        self._in_caption = False
        self._in_thead = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self._t = {"attrs": a, "caption": "", "headers": [], "rows": []}
        elif self._t is None:
            return
        elif tag == "caption":
            self._in_caption = True
        elif tag == "thead":
            self._in_thead = True
        elif tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = _Cell()
        elif tag == "abbr" and self._cell is not None:
            self._cell.abbr_title = a.get("title")

    def handle_endtag(self, tag):
        if self._t is None:
            return
        if tag == "table":
            self.tables.append(self._t)
            self._t = None
        elif tag == "caption":
            self._in_caption = False
        elif tag == "thead":
            self._in_thead = False
        elif tag in ("td", "th") and self._cell is not None and self._row is not None:
            txt = re.sub(r"\s+", " ", "".join(self._cell.text)).strip()
            self._row.append((txt, self._cell.abbr_title, tag))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._in_thead:
                self._t["headers"] = [c[0] for c in self._row]
            elif self._row:
                self._t["rows"].append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.text.append(data)
        elif self._in_caption and self._t is not None:
            self._t["caption"] += data


def parse_tables(html: str) -> list[dict]:
    p = TableParser()
    p.feed(html)
    return p.tables


def parse_as_of(html: str):
    """Page's own dateModified (JSON-LD) -> (datePublished, dateModified), None if absent."""
    pub = re.search(r'"datePublished"\s*:\s*"([^"]+)"', html)
    mod = re.search(r'"dateModified"\s*:\s*"([^"]+)"', html)
    return (pub.group(1) if pub else None, mod.group(1) if mod else None)


def _num(s: str):
    s = s.replace("%", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def parse_wpdt(html: str) -> dict:
    for t in parse_tables(html):
        if t["attrs"].get("id") == "table_1" and t["headers"] and t["rows"]:
            cols = t["headers"]
            rows = []
            for r in t["rows"]:
                cells = [c[0] for c in r]
                if len(cells) != len(cols):
                    continue
                rows.append({"team": cells[0], "values": {c: _num(v) for c, v in zip(cols[1:], cells[1:])}})
            return {"columns": cols, "rows": rows}
    raise ValueError("wpDataTable table_1 not found")


def parse_personnel(html: str) -> dict:
    for t in parse_tables(html):
        if "pt-pre" in (t["attrs"].get("class") or "") and t["rows"]:
            cols = t["headers"]
            rows = []
            for r in t["rows"]:
                # <td>rank</td><th scope=row><abbr title=Name>ABB</abbr> Name</th><td>..%</td>...
                if len(r) != len(cols) or r[1][2] != "th":
                    continue
                vals = {c: _num(v[0]) for c, v in zip(cols[2:], r[2:])}
                rows.append({"team": r[1][1] or r[1][0], "abbr": r[1][0].split(" ")[0],
                             "rank": _num(r[0][0]), "values": vals})
            return {"columns": cols, "rows": rows, "caption": t["caption"].strip()}
    raise ValueError("personnel table not found")


PARSERS = {"wpdt": parse_wpdt, "personnel": parse_personnel}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("response over %d bytes" % MAX_BYTES)
    return data.decode("utf-8", "replace")


def content_hash(parsed: dict) -> str:
    return hashlib.sha256(json.dumps([parsed["columns"], parsed["rows"]], sort_keys=True).encode()).hexdigest()


def latest_hash(card_dir: Path):
    snaps = sorted(card_dir.glob("*.json"))
    if not snaps:
        return None
    try:
        return json.loads(snaps[-1].read_text()).get("content_hash")
    except Exception:
        return None


def bytes_written_today(store: Path, now: datetime) -> int:
    day = now.strftime("%Y%m%d")
    total = 0
    for p in store.glob("*/%s*" % day):
        total += p.stat().st_size
    return total


def capture_card(card: str, store: Path, now: datetime, html: str) -> dict:
    slug, kind = CARDS[card]
    parsed = PARSERS[kind](html)
    pub, mod = parse_as_of(html)
    h = content_hash(parsed)
    card_dir = store / card
    status = "unchanged"
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    if h != latest_hash(card_dir):
        gz = gzip.compress(html.encode("utf-8"))
        if bytes_written_today(store, now) + len(gz) > DAILY_BYTES_CAP:
            return {"card": card, "status": "daily_cap_skipped", "rows": len(parsed["rows"])}
        card_dir.mkdir(parents=True, exist_ok=True)
        (card_dir / (stamp + ".html.gz")).write_bytes(gz)
        snap = {"card": card, "source_url": BASE + slug + "/", "fetched_at": now.isoformat(),
                "as_of": mod, "date_published": pub, "content_hash": h,
                "html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
                "n_rows": len(parsed["rows"]), **parsed}
        path = card_dir / (stamp + ".json")
        with open(path, "x") as f:  # never overwrite
            json.dump(snap, f, indent=1)
        status = "written"
    return {"card": card, "status": status, "rows": len(parsed["rows"]), "as_of": mod, "hash": h[:12]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--store", type=Path, default=DEFAULT_STORE)
    ap.add_argument("--log", type=Path, help="also append each result line to this file (one-off runs; cron redirects stdout)")
    ap.add_argument("--card", action="append", choices=sorted(CARDS), help="limit to card(s)")
    args = ap.parse_args(argv)
    store: Path = args.store
    store.mkdir(parents=True, exist_ok=True)
    lock = open(store / ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another source_capture run holds the lock; exiting")
        return 0
    now = datetime.now(timezone.utc)
    failures = 0
    for card in args.card or sorted(CARDS):
        slug = CARDS[card][0]
        try:
            res = capture_card(card, store, now, fetch(BASE + slug + "/"))
        except Exception as e:  # one page failing must not stop the rest
            failures += 1
            res = {"card": card, "status": "error", "error": "%s: %s" % (type(e).__name__, e)}
        res["ts"] = now.isoformat()
        with open(store / "checks.jsonl", "a") as f:
            f.write(json.dumps(res) + "\n")
        print(json.dumps(res))
        if args.log:
            with open(args.log, "a") as f:
                f.write("%s source_capture %s\n" % (now.isoformat(), json.dumps(res)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
