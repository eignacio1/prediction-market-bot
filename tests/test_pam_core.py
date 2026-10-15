import csv
import datetime as dt
from pathlib import Path

import pytest

from prediction_market_bot.pam import (ArchetypeWeight, Basis, Classifier, PamRecord, PamStore,
                                       PamValidationError, pam_as_of)
from prediction_market_bot.pam import nba_port as nba

D = dt.date


def rec(rid="r1", pid="p1", eff=D(2024, 1, 1), until=None, rec_at=D(2024, 1, 1), tier="mass",
        archs=(("A", 1.0),), supersedes=(), sport="nfl", **kw):
    return PamRecord(record_id=rid, sport=sport, player_id=pid,
                     archetypes=tuple(ArchetypeWeight(a, w) for a, w in archs), tier=tier,
                     classified_by=Classifier("rule", "t", "1"), effective_from=eff, recorded_at=rec_at,
                     effective_until=until, basis=Basis(("2023",), ("pbp",), "x"), supersedes=supersedes, **kw)


# ---- weights / validation
def test_weights_must_sum_to_one():
    with pytest.raises(PamValidationError):
        rec(archs=(("A", 0.6), ("B", 0.3)))
    rec(archs=(("A", 0.6), ("B", 0.3), ("C", 0.1)))  # any number of archetypes


def test_validation_rejects_bad_fields():
    for kw in ({"tier": "x"}, {"archs": (("A", 0.5), ("A", 0.5))}, {"until": D(2023, 1, 1)}, {"confidence": 1.5},
               {"backdated": True}):
        with pytest.raises(PamValidationError):
            rec(**kw)


# ---- point-in-time
def test_pit_effective_after_as_of_never_returned(tmp_path):
    s = PamStore(tmp_path)
    s.append([rec(eff=D(2024, 9, 1))])
    assert s.as_of("nfl", "p1", D(2024, 8, 31)) is None            # before it takes effect
    assert s.as_of("nfl", "p1", D(2024, 9, 1)).record_id == "r1"   # positive control
    assert s.as_of("nfl", "p1", "2025-01-01").record_id == "r1"


def test_pit_until_is_exclusive(tmp_path):
    s = PamStore(tmp_path)
    s.append([rec(until=D(2024, 6, 1))])
    assert s.as_of("nfl", "p1", D(2024, 5, 31)) is not None
    assert s.as_of("nfl", "p1", D(2024, 6, 1)) is None


def test_known_at_hides_later_recorded(tmp_path):
    s = PamStore(tmp_path)
    s.append([rec(eff=D(2022, 1, 1), rec_at=D(2025, 1, 1))])  # backdated-style: made 2025, effective 2022
    assert s.as_of("nfl", "p1", D(2023, 1, 1)).record_id == "r1"
    assert s.as_of("nfl", "p1", D(2023, 1, 1), known_at=D(2024, 1, 1)) is None


def test_other_player_and_sport_isolated(tmp_path):
    s = PamStore(tmp_path)
    s.append([rec()])
    assert s.as_of("nfl", "p2", D(2025, 1, 1)) is None
    assert s.as_of("nba", "p1", D(2025, 1, 1)) is None
    assert pam_as_of("nfl", "p1", D(2025, 1, 1), root=tmp_path).record_id == "r1"


# ---- supersession / append-only
def test_supersession_new_wins_old_history_kept(tmp_path):
    s = PamStore(tmp_path)
    s.append([rec("old", eff=D(2023, 1, 1))])
    s.append([rec("new", eff=D(2024, 1, 1), rec_at=D(2024, 1, 1), supersedes=("old",), tier="deep")])
    assert s.as_of("nfl", "p1", D(2023, 6, 1)).record_id == "old"   # history before the superseder still reads old
    assert s.as_of("nfl", "p1", D(2024, 6, 1)).record_id == "new"
    assert len(s.load("nfl")) == 2                                    # nothing overwritten


def test_append_only_rejects_duplicate_and_unknown_supersede(tmp_path):
    s = PamStore(tmp_path)
    s.append([rec()])
    before = s.path("nfl").read_bytes()
    with pytest.raises(PamValidationError):
        s.append([rec()])
    with pytest.raises(PamValidationError):
        s.append([rec("z", supersedes=("nope",))])
    with pytest.raises(PamValidationError):
        s.append([rec("y", pid="other", supersedes=("r1",))])
    assert s.path("nfl").read_bytes() == before


def test_append_preserves_existing_bytes(tmp_path):
    s = PamStore(tmp_path)
    s.append([rec("a")])
    first = s.path("nfl").read_bytes()
    s.append([rec("b", pid="p2")])
    assert s.path("nfl").read_bytes().startswith(first)


def test_deep_beats_mass_on_tie(tmp_path):
    s = PamStore(tmp_path)
    s.append([rec("m", tier="mass"), rec("d", tier="deep")])
    assert s.as_of("nfl", "p1", D(2025, 1, 1)).record_id == "d"


# ---- round trip
def test_dict_round_trip(tmp_path):
    r = rec(archs=(("A", 0.7), ("B", 0.3)), id_map={"gsis": "x"}, confidence=0.8,
            backdated=True, backdating_rationale="why")
    assert PamRecord.from_dict(r.to_dict()) == r
    s = PamStore(tmp_path)
    s.append([r])
    assert s.load("nfl") == [r]


# ---- NBA v4 lossless port
@pytest.mark.parametrize("snap", nba.SNAPSHOTS)
def test_nba_csv_round_trip_lossless(snap):
    tax = nba.load_taxonomy()
    rows = nba.read_snapshot(snap)
    assert len(rows) == 50
    for row in rows:
        r = nba.csv_row_to_record(row, snap, tax)
        assert nba.record_to_csv_row(PamRecord.from_dict(r.to_dict())) == row


def test_nba_taxonomy_complete():
    tax = nba.load_taxonomy()
    assert len(tax["archetypes"]) == 15 and len(tax["modifiers"]) == 32
    assert all(v["name"] for v in tax["archetypes"].values())


def test_nba_store_pit_and_supersession(tmp_path):
    s = PamStore(tmp_path)
    s.append(nba.build_records())
    # LeBron: 001 effective 2025-10-22; 002 (backdated) effective 2022-10-18 supersedes it
    assert s.as_of("nba", "2544", D(2022, 10, 17)) is None
    r = s.as_of("nba", "2544", D(2023, 1, 1))
    assert r.snapshot_id == "QS-2026-05-28-002" and r.backdated
    assert s.as_of("nba", "2544", D(2025, 11, 1)).snapshot_id == "QS-2026-05-28-002"
    assert s.as_of("nba", "2544", D(2023, 1, 1), known_at=D(2026, 5, 27)) is None
    assert abs(sum(a.weight for a in r.archetypes) - 1) < 1e-9


def test_nba_committed_store_matches_csv():
    recs = PamStore().load("nba")
    assert [r.record_id for r in recs] == [r.record_id for r in nba.build_records()]
