"""TIMELINE tests."""

from chronos import Timeline, TemporalStore


def test_root_creation():
    tl = Timeline.create_root({"v": 0})
    assert tl.head().logical_time == 0
    assert tl.head().state_root == {"v": 0}
    assert tl.root_state_id == tl.head_state_id
    assert tl.head().parent_state is None


def test_transition_and_head():
    tl = Timeline.create_root({"v": 0})
    parent_id = tl.head().state_id
    event, state = tl.transition({"v": 1}, payload={"op": "inc"})
    assert state.parent_state == parent_id
    assert state.logical_time == 1
    assert tl.head_state_id == state.state_id
    old = tl.get_state(parent_id)
    assert old is not None
    assert old.state_root == {"v": 0}


def test_event_state_relationships():
    tl = Timeline.create_root({})
    e1, s1 = tl.transition({"a": 1})
    e2, s2 = tl.transition({"a": 2})
    events = tl.events()
    assert len(events) == 2
    assert events[0].result_state_id == s1.state_id
    assert events[1].input_state_id == s1.state_id
    assert events[1].result_state_id == s2.state_id


def test_shared_store():
    store = TemporalStore()
    tl = Timeline.create_root({"x": 1}, store=store)
    tl.transition({"x": 2})
    assert len(store.states()) >= 2
    assert len(store.events()) >= 1
