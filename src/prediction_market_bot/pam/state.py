"""PAM state tables (W129.4; design: 02_ARCHITECTURE_DESIGN/PAM_ATTRIBUTE_CLASSES.md section 3 A-C).

PamRecord (schema.py) is a classification over a date range. These three tables hold *state* that changes
game to game: player_state (class 1 role, class 4 security), availability_profile (class 2) and
trait_reliability (class 3). Every row carries ``as_of_ts`` (the decision time it describes), ``known_at``
(the earliest instant the information could be known), ``source`` and ``version``. There is ONE read path,
``StateStore.as_of(table, sport, key, decision_ts, known_at=...)``: a row whose ``known_at`` is later than
the cutoff is never returned, and a row whose ``as_of_ts`` is later than the decision time is never returned.
A null field means "not known at that time" and is never imputed here.
"""
from __future__ import annotations

import dataclasses as dc
import datetime as _dt
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from .schema import PamValidationError

DEFAULT_STATE_ROOT = Path(__file__).resolve().parents[3] / "qualitative_data" / "pam_state"
TABLES = ("player_state", "availability_profile", "trait_reliability")


def to_ts(v: Any) -> _dt.datetime:
    """Parse to a timezone-aware UTC datetime. Naive input is rejected: a time without a zone is a leak risk."""
    if isinstance(v, _dt.datetime):
        d = v
    else:
        try:
            d = _dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        except ValueError as e:
            raise PamValidationError(f"not a timestamp: {v!r}") from e
    if d.tzinfo is None:
        raise PamValidationError(f"timestamp has no timezone: {v!r}")
    return d.astimezone(_dt.timezone.utc)


def _iso(d: _dt.datetime) -> str:
    return d.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_common(r: Any) -> None:
    for f in ("sport", "source", "version"):
        if not getattr(r, f):
            raise PamValidationError(f"{type(r).__name__}.{f} is required")
    to_ts(r.as_of_ts), to_ts(r.known_at)  # both must parse and carry a zone; known_at > as_of_ts is a late correction


@dc.dataclass(frozen=True)
class PlayerState:
    """Class 1 (role state) and class 4 (role security), one row per player-game at the pre-tip decision time."""
    sport: str
    player_id: str
    game_id: str
    team: str
    as_of_ts: str
    known_at: str
    source: str
    version: str
    usage_rate_shrunk: float | None = None
    usage_rank_available: int | None = None
    teammates_out: int | None = None
    vacated_usage_share: float | None = None
    minutes_expected: float | None = None
    minutes_share_full_roster: float | None = None
    role_security: float | None = None   # class 4: not built; null by design (PREREG_PAM4)
    return_window: str | None = None     # class 4: not built; null by design
    extra: Mapping[str, Any] = dc.field(default_factory=dict)

    table = "player_state"

    def __post_init__(self) -> None:
        _check_common(self)
        for f in ("player_id", "game_id", "team"):
            if not getattr(self, f):
                raise PamValidationError(f"PlayerState.{f} is required")
        for f in ("usage_rate_shrunk", "vacated_usage_share", "minutes_share_full_roster"):
            v = getattr(self, f)
            if v is not None and not 0.0 <= v <= 1.0:
                raise PamValidationError(f"PlayerState.{f} outside [0,1]: {v}")
        if self.minutes_expected is not None and not 0.0 <= self.minutes_expected <= 60.0:
            raise PamValidationError(f"minutes_expected outside [0,60]: {self.minutes_expected}")
        for f in ("usage_rank_available", "teammates_out"):
            v = getattr(self, f)
            if v is not None and v < 0:
                raise PamValidationError(f"PlayerState.{f} negative: {v}")

    @property
    def key(self) -> str:
        return self.player_id

    def to_dict(self) -> dict:
        d = dc.asdict(self)
        d["extra"] = dict(self.extra)
        return d

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "PlayerState":
        return cls(**{k: v for k, v in d.items() if k in {f.name for f in dc.fields(cls)}})


@dc.dataclass(frozen=True)
class AvailabilityProfile:
    """Class 2 (availability distribution), one row per player per date."""
    sport: str
    player_id: str
    as_of_ts: str
    known_at: str
    source: str
    version: str
    gp_by_season: Mapping[str, list] = dc.field(default_factory=dict)  # season -> [games_played, team_games]
    missed_by_body_part: Mapping[str, int] | None = None
    recurrence_flags: Mapping[str, bool] | None = None
    expected_games_dist: Mapping[str, float] | None = None  # {"alpha": .., "beta": ..} (not built in W129.4)
    extra: Mapping[str, Any] = dc.field(default_factory=dict)

    table = "availability_profile"

    def __post_init__(self) -> None:
        _check_common(self)
        if not self.player_id:
            raise PamValidationError("AvailabilityProfile.player_id is required")
        for s, v in self.gp_by_season.items():
            if len(v) != 2 or v[0] < 0 or v[1] < v[0]:
                raise PamValidationError(f"gp_by_season[{s}] must be [gp, team_games] with 0<=gp<=team_games: {v}")

    @property
    def key(self) -> str:
        return self.player_id

    def to_dict(self) -> dict:
        d = dc.asdict(self)
        d["extra"] = dict(self.extra)
        return d

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "AvailabilityProfile":
        return cls(**{k: v for k, v in d.items() if k in {f.name for f in dc.fields(cls)}})


