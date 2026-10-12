#!/usr/bin/env python3
"""Choose the next production patch version and package the existing action."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
from zipfile import ZIP_DEFLATED, ZipFile

TAG_PATTERN = re.compile(r"^prod-v(\d+)\.(\d+)\.(\d+)$")
PACKAGE_FILES = ("README.md", "scripts/update_readme.py")


def next_version(tags: list[str]) -> str:
    versions = [tuple(map(int, match.groups())) for tag in tags if (match := TAG_PATTERN.fullmatch(tag))]
    major, minor, patch = max(versions, default=(1, 0, -1))
    return f"{major}.{minor}.{patch + 1}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("release-bundle.zip"))
    args = parser.parse_args()
    tags = subprocess.check_output(["git", "tag", "--list", "prod-v*"], text=True).splitlines()
    version = next_version(tags)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.output, "w", ZIP_DEFLATED) as archive:
        for name in PACKAGE_FILES:
            archive.write(name)
        archive.writestr("VERSION", version + "\n")
    Path("release-version.txt").write_text(version + "\n", encoding="utf-8")
    print(f"Packaged {args.output} for version {version}")


if __name__ == "__main__":
    main()
