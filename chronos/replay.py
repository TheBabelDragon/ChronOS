"""
Deterministic replay.

same root + same events  ⇒  same state identities

Replay walks event ancestry and reconstructs states without mutating
the original timeline. Missing transition information fails explicitly.
"""

from __future__ import annotations

from typing import Any, Callable, List, Optional, Sequence

from .event import TemporalEvent
from .state import TemporalState
from .timeline import Timeline


def _event_chain(
    timeline: Timeline,
    from_state: Optional[str],
    to_state: Optional[str],
) -> List[TemporalEvent]:
    """
    Collect events on this timeline between from_state (exclusive)
    and to_state (inclusive), in logical-time order.
    """
    events = sorted(
        timeline.events(),
        key=lambda e: (e.logical_time, e.event_id),
    )
    if not events:
        return []

    start_id = from_state or timeline.root_state_id
    end_id = to_state or timeline.head_state_id

    needed_results = set()
    current = timeline.store.get_state(end_id)
    seen = set()
    while current is not None and current.state_id not in seen:
        seen.add(current.state_id)
        if current.state_id == start_id:
            break
        needed_results.add(current.state_id)
        if current.parent_state:
            current = timeline.store.get_state(current.parent_state)
        else:
            break

    return [e for e in events if e.result_state_id in needed_results]


def replay(
    timeline: Timeline,
    *,
    from_state: Optional[str] = None,
    to_state: Optional[str] = None,
    event_handler: Optional[Callable[[TemporalEvent, Optional[TemporalState]], Any]] = None,
) -> List[TemporalState]:
    """
    Reconstruct the state sequence for a timeline segment.

    If event_handler is provided it is invoked for each event as
    ``handler(event, input_state)`` and must return the new state_root
    (or a TemporalState). When omitted, the committed result states
    already in the store are returned (verification path).

    Replay never mutates the original timeline's head or clock.
    """
    chain = _event_chain(timeline, from_state, to_state)
    start_id = from_state or timeline.root_state_id
    start = timeline.store.get_state(start_id)
    if start is None:
        raise ValueError(f"Replay start state missing: {start_id}")

    results: List[TemporalState] = [start]

    if event_handler is None:
        for event in chain:
            if not event.result_state_id:
                raise ValueError(
                    f"Event {event.event_id} lacks result_state_id; "
                    "cannot reconstruct transition"
                )
            st = timeline.store.get_state(event.result_state_id)
            if st is None:
                raise ValueError(
                    f"Event {event.event_id} references missing result "
                    f"state {event.result_state_id}"
                )
            results.append(st)
        return results

    current: Optional[TemporalState] = start
    for event in chain:
        if event.input_state_id and current and event.input_state_id != current.state_id:
            resolved = timeline.store.get_state(event.input_state_id)
            if resolved is None:
                raise ValueError(
                    f"Event {event.event_id} input state "
                    f"{event.input_state_id} not found"
                )
            current = resolved
        produced = event_handler(event, current)
        if isinstance(produced, TemporalState):
            results.append(produced)
            current = produced
        else:
            from .provenance import Provenance

            synthetic = TemporalState(
                timeline_id=timeline.timeline_id,
                logical_time=event.logical_time,
                state_root=produced,
                parent_state=current.state_id if current else None,
                causal_parents=event.causal_parents,
                provenance=event.provenance or Provenance(),
            )
            results.append(synthetic)
            current = synthetic
    return results


def assert_deterministic_replay(
    timeline: Timeline,
    *,
    from_state: Optional[str] = None,
    to_state: Optional[str] = None,
) -> List[str]:
    """
    Run the segment reconstruction twice and compare state identity
    sequences. Raises AssertionError on divergence. Returns the
    identity sequence on success.
    """
    first = [s.state_id for s in replay(timeline, from_state=from_state, to_state=to_state)]
    second = [s.state_id for s in replay(timeline, from_state=from_state, to_state=to_state)]
    if first != second:
        raise AssertionError(
            f"Non-deterministic replay detected:\n  first={first}\n  second={second}"
        )
    return first
