#!/usr/bin/env python3
"""Inject the standardized auto-setup cell into starter/model pack notebooks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

AUTO_SETUP_SOURCE = [
    "# 🚀 Auto-setup: installs deps + configures CFBD access\n",
    "%run ./_auto_setup.py\n",
]

AUTO_SETUP_METADATA = {"tags": ["auto-setup", "do-not-remove"]}
PACK_DIRS = ("starter_pack", "model_pack")


def load_notebook(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_notebook(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
        f.write("\n")


def needs_injection(data: dict) -> bool:
    if not data.get("cells"):
        return True
    first_cell = data["cells"][0]
    metadata = first_cell.get("metadata", {})
    tags = metadata.get("tags", [])
    if any(tag == "auto-setup" for tag in tags):
        return False
    source = "".join(first_cell.get("source", [])).strip()
    return "%run ./_auto_setup.py" not in source


def inject_cell(data: dict) -> None:
    new_cell = {
        "cell_type": "code",
        "metadata": AUTO_SETUP_METADATA,
        "source": AUTO_SETUP_SOURCE,
        "outputs": [],
        "execution_count": None,
    }
    data.setdefault("cells", [])
    data["cells"] = [new_cell] + data["cells"]


def iter_notebooks(root: Path) -> Iterable[Path]:
    for path in sorted(root.glob("*.ipynb")):
        yield path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    overall_changed = {}

    for pack in PACK_DIRS:
        pack_dir = repo_root / pack
        changed = []
        for nb_path in iter_notebooks(pack_dir):
            data = load_notebook(nb_path)
            if needs_injection(data):
                inject_cell(data)
                save_notebook(nb_path, data)
                changed.append(nb_path.name)
        if changed:
            overall_changed[pack] = changed

    if overall_changed:
        print("Injected auto-setup cell into:")
        for pack, names in overall_changed.items():
            print(f"[{pack}]")
            for name in names:
                print(f"  - {name}")
    else:
        print("All notebooks already have auto-setup cells.")


if __name__ == "__main__":
    main()
