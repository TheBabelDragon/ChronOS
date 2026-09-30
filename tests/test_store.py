"""STORE tests."""

import pytest

from chronos import TemporalStore, TemporalEvent, TemporalState, Timeline


def test_duplicate_identical_idempotent():
    store = TemporalStore()
    tl = Timeline.create_root({"a": 1}, store=store)
    s = tl.head()
    store.put_state(s)
    e, _ = tl.transition({"a": 2})
    store.append_event(e)


def test_conflicting_duplicate_fails():
    store = TemporalStore()
    s1 = TemporalState(timeline_id="tl", logical_time=0, state_root={"a": 1})
    store.put_state(s1)
    s2 = TemporalState(timeline_id="tl", logical_time=0, state_root={"a": 2})
    assert s1.state_id != s2.state_id
    store.put_state(s2)


def test_serialization_roundtrip():
    store = TemporalStore()
    tl = Timeline.create_root({"x": 0}, store=store)
    tl.transition({"x": 1})
    d = store.to_dict()
    store2 = TemporalStore.from_dict(d)
    assert len(store2.events()) == len(store.events())
    assert len(store2.states()) == len(store.states())
    for e in store.events():
        assert store2.get_event(e.event_id) is not None
