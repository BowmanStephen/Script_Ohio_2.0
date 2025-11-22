#!/usr/bin/env python3
"""Papermill smoke tests for the primary starter-pack notebook."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

try:  # pragma: no cover - imported dynamically in tests
    import papermill as pm
except ImportError:  # pragma: no cover
    pm = None


NOTEBOOK_ROOT = Path(__file__).resolve().parents[1]
STARTER_NOTEBOOK = NOTEBOOK_ROOT / "starter_pack" / "01_intro_to_data.ipynb"


@pytest.mark.slow
def test_intro_notebook_executes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Execute the intro notebook end-to-end to catch regressions."""
    if pm is None:
        pytest.skip("papermill is not installed")

    assert STARTER_NOTEBOOK.exists(), "Starter notebook missing; verify repository checkout."

    # Ensure matplotlib renders headless during automation
    monkeypatch.setenv("MPLBACKEND", "Agg")
    monkeypatch.setenv("CFB_AUTO_INSTALL", "0")  # Don't mutate the environment during CI
    existing_path = os.environ.get("PYTHONPATH")
    new_path = str(NOTEBOOK_ROOT)
    if existing_path:
        new_path = f"{new_path}{os.pathsep}{existing_path}"
    monkeypatch.setenv("PYTHONPATH", new_path)

    output_path = tmp_path / "01_intro_to_data.output.ipynb"
    pm.execute_notebook(
        str(STARTER_NOTEBOOK),
        str(output_path),
        cwd=str(STARTER_NOTEBOOK.parent),
        parameters={"fetch_latest": False},
        kernel_name="python3",
        log_output=False,
    )

    assert output_path.exists()
