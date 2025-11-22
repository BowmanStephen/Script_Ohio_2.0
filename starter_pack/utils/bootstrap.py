#!/usr/bin/env python3
"""
Reusable bootstrap helpers for starter/model pack notebooks.

The notebooks frequently run in fresh kernels where even core dependencies
(`pandas`, `numpy`, etc.) are missing. Relying on each user to remember the
right `%pip install` command caused repeated `ModuleNotFoundError`s.

This module provides a single `ensure_notebook_environment()` helper that can
be invoked from the first cell in any notebook. It will:

1. Detect the project root so local imports like `agents.*` work.
2. Check for core dependencies that every notebook uses.
3. Optionally run `pip install -r requirements.txt` exactly once per kernel if
   anything is missing (users can skip auto-install via env var).
4. Emit clear guidance for CFBD API configuration (key, rate limiting, etc.).

Usage inside a notebook:

```python
from starter_pack.utils.bootstrap import ensure_notebook_environment
ensure_notebook_environment()
```
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT_MARKERS = {"AGENTS.md", "README.md", ".project-root"}

# Map module name -> package name (for informative messaging)
ESSENTIAL_DEPENDENCIES: Dict[str, str] = {
    "pandas": "pandas",
    "numpy": "numpy",
    "sklearn": "scikit-learn",
    "xgboost": "xgboost",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "cfbd": "cfbd",
}


@dataclass
class BootstrapResult:
    """Summary returned to notebooks for optional logging/inspection."""

    project_root: Path
    requirements_file: Path
    missing_modules: List[str]
    auto_install_performed: bool

    def as_dict(self) -> Dict[str, str]:
        return {
            "project_root": str(self.project_root),
            "requirements_file": str(self.requirements_file),
            "missing_modules": json.dumps(self.missing_modules),
            "auto_install_performed": json.dumps(self.auto_install_performed),
        }


def _detect_project_root(start: Optional[Path] = None) -> Path:
    """Locate the project root using known marker files."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current] + list(current.parents):
        if any((candidate / marker).exists() for marker in PROJECT_ROOT_MARKERS):
            return candidate
    return current


def _resolve_requirements_file(project_root: Path, override: Optional[str]) -> Path:
    """Choose which requirements file to install from."""
    if override:
        override_path = Path(override).expanduser()
        if override_path.exists():
            return override_path
    for candidate in ("requirements.txt", "requirements-dev.txt", "requirements-prod.txt"):
        candidate_path = project_root / candidate
        if candidate_path.exists():
            return candidate_path
    return project_root / "requirements.txt"


def _find_missing_modules() -> List[str]:
    """Return a list of essential modules that cannot be imported."""
    missing = []
    for module_name in ESSENTIAL_DEPENDENCIES:
        if importlib.util.find_spec(module_name) is None:
            missing.append(module_name)
    return missing


def _auto_install(requirements_file: Path) -> None:
    """Install dependencies using pip if missing modules were detected."""
    print(f"📦 Installing dependencies from {requirements_file} ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])


def _print_cfbd_guidance() -> None:
    """Give users actionable guidance for CFBD API configuration."""
    api_key = os.environ.get("CFBD_API_KEY") or os.environ.get("CFBD_API_TOKEN")
    if api_key:
        return

    message = """
⚠️  CFBD API key missing.

Set an environment variable before launching Jupyter to enable live data pulls:

    export CFBD_API_KEY="<your key>"

Rate limit guidance: The official API allows 6 requests/second. Insert
`time.sleep(0.17)` between looped requests and handle 401/429 responses.

See documentation/user/cfbd_api_guide.md for detailed setup instructions.
"""
    print(message.strip())


def ensure_notebook_environment(
    *,
    auto_install: bool = True,
    requirements_override: Optional[str] = None,
    quiet_success: bool = False,
) -> BootstrapResult:
    """
    Guarantee notebooks have dependencies, project paths, and CFBD guidance.

    Args:
        auto_install: Whether to call pip automatically when modules are missing.
                      Can also be toggled via the CFB_AUTO_INSTALL (default: 1).
        requirements_override: Optional path to a requirements file.
        quiet_success: Suppress success message when no action is needed.

    Returns:
        BootstrapResult summarizing what occurred.
    """
    project_root = _detect_project_root()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    requirements_file = _resolve_requirements_file(project_root, requirements_override)
    missing_modules = _find_missing_modules()

    env_flag = os.environ.get("CFB_AUTO_INSTALL")
    if env_flag is not None:
        auto_install = env_flag not in {"0", "false", "False"}

    auto_install_performed = False
    if missing_modules:
        print(f"Detected missing modules: {', '.join(missing_modules)}")
        if auto_install:
            _auto_install(requirements_file)
            auto_install_performed = True
        else:
            pkg_list = ", ".join(ESSENTIAL_DEPENDENCIES[m] for m in missing_modules)
            print(
                "Auto-install disabled. Run:\n"
                f"    %pip install -r {requirements_file}\n"
                f"to install: {pkg_list}"
            )
    elif not quiet_success:
        print("✅ Notebook environment already satisfied.")

    _print_cfbd_guidance()

    result = BootstrapResult(
        project_root=project_root,
        requirements_file=requirements_file,
        missing_modules=missing_modules,
        auto_install_performed=auto_install_performed,
    )

    if not quiet_success:
        print(
            f"Project root: {project_root}\n"
            f"Requirements file: {requirements_file}\n"
            f"Auto install: {'yes' if auto_install_performed else 'no'}"
        )

    return result


__all__ = [
    "BootstrapResult",
    "ESSENTIAL_DEPENDENCIES",
    "ensure_notebook_environment",
]


if __name__ == "__main__":
    ensure_notebook_environment()

