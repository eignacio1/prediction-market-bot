import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
import features as F  # noqa: E402
from injury_parse import flip, norm_name, parse_text  # noqa: E402


def utc(y, m, d, h, mi=0):
    return datetime(y, m, d, h, mi, tzinfo=timezone.utc)


def test_parse_rows():
    t = ("  09:30 (ET)  DAL@OKC  Dallas Mavericks   Williams,  Brandon      Out      Injury/Illness - Thumb\n"
         "                                          Porter Jr.,  Michael     Questionable    Injury\n")
    d = parse_text(t)
    assert d == {"brandon williams": "Out", "michael porter": "Questionable"}


def test_snapshot_never_after_tip_minus_4h():
    # game tips 2024-12-10 19:00 ET = 00:00Z on the 11th; ET date is the 10th
    tip = utc(2024, 12, 11, 0, 0)
    day = {f"{h:02d}:30": {"x": str(h)} for h in range(6, 24)}
    inj = {"2024-12-10": day}
    snap = F.snapshot(inj, tip)
    assert snap == {"x": "14"}  # 14:30 ET <= 15:00 ET (=tip-4h); 15:30 would be look-ahead


def test_snapshot_missing():
    assert F.snapshot({}, utc(2024, 12, 11, 0)) is None
    assert F.snapshot({"2024-12-10": {"21:30": {}}}, utc(2024, 12, 11, 0)) is None  # only a post-cutoff report


def test_status_token_subset_and_ambiguity():
    snap = {"branden oklahoma city thunder carlson": "Available", "a b": "Out", "a c b": "Out"}
    assert F.status_of(snap, "Branden Carlson") == "Available"
    assert F.status_of(snap, "A B") == "Out"   # exact wins
    assert F.status_of(snap, "Zed Q") is None
    assert norm_name("P.J. Washington Jr.") == "p j washington"
    assert flip("Washington,  P.J.") == "p j washington"
