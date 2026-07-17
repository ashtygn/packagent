"""Skeleton smoke test so `make ci` exercises pytest from day one."""

import pkgtk


def test_package_imports() -> None:
    assert pkgtk.__version__
