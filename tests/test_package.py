"""Smoke tests for the installed package.

These assert the packaging works — that credsniff is importable, exposes a version,
and ships its type-information marker. Cheap, but they catch a broken install
before any real test has a chance to run.
"""

import importlib.metadata
import importlib.util
from pathlib import Path

import credsniff


def test_version_is_exposed() -> None:
    assert credsniff.__version__


def test_version_matches_installed_metadata() -> None:
    """The __version__ constant and the packaging metadata must not drift apart."""
    assert credsniff.__version__ == importlib.metadata.version("credsniff")


def test_ships_py_typed_marker() -> None:
    """PEP 561: without this file, downstream type checkers ignore our hints."""
    spec = importlib.util.find_spec("credsniff")
    assert spec is not None
    assert spec.origin is not None
    assert (Path(spec.origin).parent / "py.typed").is_file()
