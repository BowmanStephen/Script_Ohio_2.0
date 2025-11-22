#!/usr/bin/env python3
"""Unit tests for starter_pack.notebook_bootstrap."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import List

import pytest

import starter_pack.notebook_bootstrap as nb


@pytest.fixture()
def req_file(tmp_path: Path) -> Path:
    req = tmp_path / "requirements.txt"
    req.write_text("pandas\n", encoding="utf-8")
    return req


def _mock_project_root(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    monkeypatch.setattr(nb, "_detect_project_root", lambda start=None: path)


def _mock_requirements(monkeypatch: pytest.MonkeyPatch, req_file: Path) -> None:
    monkeypatch.setattr(nb, "_resolve_requirements_file", lambda project_root, override: req_file)


def test_env_flag_disables_auto_install(monkeypatch: pytest.MonkeyPatch, req_file: Path) -> None:
    """CFB_AUTO_INSTALL=0 should skip pip installs even when modules are missing."""
    _mock_project_root(monkeypatch, req_file.parent)
    _mock_requirements(monkeypatch, req_file)

    monkeypatch.setenv("CFB_AUTO_INSTALL", "0")
    monkeypatch.setattr(nb, "_find_missing_modules", lambda: ["pandas"])

    def fail_install(*_args, **_kwargs):
        raise AssertionError("Auto install should not run when env disables it.")

    monkeypatch.setattr(nb, "_auto_install", fail_install)

    result = nb.ensure_notebook_environment(quiet_success=True)
    assert result.auto_install_performed is False
    assert result.missing_modules == ["pandas"]


def test_auto_install_runs_when_missing(monkeypatch: pytest.MonkeyPatch, req_file: Path) -> None:
    """When modules are missing and auto install allowed, pip should be invoked."""
    _mock_project_root(monkeypatch, req_file.parent)
    _mock_requirements(monkeypatch, req_file)

    calls: List[SimpleNamespace] = []
    monkeypatch.setenv("CFB_AUTO_INSTALL", "1")
    monkeypatch.setattr(nb, "_find_missing_modules", lambda: ["numpy", "pandas"])

    def record_install(_req):
        calls.append(SimpleNamespace())

    monkeypatch.setattr(nb, "_auto_install", lambda req: record_install(req))

    result = nb.ensure_notebook_environment(quiet_success=True)
    assert result.auto_install_performed is True
    assert len(calls) == 1


def test_project_root_added_to_sys_path(monkeypatch: pytest.MonkeyPatch, req_file: Path) -> None:
    """Project root should be appended to sys.path exactly once."""
    _mock_project_root(monkeypatch, req_file.parent)
    _mock_requirements(monkeypatch, req_file)
    monkeypatch.setattr(nb, "_find_missing_modules", lambda: [])

    import sys

    if str(req_file.parent) in sys.path:
        sys.path.remove(str(req_file.parent))

    result = nb.ensure_notebook_environment(quiet_success=True)
    assert str(req_file.parent) in sys.path
    assert result.missing_modules == []
