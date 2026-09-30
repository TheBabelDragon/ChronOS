"""REPLAY tests."""

import pytest

from chronos import Timeline, replay, assert_deterministic_replay


def test_deterministic_replay():
    tl = Timeline.create_root({"v": 0})
    tl.transition({"v": 1}, payload={"delta": 1})
    tl.transition({"v": 2}, payload={"delta": 1})
    ids = assert_deterministic_replay(tl)
    assert len(ids) == 3
    assert ids[0] == tl.root_state_id
    assert ids[-1] == tl.head_state_id


def test_replay_isolation():
    tl = Timeline.create_root({"v": 0})
    tl.transition({"v": 1})
    head_before = tl.head_state_id
    states = replay(tl)
    assert tl.head_state_id == head_before
    assert [s.state_id for s in states][-1] == head_before


def test_divergence_detection():
    tl = Timeline.create_root({})
    tl.transition({"a": 1})
    assert_deterministic_replay(tl)


def test_missing_result_fails():
    tl = Timeline.create_root({})
    with pytest.raises(ValueError):
        replay(tl, from_state="nonexistent")
