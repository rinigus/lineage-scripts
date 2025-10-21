#!/usr/bin/env python3
"""
Compare files in two directories and report identical files.
"""

import argparse
import hashlib
from pathlib import Path
from typing import Set


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_relative_files(directory: Path) -> Set[Path]:
    """Get all files in directory as relative paths."""
    if not directory.exists():
        raise ValueError(f"Directory does not exist: {directory}")
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    files = set()
    for f in directory.rglob("*"):
        # Skip files inside .git directories
        if ".git" in f.parts:
            continue
        if f.is_file():
            files.add(f.relative_to(directory))
    
    return files

def find_identical_files(dir1: Path, dir2: Path) -> list[str]:
    """
    Compare files in two directories and return list of identical files.
    """
    # Get all files from both directories
    files1 = get_relative_files(dir1)
    files2 = get_relative_files(dir2)
    
    # Find common files (same relative path in both directories)
    common_files = files1.intersection(files2)
    different = files1 ^ files2
    
    if not common_files:
        return []
    
    # Compare content of common files
    identical_files = []
    
    for rel_path in common_files:
        file1 = dir1 / rel_path
        file2 = dir2 / rel_path
        
        try:
            # Compare file hashes
            hash1 = calculate_file_hash(file1)
            hash2 = calculate_file_hash(file2)
            
            if hash1 == hash2:
                identical_files.append(str(rel_path))
            else:
                different.add(rel_path)
        except Exception as e:
            print(f"Warning: Could not compare {rel_path}: {e}")
    
    return sorted(identical_files), sorted(different)


def main():
    parser = argparse.ArgumentParser(
        description="Compare files in two directories and report identical files."
    )
    parser.add_argument(
        "dir1",
        type=Path,
        help="First directory to compare"
    )
    parser.add_argument(
        "dir2",
        type=Path,
        help="Second directory to compare"
    )
    
    args = parser.parse_args()
    
    try:
        identical_files, different_files = find_identical_files(args.dir1, args.dir2)

        print(f"Found {len(different_files)} different file(s)\n")
        if identical_files:
            print(f"Found {len(identical_files)} identical file(s):\n")
            for file_path in identical_files:
                print(file_path)
        else:
            print("No identical files found.")
            
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())