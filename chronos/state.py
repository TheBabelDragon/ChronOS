"""
Immutable TemporalState.

State identity is deterministic (SHA-256 over canonical serialization
of the fields defined in docs/MODEL.md).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Optional, Tuple

from .provenance import Provenance


def _canonical_json(obj: Any) -> str:
    """Deterministic JSON serialization for identity hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonicalize(value: Any) -> Any:
    """
    Produce a canonically ordered, JSON-serializable structure.

    Supported: None, bool, int, float, str, list, tuple, dict
    (nested). Unsupported types raise TypeError.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [canonicalize(v) for v in value]
    if isinstance(value, dict):
        # sort keys for stability; reject non-string keys
        out = {}
        for k in sorted(value.keys(), key=lambda x: (str(type(x)), str(x))):
            if not isinstance(k, str):
                raise TypeError(
                    f"Unsupported state key type {type(k).__name__!r}; "
                    "keys must be str for stable identity"
                )
            out[k] = canonicalize(value[k])
        return out
    raise TypeError(
        f"Unsupported state value type {type(value).__name__!r}; "
        "provide a JSON-serializable structure or an explicit serializer"
    )


@dataclass(frozen=True)
class TemporalState:
    """
    Immutable committed temporal state.

    Identity fields (docs/MODEL.md):
        timeline_id, logical_time, parent_state, causal_parents,
        state_root, provenance
    """

    timeline_id: str
    logical_time: int
    state_root: Any
    parent_state: Optional[str] = None
    causal_parents: Tuple[str, ...] = field(default_factory=tuple)
    provenance: Provenance = field(default_factory=Provenance)
    state_id: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if self.logical_time < 0:
            raise ValueError("logical_time must be non-negative")
        if not self.timeline_id:
            raise ValueError("timeline_id is required")
        # Fail clearly on unsupported values rather than unstable identity
        try:
            canon_root = canonicalize(self.state_root)
        except TypeError as exc:
            raise TypeError(
                f"state_root is not canonically serializable: {exc}"
            ) from exc
        object.__setattr__(self, "state_root", canon_root)

        identity_payload = {
            "timeline_id": self.timeline_id,
            "logical_time": self.logical_time,
            "parent_state": self.parent_state,
            "causal_parents": list(self.causal_parents),
            "state_root": canon_root,
            "provenance": self.provenance.to_dict() if self.provenance else {},
        }
        sid = _sha256_hex(_canonical_json(identity_payload))
        object.__setattr__(self, "state_id", sid)

    def to_dict(self) -> dict:
        return {
            "state_id": self.state_id,
            "timeline_id": self.timeline_id,
            "logical_time": self.logical_time,
            "parent_state": self.parent_state,
            "causal_parents": list(self.causal_parents),
            "state_root": self.state_root,
            "provenance": self.provenance.to_dict() if self.provenance else {},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TemporalState":
        prov = Provenance.from_dict(data.get("provenance") or {})
        return cls(
            timeline_id=data["timeline_id"],
            logical_time=int(data["logical_time"]),
            state_root=data.get("state_root"),
            parent_state=data.get("parent_state"),
            causal_parents=tuple(data.get("causal_parents") or ()),
            provenance=prov,
        )

    def identity(self) -> str:
        return self.state_id

    def integrity_record(self) -> dict:
        """Compact integrity metadata (no wall-clock)."""
        return {
            "state_id": self.state_id,
            "timeline_id": self.timeline_id,
            "logical_time": self.logical_time,
            "parent_state": self.parent_state,
            "causal_parents": list(self.causal_parents),
        }
