"""CLOCK tests."""

import pytest

from chronos import LogicalClock


def test_monotonic_tick():
    c = LogicalClock()
    assert c.now() == 0
    assert c.tick() == 1
    assert c.tick(3) == 4
    assert c.now() == 4


def test_tick_invalid():
    c = LogicalClock()
    with pytest.raises(ValueError):
        c.tick(0)
    with pytest.raises(ValueError):
        c.tick(-1)


def test_observe():
    c = LogicalClock()
    c.tick()
    assert c.observe(5) == 5
    assert c.now() == 5
    assert c.observe(3) == 5  # does not go backwards


def test_observe_invalid():
    c = LogicalClock()
    with pytest.raises(ValueError):
        c.observe(-1)


def test_serialization_roundtrip():
    c = LogicalClock()
    c.tick(7)
    d = c.to_dict()
    c2 = LogicalClock.from_dict(d)
    assert c2.now() == 7
    assert c2.to_dict() == d


def test_negative_init():
    with pytest.raises(ValueError):
        LogicalClock(_time=-1)
