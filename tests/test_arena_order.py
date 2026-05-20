#!/usr/bin/env python3
"""
Scan experiment data folders for metadata.json files and report ones where
Arena keys are not in the expected order (Arena1..Arena9). This helps find
experiments affected by the shuffling bug.

Usage:
    python Tests/check_arena_order.py /path/to/experiments_folder [more_folders...]

It will print a list of problematic experiment folders and a small summary.
"""
import sys
from pathlib import Path
import json

EXPECTED_ARENAS = [f"Arena{i}" for i in range(1, 10)]


def check_metadata(path: Path):
    try:
        with open(path / "metadata.json", "r") as f:
            data = json.load(f)
    except Exception as e:
        return (False, f"could not read metadata.json: {e}")

    # Extract arena-like keys in the order they appear in the file
    # Note: json.load on Python preserves insertion order (since 3.7)
    keys = [k for k in data.keys() if k.startswith("Arena")]

    # Create a filtered list of ArenaN (no corridors) in the order they appear
    arena_keys = [k for k in keys if not "_Corridor" in k]

    # If there are no arena keys, it's not applicable
    if not arena_keys:
        return (True, "no arena keys present")

    # Build expected present arenas only (in order)
    present_expected = [k for k in EXPECTED_ARENAS if k in data]

    # If the sequence of present arenas does not match the order they appear in the file,
    # this is a sign of shuffling.
    if arena_keys != present_expected:
        return (False, {"found_order": arena_keys, "expected_order": present_expected})

    return (True, "ok")


def main(args):
    if not args:
        print("Usage: check_arena_order.py /path/to/experiment_folder [more_folders...]")
        return 2

    problematic = []
    checked = 0

    for folder in args:
        p = Path(folder)
        if p.is_file() and p.name == "metadata.json":
            # If user passed a metadata.json directly
            base = p.parent
            ok, info = check_metadata(base)
            checked += 1
            if not ok:
                problematic.append((str(base), info))
        elif p.is_dir():
            # Walk immediate subfolders only (assume experiments are one level deep)
            for sub in p.iterdir():
                if sub.is_dir():
                    checked += 1
                    ok, info = check_metadata(sub)
                    if not ok:
                        problematic.append((str(sub), info))
        else:
            print(f"Path not found: {folder}")

    print(f"Checked {checked} experiment folders")
    if problematic:
        print("Problematic experiments:")
        for p, info in problematic:
            print(f" - {p}: {info}")
        return 1
    else:
        print("No problems found.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
