"""
Shared pytest bootstrap for repository-wide test execution.

This makes the consolidated tests under tests/ importable from the project root,
which is the execution mode expected by SonarQube coverage collection in CI.
"""
from pathlib import Path
from uuid import uuid4
import os
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent
SIMULATOR_DIR = PROJECT_ROOT / "simulator"
_SESSION_TK_ROOT = None

# Keep relative test fixtures and assets stable no matter where pytest is started.
os.chdir(PROJECT_ROOT)

for candidate in (str(PROJECT_ROOT), str(SIMULATOR_DIR)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)


def _configure_tk_library_paths():
    """Point Tkinter at the bundled Python Tcl/Tk scripts before Tk loads."""
    tcl_root = Path(sys.base_prefix) / "tcl"
    os.environ.setdefault("TCL_LIBRARY", str(tcl_root / "tcl8.6"))
    os.environ.setdefault("TK_LIBRARY", str(tcl_root / "tk8.6"))


def pytest_configure(config):
    """Load one real Tk root early so later GUI tests reuse a stable interpreter."""
    global _SESSION_TK_ROOT
    _configure_tk_library_paths()
    try:
        import tkinter as tk

        if getattr(tk, "_default_root", None) is None:
            _SESSION_TK_ROOT = tk.Tk()
            _SESSION_TK_ROOT.withdraw()
        else:
            _SESSION_TK_ROOT = tk._default_root
    except Exception:
        _SESSION_TK_ROOT = None


def pytest_sessionfinish(session, exitstatus):
    global _SESSION_TK_ROOT
    if _SESSION_TK_ROOT is not None:
        try:
            _SESSION_TK_ROOT.destroy()
        except Exception:
            pass
        _SESSION_TK_ROOT = None


@pytest.fixture
def tmp_path():
    """Project-local replacement for pytest's tmp_path fixture.

    The default pytest temp root is not reliable in this environment, so we
    create a temporary directory under the repository's temp/ folder instead.
    """
    temp_root = PROJECT_ROOT / "temp" / "pytest-fixtures"
    temp_root.mkdir(parents=True, exist_ok=True)
    path = temp_root / f"tmp-{uuid4().hex}"
    path.mkdir()
    yield path
