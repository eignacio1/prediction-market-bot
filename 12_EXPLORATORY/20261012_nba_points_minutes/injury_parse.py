"""Parse NBA official injury-report PDFs (layout text) into {normalized_name: status}.

Team/game columns are scrambled by the layout, so only (name, status) pairs are kept;
association to a team happens downstream by matching the player's own prior team.
"""
from __future__ import annotations

import re
import unicodedata

STATUSES = ("Out", "Doubtful", "Questionable", "Probable", "Available")
_ROW = re.compile(r"(\S[^,\n]*?,\s+\S.*?)\s{3,}(Out|Doubtful|Questionable|Probable|Available)\b")
_SUFFIX = {"jr", "sr", "ii", "iii", "iv", "v"}


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z\s]", " ", s)
    toks = [t for t in s.split() if t not in _SUFFIX]
    return " ".join(toks)


def flip(last_first: str) -> str:
    last, _, first = last_first.partition(",")
    return norm_name(f"{first.strip()} {last.strip()}")


def parse_text(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        for m in _ROW.finditer(line):
            name = flip(re.sub(r"\s+", " ", re.split(r"\s{3,}", m.group(1).strip())[-1]).strip())
            if name:
                out[name] = m.group(2)
    return out


def parse_pdf(path: str) -> dict[str, str]:
    import pypdf

    r = pypdf.PdfReader(path)
    return parse_text("\n".join(p.extract_text(extraction_mode="layout") or "" for p in r.pages))
