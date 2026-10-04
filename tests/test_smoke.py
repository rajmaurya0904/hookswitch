"""Smoke test: package imports cleanly. Replace/extend as modules land."""

import hookswitch


def test_version_is_set() -> None:
    assert hookswitch.__version__
