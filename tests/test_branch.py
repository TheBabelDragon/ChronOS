"""BRANCH tests."""

from chronos import Timeline, fork


def test_fork_shared_ancestry():
    tl = Timeline.create_root({"v": 0})
    _, s1 = tl.transition({"v": 1})
    _, s2 = tl.transition({"v": 2})

    branch = fork(tl, s1.state_id, name="alt")
    assert branch.timeline_id != tl.timeline_id
    assert branch.parent_timeline_id == tl.timeline_id
    assert branch.fork_state_id == s1.state_id
    # Branch head is a re-addressed view; ancestry points at shared s1
    assert branch.head().parent_state == s1.state_id
    assert branch.head().state_root == s1.state_root


def test_independent_heads():
    tl = Timeline.create_root({"v": 0})
    _, s1 = tl.transition({"v": 1})
    branch = fork(tl, s1.state_id)

    tl.transition({"v": 10})
    branch.transition({"v": 20})

    assert tl.head().state_root == {"v": 10}
    assert branch.head().state_root == {"v": 20}
    # Parent timeline not mutated by branch advancement
    assert tl.get_state(s1.state_id).state_root == {"v": 1}


def test_branch_isolation_objects():
    tl = Timeline.create_root({})
    _, s = tl.transition({"a": 1})
    branch = fork(tl, s.state_id)
    # Historical objects are shared by identity in the store, not cloned
    assert branch.store is tl.store
    assert branch.store.get_state(s.state_id) is tl.store.get_state(s.state_id)
