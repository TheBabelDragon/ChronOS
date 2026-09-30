"""TEMPORAL ABI tests."""

from chronos import TemporalOp, map_kernel_op, KERNEL_TO_ABI


def test_all_ops_stable():
    expected = {
        "BEGIN",
        "OBSERVE",
        "TRANSITION",
        "COMMIT",
        "SNAPSHOT",
        "RESTORE",
        "FORK",
        "REPLAY",
        "TRACE",
        "INTEGRITY",
    }
    assert {op.value for op in TemporalOp} == expected


def test_kernel_mapping():
    assert map_kernel_op("SELF.GET") == TemporalOp.OBSERVE
    assert map_kernel_op("SELF.SET") == TemporalOp.TRANSITION
    assert map_kernel_op("SELF.RUN") == TemporalOp.TRANSITION
    assert map_kernel_op("SELF.QUERY") == TemporalOp.OBSERVE
    assert map_kernel_op("TRACE") == TemporalOp.TRACE
    assert map_kernel_op("INTEGRITY") == TemporalOp.INTEGRITY
    assert map_kernel_op("SET") == TemporalOp.TRANSITION
    assert map_kernel_op("GET") == TemporalOp.OBSERVE


def test_mapping_table_complete():
    for name, op in KERNEL_TO_ABI.items():
        assert isinstance(op, TemporalOp)
