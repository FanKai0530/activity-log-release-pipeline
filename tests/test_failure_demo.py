"""Run only by the explicit workflow_dispatch failure demonstration."""


def test_release_gate_blocks_failing_tests():
    assert False, "Intentional failed-test demonstration: all release jobs must be skipped"
