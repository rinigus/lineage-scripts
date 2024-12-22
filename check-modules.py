#!/usr/bin/env python

import argparse
from pathlib import Path
import subprocess
import sys


def get_dependencies_with_modinfo(ko_file):
    """
    Get the dependencies of a .ko file using modinfo.
    """
    try:
        result = subprocess.run(
            ["modinfo", "-F", "depends", str(ko_file)],
            text=True,
            capture_output=True,
            check=True
        )
        dependencies = result.stdout.strip()
        return set(dependencies.split(",")) if dependencies else set()
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to run modinfo on {ko_file}. {e.stderr}")
        return set()


def validate_modules(ko_folder):
    """
    Validate all .ko files in the directory by checking their dependencies.
    """
    ko_folder = Path(ko_folder)
    if not ko_folder.is_dir():
        print(f"Error: {ko_folder} is not a valid directory.")
        sys.exit(1)

    # Get a set of all available .ko filenames without the extension
    available_modules = {file.stem for file in ko_folder.glob("*.ko")}

    invalid_modules = []

    for ko_file in sorted(ko_folder.glob("*.ko")):
        dependencies = get_dependencies_with_modinfo(ko_file)
        print(f"{ko_file.stem}: {' '.join(sorted(list(dependencies)))}")

        # Check if any dependency is missing
        missing_dependencies = dependencies - available_modules
        if missing_dependencies:
            invalid_modules.append((ko_file.name, missing_dependencies))

    if invalid_modules:
        print("Some modules are invalid:")
        for module, missing in invalid_modules:
            print(f"  - {module} is missing dependencies: {' '.join([m + ".ko" for m in missing])}")
    else:
        print("All modules are valid.")


def main():
    parser = argparse.ArgumentParser(description="Check whether modules have all requirements included")
    parser.add_argument(
        "modules_folder",
        type=str,
        help="Path to the directory containing the modules .ko files."
    )

    args = parser.parse_args()
    validate_modules(args.modules_folder)


if __name__ == "__main__":
    main()
