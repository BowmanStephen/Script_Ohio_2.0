"""Helper entrypoint so notebooks can simply `%run _auto_setup.py`."""
from __future__ import annotations

import os
from pathlib import Path

from starter_pack.utils.bootstrap import ensure_notebook_environment

if __name__ == "__main__":
    requirements_override = os.environ.get("CFB_NOTEBOOK_REQUIREMENTS")
    result = ensure_notebook_environment(
        auto_install=os.environ.get("CFB_AUTO_INSTALL", "1") not in {"0", "false", "False"},
        requirements_override=requirements_override,
        quiet_success=True,
    )
    print(
        "🔧 Notebook auto-setup complete:\n"
        f"  • Project root: {result.project_root}\n"
        f"  • Requirements: {result.requirements_file}\n"
        f"  • Missing modules: {', '.join(result.missing_modules) or 'none'}\n"
        f"  • Auto install performed: {result.auto_install_performed}"
    )
