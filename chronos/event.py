"""
Immutable TemporalEvent.

Events are the atomic units of change in ChronOS.
Identity is deterministic (SHA-256 over canonical serialization).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, FrozenSet, Optional, Sequence, Tuple

from .provenance import Provenance


def _canonical_json(obj: Any) -> str:
    """Deterministic JSON serialization for identity hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class TemporalEvent:
    """
    Immutable temporal event.

    Fields
    ------
    event_id : str
        Deterministic identity (SHA-256 hex).
    event_type : str
        Semantic type of the event (e.g. "TRANSITION", "OBSERVE").
    logical_time : int
        Authoritative logical time at which the event was committed.
    source : str
        Origin of the event (adapter name, actor, system).
    input_state_id : Optional[str]
        State identity before the transition (None for root events).
    result_state_id : Optional[str]
        State identity after the transition.
    causal_parents : Tuple[str, ...]
        Explicit causal parent event IDs (not inferred from time).
    payload : Any
        Domain payload (must be canonically serializable).
    payload_hash : str
        SHA-256 of the canonical payload.
    provenance : Provenance
        Provenance record for the event.
    wall_clock : Optional[str]
        Optional ISO-8601 wall-clock metadata (never authoritative).
    """

    event_type: str
    logical_time: int
    source: str
    input_state_id: Optional[str] = None
    result_state_id: Optional[str] = None
    causal_parents: Tuple[str, ...] = field(default_factory=tuple)
    payload: Any = None
    payload_hash: str = ""
    provenance: Provenance = field(default_factory=lambda: Provenance())
    wall_clock: Optional[str] = None
    event_id: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if not self.payload_hash:
            object.__setattr__(
                self,
                "payload_hash",
                _sha256_hex(_canonical_json(self.payload)),
            )
        identity_payload = {
            "event_type": self.event_type,
            "logical_time": self.logical_time,
            "source": self.source,
            "input_state_id": self.input_state_id,
            "result_state_id": self.result_state_id,
            "causal_parents": list(self.causal_parents),
            "payload_hash": self.payload_hash,
            "provenance": self.provenance.to_dict() if self.provenance else {},
            "wall_clock": self.wall_clock,
        }
        eid = _sha256_hex(_canonical_json(identity_payload))
        object.__setattr__(self, "event_id", eid)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "logical_time": self.logical_time,
            "source": self.source,
            "input_state_id": self.input_state_id,
            "result_state_id": self.result_state_id,
            "causal_parents": list(self.causal_parents),
            "payload": self.payload,
            "payload_hash": self.payload_hash,
            "provenance": self.provenance.to_dict() if self.provenance else {},
            "wall_clock": self.wall_clock,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TemporalEvent":
        prov = Provenance.from_dict(data.get("provenance") or {})
        return cls(
            event_type=data["event_type"],
            logical_time=int(data["logical_time"]),
            source=data["source"],
            input_state_id=data.get("input_state_id"),
            result_state_id=data.get("result_state_id"),
            causal_parents=tuple(data.get("causal_parents") or ()),
            payload=data.get("payload"),
            payload_hash=data.get("payload_hash", ""),
            provenance=prov,
            wall_clock=data.get("wall_clock"),
        )

    def identity(self) -> str:
        return self.event_id