@dc.dataclass(frozen=True)
class TraitReliability:
    """Class 3 (trait stability), one row per stat per fit version. known_at is when the fit finished its data window."""
    sport: str
    stat: str
    as_of_ts: str
    known_at: str
    source: str
    version: str
    rate_def: str | None = None
    r_year_to_year: float | None = None
    r_split_half: float | None = None
    r_split_half_interval: list | None = None
    k_stabilize: float | None = None
    k_unit: str | None = None
    prior_rule: str | None = None
    fit_seasons: list = dc.field(default_factory=list)
    extra: Mapping[str, Any] = dc.field(default_factory=dict)

    table = "trait_reliability"
    known_after_as_of_ok = True  # a fit applies to decisions after it finished, not to its own as_of_ts

    def __post_init__(self) -> None:
        _check_common(self)
        if not self.stat:
            raise PamValidationError("TraitReliability.stat is required")
        for f in ("r_year_to_year", "r_split_half"):
            v = getattr(self, f)
            if v is not None and not -1.0 <= v <= 1.0:
                raise PamValidationError(f"TraitReliability.{f} outside [-1,1]: {v}")

    @property
    def key(self) -> str:
        return self.stat

    def to_dict(self) -> dict:
        d = dc.asdict(self)
        d["extra"] = dict(self.extra)
        return d

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "TraitReliability":
        return cls(**{k: v for k, v in d.items() if k in {f.name for f in dc.fields(cls)}})


_CLASSES = {"player_state": PlayerState, "availability_profile": AvailabilityProfile,
            "trait_reliability": TraitReliability}


class StateStore:
    """Append-only JSONL, one file per (sport, table): ``<root>/<sport>/<table>.jsonl``."""

    def __init__(self, root: Path | str | None = None):
        self.root = Path(root) if root else DEFAULT_STATE_ROOT

    def path(self, sport: str, table: str) -> Path:
        if table not in _CLASSES:
            raise PamValidationError(f"unknown table {table!r}; one of {TABLES}")
        return self.root / sport / f"{table}.jsonl"

    def load(self, sport: str, table: str) -> list:
        p = self.path(sport, table)
        if not p.exists():
            return []
        cls = _CLASSES[table]
        with p.open(encoding="utf-8") as fh:
            return [cls.from_dict(json.loads(line)) for line in fh if line.strip()]

    def append(self, rows: Iterable[Any]) -> int:
        by: dict[tuple[str, str], list[str]] = {}
        for r in rows:
            by.setdefault((r.sport, r.table), []).append(json.dumps(r.to_dict(), sort_keys=True, ensure_ascii=False))
        n = 0
        for (sport, table), lines in by.items():
            p = self.path(sport, table)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("a", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            n += len(lines)
        return n

    def as_of(self, table: str, sport: str, key: str, decision_ts: Any, known_at: Any | None = None,
              game_id: str | None = None):
        """The one read path. Latest row for ``key`` with as_of_ts <= decision_ts AND known_at <= cutoff.

        ``known_at`` is the knowledge cutoff (default: decision_ts). Returns None when nothing was visible.
        ``game_id`` pins a player_state lookup to that game's own row (the row written for that decision).
        """
        return as_of_rows(self.load(sport, table), key, decision_ts, known_at, game_id)


def as_of_rows(rows: Iterable[Any], key: str, decision_ts: Any, known_at: Any | None = None,
               game_id: str | None = None):
    dt = to_ts(decision_ts)
    cutoff = to_ts(known_at) if known_at is not None else dt
    best = None
    best_k = None
    for r in rows:
        if r.key != key:
            continue
        if game_id is not None and getattr(r, "game_id", game_id) != game_id:
            continue
        a, k = to_ts(r.as_of_ts), to_ts(r.known_at)
        if k > cutoff:
            continue
        if a > dt and not getattr(r, "known_after_as_of_ok", False):
            continue
        rank = (a, k, r.version)
        if best_k is None or rank > best_k:
            best, best_k = r, rank
    return best


def team_as_of(rows: Iterable[PlayerState], player_id: str, decision_ts: Any, known_at: Any | None = None) -> str | None:
    """The team a player is on at the decision time; a trade changes it from its date."""
    r = as_of_rows(rows, player_id, decision_ts, known_at)
    return r.team if r else None
