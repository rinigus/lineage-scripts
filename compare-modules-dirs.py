#!/usr/bin/env python

import argparse
from pathlib import Path

def loadfiles(path: Path):
    if not path.exists():
        raise RuntimeError(f"Folder does not exist: {path}")
    files = [str(m.name) for m in path.glob("*.ko")]
    return sorted(files)

def main():
    parser = argparse.ArgumentParser(
        description="Compare modules in stock and custom ROMs"
    )
    parser.add_argument(
        "stock_module_path", type=Path, help="Path to the modules directory for stock ROM."
    )
    parser.add_argument(
        "custom_module_path", type=Path, help="Path to the modules directory for custom ROM."
    )

    args = parser.parse_args()
    stock_module_path = args.stock_module_path
    custom_module_path = args.custom_module_path

    stock = loadfiles(stock_module_path)
    custom = loadfiles(custom_module_path)

    # compare sizes
    for s in stock:
        if s in custom:
            ss = (stock_module_path / s).stat().st_size
            cs = (custom_module_path / s).stat().st_size
            print(f"Module sizes: {s} -- {ss} vs {cs}")

    for s in stock:
        if s not in custom:
            print(f"Custom ROM is missing: {s}")

    for c in custom:
        if c not in stock:
            print(f"Custom ROM has extra module: {c}")
    



if __name__ == "__main__":
    main()
