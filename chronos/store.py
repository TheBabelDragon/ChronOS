"""
Append-only temporal store (in-memory).

Events and committed states are immutable.
Duplicate IDs are rejected unless byte-identical.
"""

from __future__ import annotations

import json
from typing import Dict, Iterable, List, Optional

from .event import TemporalEvent
from .state import TemporalState


class TemporalStore:
    """
    In-memory append-only store for events and states.

    Designed so a persistent backend can later implement the same interface.
    """

    def __init__(self) -> None:
        self._events: Dict[str, TemporalEvent] = {}
        self._event_order: List[str] = []
        self._states: Dict[str, TemporalState] = {}
        self._state_order: List[str] = []

    def append_event(self, event: TemporalEvent) -> None:
        """Append an event. Rejects non-identical duplicates."""
        existing = self._events.get(event.event_id)
        if existing is not None:
            if existing.to_dict() != event.to_dict():
                raise ValueError(
                    f"Event ID collision with non-identical content: {event.event_id}"
                )
            return
        self._events[event.event_id] = event
        self._event_order.append(event.event_id)

    def get_event(self, event_id: str) -> Optional[TemporalEvent]:
        return self._events.get(event_id)

    def events(self) -> List[TemporalEvent]:
        """Return events in insertion order."""
        return [self._events[eid] for eid in self._event_order]

    def events_for_state(self, state_id: str) -> List[TemporalEvent]:
        """Events that reference the given state as input or result."""
        return [
            e
            for e in self.events()
            if e.input_state_id == state_id or e.result_state_id == state_id
        ]

    def events_for_timeline(self, timeline_id: str) -> List[TemporalEvent]:
        """Events whose result state belongs to the given timeline."""
        result: List[TemporalEvent] = []
        for e in self.events():
            if e.result_state_id:
                st = self._states.get(e.result_state_id)
                if st and st.timeline_id == timeline_id:
                    result.append(e)
        return result

    def put_state(self, state: TemporalState) -> None:
        """Store a committed state. Rejects non-identical duplicates."""
        existing = self._states.get(state.state_id)
        if existing is not None:
            if existing.to_dict() != state.to_dict():
                raise ValueError(
                    f"State ID collision with non-identical content: {state.state_id}"
                )
            return
        self._states[state.state_id] = state
        self._state_order.append(state.state_id)

    def get_state(self, state_id: str) -> Optional[TemporalState]:
        return self._states.get(state_id)

    def states(self) -> List[TemporalState]:
        return [self._states[sid] for sid in self._state_order]

    def to_dict(self) -> dict:
        return {
            "events": [e.to_dict() for e in self.events()],
            "states": [s.to_dict() for s in self.states()],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TemporalStore":
        store = cls()
        for sdata in data.get("states") or []:
            store.put_state(TemporalState.from_dict(sdata))
        for edata in data.get("events") or []:
            store.append_event(TemporalEvent.from_dict(edata))
        return store

    def __len__(self) -> int:
        return len(self._events) + len(self._states)
