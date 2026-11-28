#!/usr/bin/env python3
"""Set the application and Python package versions for a tagged build."""

import argparse
import re
from pathlib import Path


VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
VERSION_FILES = (
    (Path("setup.py"), r'(?m)^    version="[^"]+",$', '    version="{version}",'),
    (Path("pymbook/version.py"), r"(?m)^APP_VERSION = '[^']+'$", "APP_VERSION = '{version}'"),
)


def update_version(project_root: Path, version: str) -> None:
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"Unsupported release version: {version}")

    for relative_path, pattern, replacement in VERSION_FILES:
        path = project_root / relative_path
        content = path.read_text(encoding="utf-8")
        updated, count = re.subn(
            pattern,
            replacement.format(version=version),
            content,
            count=1,
        )
        if count != 1:
            raise ValueError(f"Expected exactly one version declaration in {path}")
        path.write_text(updated, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("version")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    update_version(arguments.project_root, arguments.version)


if __name__ == "__main__":
    main()
