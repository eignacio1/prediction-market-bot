"""Lossless port of NBA PAM v4 (two QS CSVs + docx taxonomy) into the PAM core store (W75.1).

The experiment scripts keep reading the old CSVs; this module only reads them. ``record_to_csv_row`` is
the inverse used by the round-trip test.
"""
from __future__ import annotations

import csv
import datetime as _dt
import json
import re
import zipfile
from pathlib import Path

from .schema import ArchetypeWeight, Basis, Classifier, Modifier, PamRecord

REPO = Path(__file__).resolve().parents[3]
V4 = REPO / "qualitative_data" / "pam_v4"
TAXONOMY_PATH = REPO / "qualitative_data" / "pam" / "nba" / "taxonomy.json"
DOCX = V4 / "Player_Attribute_Matrix_v4.docx"
SNAPSHOTS = ("QS-2026-05-28-001", "QS-2026-05-28-002")  # 002 supersedes 001 (backdated)
TAXONOMY_VERSION = "pam_v4"
MOD_COLS = [f"mod_{i:02d}" for i in range(1, 33)]


def _cells(xml: str) -> list[list[str]]:
    rows = []
    for tr in re.findall(r"<w:tr[ >].*?</w:tr>", xml, flags=re.S):
        row = []
        for tc in re.findall(r"<w:tc>.*?</w:tc>", tr, flags=re.S):
            paras = re.findall(r"<w:p[ >].*?</w:p>", tc, flags=re.S)
            row.append(" ".join("".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, flags=re.S)) for p in paras).strip())
        rows.append(row)
    return rows


def extract_taxonomy_from_docx(docx: Path = DOCX) -> dict:
    import html
    xml = zipfile.ZipFile(docx).read("word/document.xml").decode("utf-8")
    archetypes, modifiers = {}, {}
    for tbl in re.findall(r"<w:tbl>.*?</w:tbl>", xml, flags=re.S):
        for row in _cells(tbl):
            row = [html.unescape(c) for c in row]
            if row and re.fullmatch(r"PRF-\d+", row[0]) and len(row) >= 3:
                archetypes[row[0]] = {"name": row[1], "threshold": row[2], "signals": row[3] if len(row) > 3 else "",
                                      "notes": row[4] if len(row) > 4 else ""}
            elif row and re.fullmatch(r"M-\d+", row[0]) and len(row) >= 3:
                modifiers[row[0]] = {"name": row[1], "threshold": row[2], "notes": row[3] if len(row) > 3 else ""}
    return {"version": TAXONOMY_VERSION, "sport": "nba", "source": "qualitative_data/pam_v4/Player_Attribute_Matrix_v4.docx",
            "archetypes": archetypes, "modifiers": modifiers}


def load_taxonomy(path: Path = TAXONOMY_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _d(s: str):
    return _dt.date.fromisoformat(s) if s else None


def csv_row_to_record(row: dict, snapshot_id: str, tax: dict, supersedes: tuple[str, ...] = ()) -> PamRecord:
    prim, sec = int(row["prf_primary"]), int(row["prf_secondary"])
    if sec == 0:
        archs = (ArchetypeWeight(f"PRF-{prim}", 1.0, row["prf_primary_name"] or None),)
    else:
        w = float(row["prf_hybrid_weight"])
        archs = (ArchetypeWeight(f"PRF-{prim}", w, row["prf_primary_name"] or None),
                 ArchetypeWeight(f"PRF-{sec}", round(1.0 - w, 10), row["prf_secondary_name"] or None))
    mods = []
    for i, col in enumerate(MOD_COLS, 1):
        if row[col] == "1":
            t = tax["modifiers"].get(f"M-{i}", {})
            mods.append(Modifier(f"M-{i}", t.get("name"), t.get("threshold"), None))
    seasons = tuple(re.findall(r"\d{4}-\d{2}", row["classification_basis"]))
    return PamRecord(
        record_id=f"nba:{snapshot_id}:{row['player_id']}", sport="nba", player_id=row["player_id"],
        archetypes=archs, tier="deep", classified_by=Classifier("human", row["classified_by"], TAXONOMY_VERSION),
        effective_from=_d(row["effective_from"]), recorded_at=_d(row["classification_date"]),
        effective_until=_d(row["effective_until"]), basis=Basis(seasons=seasons, sources=("NBA.com box score", "PAM v4 framework"),
                                                                text=row["classification_basis"]),
        modifiers=tuple(mods), supersedes=supersedes, snapshot_id=snapshot_id, taxonomy_version=TAXONOMY_VERSION,
        id_map={"nba_person_id": row["player_id"]}, player_name=row["player_name"],
        backdated=row["backdated"] == "1", backdating_rationale=row["backdating_rationale"] or None,
        notes=row["notes"],
    )


def record_to_csv_row(rec: PamRecord) -> dict:
    a = list(rec.archetypes)
    prim = int(a[0].id.split("-")[1])
    sec = int(a[1].id.split("-")[1]) if len(a) > 1 else 0
    on = {m.id for m in rec.modifiers}
    row = {
        "player_id": rec.player_id, "player_name": rec.player_name or "",
        "classification_date": rec.recorded_at.isoformat(), "classified_by": rec.classified_by.name,
        "classification_basis": rec.basis.text, "effective_from": rec.effective_from.isoformat(),
        "effective_until": rec.effective_until.isoformat() if rec.effective_until else "",
        "backdated": "1" if rec.backdated else "0", "backdating_rationale": rec.backdating_rationale or "",
        "prf_primary": str(prim), "prf_secondary": str(sec),
        "prf_hybrid_weight": f"{a[0].weight:.2f}" if len(a) > 1 else "",
        "prf_primary_name": a[0].label or "", "prf_secondary_name": (a[1].label or "") if len(a) > 1 else "",
    }
    for i, col in enumerate(MOD_COLS, 1):
        row[col] = "1" if f"M-{i}" in on else "0"
    row["notes"] = rec.notes
    return row


def read_snapshot(snapshot_id: str) -> list[dict]:
    with (V4 / f"{snapshot_id}_classifications.csv").open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_records(tax: dict | None = None) -> list[PamRecord]:
    """001 first; each 002 record supersedes the same player's 001 record (002 is the backdated restatement)."""
    tax = tax or load_taxonomy()
    out = [csv_row_to_record(r, SNAPSHOTS[0], tax) for r in read_snapshot(SNAPSHOTS[0])]
    for r in read_snapshot(SNAPSHOTS[1]):
        out.append(csv_row_to_record(r, SNAPSHOTS[1], tax, supersedes=(f"nba:{SNAPSHOTS[0]}:{r['player_id']}",)))
    return out
