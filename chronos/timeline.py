"""
Timeline — core execution object of ChronOS.

Owns the graph of immutable states linked by append-only events,
with a movable head. Does not own domain execution semantics.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from .clock import LogicalClock
from .event import TemporalEvent
from .provenance import Provenance
from .state import TemporalState, canonicalize
from .store import TemporalStore


def _new_timeline_id(prefix: str = "tl") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


@dataclass
class Timeline:
    """
    Mutable handle over immutable temporal history.

    The handle (head, clock) is mutable; committed states and events
    in the store are not.
    """

    store: TemporalStore
    timeline_id: str
    clock: LogicalClock
    root_state_id: str
    head_state_id: str
    parent_timeline_id: Optional[str] = None
    fork_state_id: Optional[str] = None
    name: Optional[str] = None
    _last_event_id: Optional[str] = field(default=None, repr=False)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def create_root(
        cls,
        state_root: Any = None,
        *,
        store: Optional[TemporalStore] = None,
        timeline_id: Optional[str] = None,
        provenance: Optional[Provenance] = None,
        source: str = "chronos",
    ) -> "Timeline":
        """Create a new root timeline with an initial committed state."""
        if store is None:
            store = TemporalStore()
        tid = timeline_id or _new_timeline_id()
        clock = LogicalClock()
        # Root occupies logical time 0 without a prior tick.
        prov = provenance or Provenance(source=source, operation="CREATE_ROOT")
        root = TemporalState(
            timeline_id=tid,
            logical_time=0,
            state_root=state_root if state_root is not None else {},
            parent_state=None,
            causal_parents=(),
            provenance=prov,
        )
        store.put_state(root)
        return cls(
            store=store,
            timeline_id=tid,
            clock=clock,
            root_state_id=root.state_id,
            head_state_id=root.state_id,
            parent_timeline_id=None,
            fork_state_id=None,
        )

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def head(self) -> TemporalState:
        st = self.store.get_state(self.head_state_id)
        if st is None:
            raise RuntimeError(f"Head state missing: {self.head_state_id}")
        return st

    def root(self) -> TemporalState:
        st = self.store.get_state(self.root_state_id)
        if st is None:
            raise RuntimeError(f"Root state missing: {self.root_state_id}")
        return st

    def get_state(self, state_id: str) -> Optional[TemporalState]:
        return self.store.get_state(state_id)

    def events(self) -> List[TemporalEvent]:
        """Events whose result state belongs to this timeline."""
        return self.store.events_for_timeline(self.timeline_id)

    def states(self) -> List[TemporalState]:
        """Committed states belonging to this timeline (insertion order)."""
        return [
            s
            for s in self.store.states()
            if s.timeline_id == self.timeline_id
        ]

    # ------------------------------------------------------------------
    # Transition
    # ------------------------------------------------------------------

    def transition(
        self,
        new_state_root: Any,
        *,
        event_type: str = "TRANSITION",
        source: str = "chronos",
        payload: Any = None,
        causal_parents: Optional[Sequence[str]] = None,
        provenance: Optional[Provenance] = None,
        wall_clock: Optional[str] = None,
    ) -> Tuple[TemporalEvent, TemporalState]:
        """
        Apply a domain transition:

            current state  →  operation  →  event  →  immutable new state  →  new head

        The previous state is unchanged. The event carries enough
        information to reconstruct the transition on replay.
        """
        parent = self.head()
        t = self.clock.tick()
        if causal_parents is None:
            # Default causal parent is the previous event on this timeline
            # when the caller does not supply explicit causal edges.
            parents = (self._last_event_id,) if self._last_event_id else ()
        else:
            parents = tuple(causal_parents)

        prov = provenance or Provenance(
            source=source,
            operation=event_type,
            parent_events=parents,
        )
        new_state = TemporalState(
            timeline_id=self.timeline_id,
            logical_time=t,
            state_root=new_state_root,
            parent_state=parent.state_id,
            causal_parents=parents,
            provenance=prov,
        )
        event = TemporalEvent(
            event_type=event_type,
            logical_time=t,
            source=source,
            input_state_id=parent.state_id,
            result_state_id=new_state.state_id,
            causal_parents=parents,
            payload=payload if payload is not None else {
                "state_root": canonicalize(new_state_root),
            },
            provenance=prov,
            wall_clock=wall_clock,
        )
        self.store.put_state(new_state)
        self.store.append_event(event)
        self.head_state_id = new_state.state_id
        self._last_event_id = event.event_id
        return event, new_state

    # ------------------------------------------------------------------
    # Fork / snapshot / replay / trace (delegates)
    # ------------------------------------------------------------------

    def fork(
        self,
        state_id: Optional[str] = None,
        *,
        name: Optional[str] = None,
        timeline_id: Optional[str] = None,
    ) -> "Timeline":
        from .branch import fork as _fork

        return _fork(self, state_id=state_id, name=name, timeline_id=timeline_id)

    def snapshot(self, state_id: Optional[str] = None):
        from .snapshot import create_snapshot

        st = self.get_state(state_id) if state_id else self.head()
        if st is None:
            raise ValueError(f"Unknown state: {state_id}")
        return create_snapshot(st)

    def replay(
        self,
        *,
        from_state: Optional[str] = None,
        to_state: Optional[str] = None,
        event_handler: Optional[Callable[..., Any]] = None,
    ):
        from .replay import replay as _replay

        return _replay(
            self,
            from_state=from_state,
            to_state=to_state,
            event_handler=event_handler,
        )

    def trace(self, state_id: Optional[str] = None) -> List[dict]:
        """Return provenance / causal history for a state (default: head)."""
        st = self.get_state(state_id) if state_id else self.head()
        if st is None:
            raise ValueError(f"Unknown state: {state_id}")
        records: List[dict] = []
        current: Optional[TemporalState] = st
        seen = set()
        while current is not None and current.state_id not in seen:
            seen.add(current.state_id)
            records.append(
                {
                    "state_id": current.state_id,
                    "logical_time": current.logical_time,
                    "parent_state": current.parent_state,
                    "causal_parents": list(current.causal_parents),
                    "provenance": current.provenance.to_dict(),
                }
            )
            if current.parent_state:
                current = self.store.get_state(current.parent_state)
            else:
                break
        records.reverse()
        return records

    def integrity(self) -> dict:
        """Integrity record for the current head (no wall-clock)."""
        h = self.head()
        return {
            "timeline_id": self.timeline_id,
            "head_state_id": h.state_id,
            "logical_time": h.logical_time,
            "root_state_id": self.root_state_id,
        }

    def to_dict(self) -> dict:
        return {
            "timeline_id": self.timeline_id,
            "root_state_id": self.root_state_id,
            "head_state_id": self.head_state_id,
            "parent_timeline_id": self.parent_timeline_id,
            "fork_state_id": self.fork_state_id,
            "name": self.name,
            "clock": self.clock.to_dict(),
            "last_event_id": self._last_event_id,
        }
