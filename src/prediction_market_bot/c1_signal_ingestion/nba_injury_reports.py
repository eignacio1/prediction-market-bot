"""Point-in-time NBA official injury-report snapshots for the EXP-040 challenger.

Source: the league's own Injury Report PDFs (ak-static.cms.nba.com/referee/injury). Same parser, same 2-hourly ET
slot grid and same ">= 4h before tip" rule as the frozen study (12_EXPLORATORY/20261012_nba_points_minutes), so the
live feature means what the training feature meant. A slot is only ever read at or after its own stamp
(``slot_utc <= now``) -- no look-ahead. Parsed slots are cached as JSON; a failed fetch is never cached."""
from __future__ import annotations

import json
import re
import unicodedata
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import et_date, et_midnight_utc

URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_{d}_{h:02d}{ap}.pdf"
SLOTS = [(11, "AM"), (1, "PM"), (3, "PM"), (5, "PM"), (7, "PM")]     # 11:30 13:30 15:30 17:30 19:30 ET
LEAD = timedelta(hours=4)
_ROW = re.compile(r"(\S[^,\n]*?,\s+\S.*?)\s{3,}(Out|Doubtful|Questionable|Probable|Available)\b")
_SUFFIX = {"jr", "sr", "ii", "iii", "iv", "v"}


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    toks = [t for t in re.sub(r"[^a-z\s]", " ", s).split() if t not in _SUFFIX]
    return " ".join(toks)


def _flip(last_first: str) -> str:
    last, _, first = last_first.partition(",")
    return norm_name(f"{first.strip()} {last.strip()}")


def parse_text(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        for m in _ROW.finditer(line):
            name = _flip(re.sub(r"\s+", " ", re.split(r"\s{3,}", m.group(1).strip())[-1]).strip())
            if name:
                out[name] = m.group(2)
    return out


def parse_pdf_bytes(data: bytes) -> dict[str, str]:
    import io

    import pypdf     # deliberately not guarded: a missing parser must fail the arm loudly, not log "no report"
    r = pypdf.PdfReader(io.BytesIO(data))
    return parse_text("\n".join(p.extract_text(extraction_mode="layout") or "" for p in r.pages))


def slot_key(h: int, ap: str) -> str:
    return f"{(h % 12) + (12 if ap == 'PM' else 0):02d}:30"


def _http_get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read()


class InjurySnapshots:
    def __init__(self, cache_dir: Path, fetch: Callable[[str], bytes] = _http_get,
                 parse: Callable[[bytes], dict[str, str]] = parse_pdf_bytes) -> None:
        self.dir, self._fetch, self._parse = Path(cache_dir), fetch, parse
        self._mem: dict[tuple[str, str], Optional[dict]] = {}

    def _slot(self, d, h: int, ap: str) -> Optional[dict]:
        key = (str(d), slot_key(h, ap))
        if key in self._mem:
            return self._mem[key]
        fp = self.dir / f"inj_{key[0]}_{key[1].replace(':', '')}.json"
        res = None
        if fp.exists():
            res = json.loads(fp.read_text())
        else:
            try:
                data = self._fetch(URL.format(d=key[0], h=h, ap=ap))
            except Exception:           # not published (yet) / network: leave uncached, fall back to earlier slot
                data = None
            if data is not None:
                res = self._parse(data)
                self.dir.mkdir(parents=True, exist_ok=True)
                fp.write_text(json.dumps(res, sort_keys=True))
        self._mem[key] = res
        return res

    def snapshot(self, game_start: datetime, now: datetime):
        """Latest report on the game's ET date with slot <= min(now, tip - 4h). -> (snap, slot_label, slot_utc)
        or (None, None, None). Never returns a slot stamped after ``now``."""
        d = et_date(game_start)
        base = et_midnight_utc(d)
        limit = min(now, game_start - LEAD)
        cands = []
        for h, ap in SLOTS:
            hh, mm = slot_key(h, ap).split(":")
            t = base + timedelta(hours=int(hh), minutes=int(mm))
            if t <= limit:
                cands.append((t, h, ap))
        for t, h, ap in sorted(cands, reverse=True):
            snap = self._slot(d, h, ap)
            if snap is not None:
                assert t <= now, "injury slot stamped after evaluation time"
                return snap, f"{d} {slot_key(h, ap)} ET", t
        return None, None, None
