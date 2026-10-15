"""PAM core record (ADR-0075 section 3, CORE_SCHEMA.md): one sport-agnostic shape for every engine."""
from __future__ import annotations

import dataclasses as dc
import datetime as _dt
from typing import Any, Mapping

TIERS = ("mass", "deep")
CLASSIFIER_KINDS = ("human", "rule", "model")
WEIGHT_TOL = 1e-6


class PamValidationError(ValueError):
    pass


def to_date(v: Any) -> _dt.date:
    if isinstance(v, _dt.datetime):
        return v.date()
    if isinstance(v, _dt.date):
        return v
    try:
        return _dt.date.fromisoformat(str(v)[:10])
    except ValueError as e:
        raise PamValidationError(f"not a date: {v!r}") from e


@dc.dataclass(frozen=True)
class ArchetypeWeight:
    id: str
    weight: float
    label: str | None = None  # name as written by the classifier; canonical names live in the sport taxonomy


@dc.dataclass(frozen=True)
class Modifier:
    id: str
    name: str | None = None
    threshold: str | None = None  # activation criterion, copied from the taxonomy at write time
    evidence: str | None = None


@dc.dataclass(frozen=True)
class Classifier:
    kind: str  # human | rule | model
    name: str
    version: str | None = None


@dc.dataclass(frozen=True)
class Basis:
    seasons: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    text: str = ""


@dc.dataclass(frozen=True)
class PamRecord:
    record_id: str
    sport: str
    player_id: str
    archetypes: tuple[ArchetypeWeight, ...]
    tier: str
    classified_by: Classifier
    effective_from: _dt.date
    recorded_at: _dt.date  # when the classification was made (knowledge time)
    basis: Basis = Basis()
    modifiers: tuple[Modifier, ...] = ()
    effective_until: _dt.date | None = None  # exclusive; None = open
    confidence: float | None = None
    supersedes: tuple[str, ...] = ()
    snapshot_id: str = ""
    taxonomy_version: str = ""
    id_map: Mapping[str, str] = dc.field(default_factory=dict)
    player_name: str | None = None
    backdated: bool = False
    backdating_rationale: str | None = None
    notes: str = ""
    extra: Mapping[str, Any] = dc.field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.record_id or not self.sport or not self.player_id:
            raise PamValidationError("record_id, sport and player_id are required")
        if self.tier not in TIERS:
            raise PamValidationError(f"tier must be one of {TIERS}, got {self.tier!r}")
        if self.classified_by.kind not in CLASSIFIER_KINDS:
            raise PamValidationError(f"classified_by.kind must be one of {CLASSIFIER_KINDS}")
        if not self.archetypes:
            raise PamValidationError("at least one archetype is required")
        ids = [a.id for a in self.archetypes]
        if len(set(ids)) != len(ids):
            raise PamValidationError(f"duplicate archetype ids: {ids}")
        for a in self.archetypes:
            if not (0.0 < a.weight <= 1.0):
                raise PamValidationError(f"archetype weight out of (0,1]: {a}")
        total = sum(a.weight for a in self.archetypes)
        if abs(total - 1.0) > WEIGHT_TOL:
            raise PamValidationError(f"archetype weights must sum to 1, got {total}")
        mids = [m.id for m in self.modifiers]
        if len(set(mids)) != len(mids):
            raise PamValidationError(f"duplicate modifier ids: {mids}")
        if self.effective_until is not None and self.effective_until <= self.effective_from:
            raise PamValidationError("effective_until must be after effective_from")
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise PamValidationError("confidence must be in [0,1]")
        if self.backdated and not (self.backdating_rationale or "").strip():
            raise PamValidationError("backdated=True requires backdating_rationale (QTI-02)")

    # -- (de)serialisation -------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        d = dc.asdict(self)
        d["effective_from"] = self.effective_from.isoformat()
        d["recorded_at"] = self.recorded_at.isoformat()
        d["effective_until"] = self.effective_until.isoformat() if self.effective_until else None
        d["id_map"] = dict(self.id_map)
        d["extra"] = dict(self.extra)
        return d

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "PamRecord":
        return cls(
            record_id=d["record_id"], sport=d["sport"], player_id=str(d["player_id"]),
            archetypes=tuple(ArchetypeWeight(**a) for a in d["archetypes"]),
            tier=d["tier"], classified_by=Classifier(**d["classified_by"]),
            effective_from=to_date(d["effective_from"]), recorded_at=to_date(d["recorded_at"]),
            basis=Basis(seasons=tuple(d["basis"]["seasons"]), sources=tuple(d["basis"]["sources"]),
                        text=d["basis"]["text"]),
            modifiers=tuple(Modifier(**m) for m in d.get("modifiers", [])),
            effective_until=to_date(d["effective_until"]) if d.get("effective_until") else None,
            confidence=d.get("confidence"), supersedes=tuple(d.get("supersedes", ())),
            snapshot_id=d.get("snapshot_id", ""), taxonomy_version=d.get("taxonomy_version", ""),
            id_map=dict(d.get("id_map", {})), player_name=d.get("player_name"),
            backdated=bool(d.get("backdated", False)), backdating_rationale=d.get("backdating_rationale"),
            notes=d.get("notes", ""), extra=dict(d.get("extra", {})),
        )
