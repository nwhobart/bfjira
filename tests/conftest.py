import os
import sys
import types
from unittest import mock

import pytest

# Ensure the package root is on the import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Stub external dependencies that may not be installed in the test environment

# Minimal git module stub
if "git" not in sys.modules:
    git_stub = types.ModuleType("git")

    class Repo:  # pragma: no cover - simple placeholder
        pass

    git_stub.Repo = Repo
    sys.modules["git"] = git_stub

# Minimal jira module stub
if "jira" not in sys.modules:
    jira_stub = types.ModuleType("jira")

    class JIRA:  # pragma: no cover - simple placeholder
        pass

    jira_stub.JIRA = JIRA
    sys.modules["jira"] = jira_stub

# Minimal colorlog module stub
if "colorlog" not in sys.modules:
    colorlog_stub = types.ModuleType("colorlog")

    class ColoredFormatter:  # pragma: no cover - simple placeholder
        def __init__(self, *args, **kwargs):
            pass

    colorlog_stub.ColoredFormatter = ColoredFormatter
    sys.modules["colorlog"] = colorlog_stub


class SimpleMocker:
    """Minimal replacement for pytest-mock's MockerFixture."""

    def __init__(self):
        self._patches = []

        class _Patcher:
            def __init__(self, outer):
                self.outer = outer

            def __call__(self, target, *args, **kwargs):
                patcher = mock.patch(target, *args, **kwargs)
                obj = patcher.start()
                outer._patches.append(patcher)
                return obj

            def dict(self, target, values=(), **kwargs):
                patcher = mock.patch.dict(target, values, **kwargs)
                patcher.start()
                outer._patches.append(patcher)
                return patcher

        outer = self
        self.patch = _Patcher(outer)

    def stopall(self):
        for p in reversed(self._patches):
            p.stop()
        self._patches.clear()


@pytest.fixture
def mocker():
    sm = SimpleMocker()
    try:
        yield sm
    finally:
        sm.stopall()
