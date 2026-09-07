"""Convert a VS Code percent-cell Python file to a Jupyter notebook.

Why keep this helper?
---------------------
The commented ``.py`` file is easy for beginners to read and diff, while the
``.ipynb`` file provides the Colab-like Run Cell experience. Generating the
notebook prevents the two teaching versions from silently diverging.

Usage from the project root::

    .\\.venv-vscode\\Scripts\\python.exe scripts\\sync_percent_notebook.py
"""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT / "notebooks" / "01_eda_s16.py"
TARGET = PROJECT_ROOT / "notebooks" / "01_eda_s16.ipynb"


def _markdown_source(lines: list[str]) -> list[str]:
    """Remove Python comment prefixes while keeping Markdown line breaks."""

    result = []
    for line in lines:
        if line.startswith("# "):
            result.append(line[2:])
        elif line.rstrip("\n") == "#":
            result.append("\n")
        else:
            result.append(line)
    return result


def parse_percent_cells(text: str) -> list[dict[str, object]]:
    """Split source at ``# %%`` markers and create notebook cell dictionaries."""

    cells: list[dict[str, object]] = []
    cell_type: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        """Append the buffered percent-cell in Jupyter's JSON structure."""

        nonlocal buffer
        if cell_type is None:
            # Module docstring before the first marker is documentation for the
            # `.py` representation and is intentionally omitted from notebook.
            buffer = []
            return
        source = _markdown_source(buffer) if cell_type == "markdown" else buffer
        cell: dict[str, object] = {
            "cell_type": cell_type,
            "metadata": {},
            "source": source,
        }
        if cell_type == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
        cells.append(cell)
        buffer = []

    for line in text.splitlines(keepends=True):
        if line.startswith("# %%"):
            flush()
            cell_type = "markdown" if "[markdown]" in line else "code"
        else:
            buffer.append(line)
    flush()
    return cells


def main() -> int:
    """Generate a deterministic UTF-8 notebook and print its cell count."""

    cells = parse_percent_cells(SOURCE.read_text(encoding="utf-8"))
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python (.venv-vscode)",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    TARGET.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "source": str(SOURCE), "target": str(TARGET), "cells": len(cells)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
