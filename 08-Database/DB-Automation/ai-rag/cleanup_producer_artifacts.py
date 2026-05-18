#!/usr/bin/env python3
"""Cleanup old scoped producer artifact directories."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = BASE_DIR / "producer-artifacts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cleanup old producer artifact scopes")
    parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT_DIR, help="Producer artifact root directory")
    parser.add_argument("--keep", type=int, default=5, help="Number of newest scope directories to keep")
    parser.add_argument("--dry-run", action="store_true", help="Show directories that would be removed")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact_dir = args.artifact_dir
    if not artifact_dir.exists():
        print(f"Artifact directory does not exist: {artifact_dir}")
        return

    scope_dirs = [path for path in artifact_dir.iterdir() if path.is_dir()]
    scope_dirs.sort(key=lambda path: path.name, reverse=True)
    removable = scope_dirs[args.keep :]

    print(f"Found {len(scope_dirs)} scoped artifact directories")
    print(f"Keeping newest {min(args.keep, len(scope_dirs))} scopes")
    for path in removable:
        if args.dry_run:
            print(f"Would remove {path}")
        else:
            shutil.rmtree(path)
            print(f"Removed {path}")


if __name__ == "__main__":
    main()
