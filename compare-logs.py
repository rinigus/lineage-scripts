#!/usr/bin/env python

import argparse
from dataclasses import dataclass
from typing import List

@dataclass
class DiffEntry:
    line_number_old: int
    line_number_new: int
    content: str


def preprocess_dmesg(lines):
    """Preprocess dmesg logs to remove the timing column."""
    return [line.split("]", 1)[-1].strip() if "]" in line else line for line in lines]


def read_file(filepath):
    """Read a file and return its lines."""
    with open(filepath, "r") as f:
        return f.readlines()


def compare_logs(file1_lines, file2_lines, context=100):
    """Compare two log files, allowing lines to be matched within a +/- context."""
    result = []
    used_indices = set()

    for i, line1 in enumerate(file1_lines):
        found = False
        start = max(0, i - context)
        end = min(len(file2_lines), i + context + 1)

        for j in range(start, end):
            if j in used_indices:
                continue
            if line1.strip() == file2_lines[j].strip():
                used_indices.add(j)
                found = True
                break

        if not found:
            result.append(DiffEntry(line_number_old=i + 1, line_number_new=-1, content=line1.strip()))

    for i, line2 in enumerate(file2_lines):
        if i not in used_indices:
            result.append(DiffEntry(line_number_old=-1, line_number_new=i + 1, content=line2.strip()))

    return sorted(result, key=lambda x: (x.line_number_old if x.line_number_old != -1 else x.line_number_new))


def main():
    parser = argparse.ArgumentParser(
        description="Compare log files with flexible line matching."
    )
    parser.add_argument("file1", help="First log file")
    parser.add_argument("file2", help="Second log file")
    parser.add_argument(
        "-c",
        "--context",
        type=int,
        default=100,
        help="Number of lines for matching context (default: 100)",
    )
    parser.add_argument(
        "--preprocess", choices=["dmesg"], help="Preprocessing step for the logs"
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    args = parser.parse_args()

    # Read files
    file1_lines = read_file(args.file1)
    file2_lines = read_file(args.file2)

    # Preprocess files if needed
    if args.preprocess == "dmesg":
        file1_lines = preprocess_dmesg(file1_lines)
        file2_lines = preprocess_dmesg(file2_lines)

    # Compare logs
    diff = compare_logs(file1_lines, file2_lines, context=args.context)

    # Output results
    for entry in diff:
        line_number_old = f"{entry.line_number_old}" if entry.line_number_old != -1 else "-"
        line_number_new = f"{entry.line_number_new}" if entry.line_number_new != -1 else "-"
        if args.no_color:
            print(f"{line_number_old:>6} {line_number_new:>6} {entry.content}")
        else:
            if entry.line_number_old == -1:
                print(f"\033[92m{line_number_old:>6} {line_number_new:>6} {entry.content}\033[0m")  # Green for added lines
            elif entry.line_number_new == -1:
                print(f"\033[91m{line_number_old:>6} {line_number_new:>6} {entry.content}\033[0m")  # Red for removed lines
            else:
                print(f"{line_number_old:>6} {line_number_new:>6} {entry.content}")


if __name__ == "__main__":
    main()