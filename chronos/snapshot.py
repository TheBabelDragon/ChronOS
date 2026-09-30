"""
Explicit temporal snapshots.

A snapshot is an identity-addressable reference to an immutable
TemporalState plus integrity metadata. It does not own a separate
copy of history.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Optional

from .provenance import Provenance
from .state import TemporalState
from .store import TemporalStore


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Snapshot:
    """
    Explicit checkpoint referencing a committed TemporalState.
    """

    state_id: str
    timeline_id: str
    logical_time: int
    state_root: Any
    created_from: Optional[str] = None  # parent state id
    provenance: Provenance = field(default_factory=Provenance)
    snapshot_id: str = field(default="", init=False)

    def __post_init__(self) -> None:
        identity_payload = {
            "state_id": self.state_id,
            "timeline_id": self.timeline_id,
            "logical_time": self.logical_time,
            "state_root": self.state_root,
            "created_from": self.created_from,
            "provenance": self.provenance.to_dict() if self.provenance else {},
        }
        sid = _sha256_hex(_canonical_json(identity_payload))
        object.__setattr__(self, "snapshot_id", sid)

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "state_id": self.state_id,
            "timeline_id": self.timeline_id,
            "logical_time": self.logical_time,
            "state_root": self.state_root,
            "created_from": self.created_from,
            "provenance": self.provenance.to_dict() if self.provenance else {},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            state_id=data["state_id"],
            timeline_id=data["timeline_id"],
            logical_time=int(data["logical_time"]),
            state_root=data.get("state_root"),
            created_from=data.get("created_from"),
            provenance=Provenance.from_dict(data.get("provenance") or {}),
        )

    def identity(self) -> str:
        return self.snapshot_id


def create_snapshot(
    state: TemporalState,
    *,
    provenance: Optional[Provenance] = None,
) -> Snapshot:
    """Create a snapshot from a committed TemporalState."""
    prov = provenance or Provenance(
        source="chronos",
        operation="SNAPSHOT",
        context={"state_id": state.state_id},
    )
    return Snapshot(
        state_id=state.state_id,
        timeline_id=state.timeline_id,
        logical_time=state.logical_time,
        state_root=state.state_root,
        created_from=state.parent_state,
        provenance=prov,
    )


def restore_snapshot(
    snapshot: Snapshot,
    store: TemporalStore,
) -> TemporalState:
    """
    Resolve a snapshot back to its committed TemporalState via the store.

    Does not mutate any committed state. Raises if the referenced state
    is absent from the store.
    """
    st = store.get_state(snapshot.state_id)
    if st is None:
        raise ValueError(
            f"Snapshot {snapshot.snapshot_id} references missing state "
            f"{snapshot.state_id}"
        )
    if st.timeline_id != snapshot.timeline_id or st.logical_time != snapshot.logical_time:
        raise ValueError(
            f"Snapshot/state mismatch for {snapshot.snapshot_id}"
        )
    return st


def compare_snapshots(a: Snapshot, b: Snapshot) -> dict:
    """
    Compare two snapshots. Returns a structured diff of identity fields.
    """
    return {
        "same_snapshot": a.snapshot_id == b.snapshot_id,
        "same_state": a.state_id == b.state_id,
        "same_timeline": a.timeline_id == b.timeline_id,
        "same_logical_time": a.logical_time == b.logical_time,
        "same_root": a.state_root == b.state_root,
        "a": {
            "snapshot_id": a.snapshot_id,
            "state_id": a.state_id,
            "timeline_id": a.timeline_id,
            "logical_time": a.logical_time,
        },
        "b": {
            "snapshot_id": b.snapshot_id,
            "state_id": b.state_id,
            "timeline_id": b.timeline_id,
            "logical_time": b.logical_time,
        },
    }
