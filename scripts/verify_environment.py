"""Verify that VS Code selected an environment with the complete DA/DS stack.

Run in the VS Code terminal:

    python scripts/verify_environment.py

The script uses only the standard library, so it can still explain which
packages are missing when the scientific environment is incomplete.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from importlib.metadata import PackageNotFoundError, version


REQUIRED_PACKAGES = (
    "numpy",
    "pandas",
    "matplotlib",
    "seaborn",
    "scipy",
    "statsmodels",
    "scikit-learn",
    "requests",
    "beautifulsoup4",
    "streamlit",
    "ipykernel",
)

# Some install names differ from the module imported in Python source.
IMPORT_NAMES = {
    "scikit-learn": "sklearn",
    "beautifulsoup4": "bs4",
}


def main() -> int:
    """Print a machine-readable report and return non-zero if anything is missing."""

    packages = []
    for package in REQUIRED_PACKAGES:
        module = IMPORT_NAMES.get(package, package)
        available = importlib.util.find_spec(module) is not None
        try:
            installed_version = version(package) if available else None
        except PackageNotFoundError:
            installed_version = "available-via-shared-runtime" if available else None
        packages.append(
            {
                "package": package,
                "import_name": module,
                "available": available,
                "version": installed_version,
            }
        )

    missing = [item["package"] for item in packages if not item["available"]]
    report = {
        "status": "ready" if not missing else "incomplete",
        "python": sys.version,
        "executable": sys.executable,
        "packages": packages,
        "missing": missing,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
