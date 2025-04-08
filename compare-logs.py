#!/usr/bin/env python

import argparse
import re
from dataclasses import dataclass
from termcolor import cprint


@dataclass
class DiffEntry:
    line_number_old: int
    line_number_new: int
    content: str


class Line:
    def __init__(self, line):
        self.line = line

    def sub(self, f, t):
        self.line = re.sub(f, t, self.line)

    def replace(self, o, n):
        self.line = self.line.replace(o, n)

    def skip(self, *starts):
        for s in starts:
            if self.line.startswith(s):
                return True
        return False


def preprocess_dmesg(lines):
    """Preprocess dmesg logs to remove the timing column."""
    processed = []
    for line in lines:
        line = Line(line.split("]", 2)[-1].strip() if "]" in line else line)

        # drop unimportant lines
        if line.skip("healthd: battery l="):
            continue

        # unify some messages
        line.replace("apexd-bootstrap:", "apexd:")
        line.replace("/vendor_dlkm/", "/vendor/")
        line.replace("/system/system_ext", "/system")
        line.replace(" No alternative instances declared in VINTF.", "")

        # replace some values with a dummy
        line.sub(r"audit\(([\d.]+:\d+)\)", "audit(REPLACED)")
        line.sub(r" duration=\d+", " duration=REPLACED")
        line.sub(r"Adding to iommu group \d+", "Adding to iommu group REPLACED")
        line.sub(r"pid \d+", "pid REPLACED")
        line.sub(r"pid=\d+", "pid=REPLACED")
        line.sub(r"pid: \d+", "pid: REPLACED")
        line.sub(r"pid:\d+", "pid:REPLACED")
        line.sub(r"PID: \d+", "PID: REPLACED")
        line.sub(r"\[\d+ \]", "[REPLACED ]")
        line.sub(r"CPU: \d+", "CPU: R")
        line.sub(r"Port: \d+", "Port: R")
        line.sub(r"took \d+.\d+ seconds", "took REPLACED seconds")
        line.sub(r"took \d+ms", "took REPLACEDms")
        line.sub(r"took \d+ ms", "took REPLACED ms")
        processed.append(line.line)
    return processed


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
            result.append(
                DiffEntry(
                    line_number_old=i + 1, line_number_new=-1, content=line1.strip()
                )
            )

    for i, line2 in enumerate(file2_lines):
        if i not in used_indices:
            result.append(
                DiffEntry(
                    line_number_old=-1, line_number_new=i + 1, content=line2.strip()
                )
            )

    return sorted(
        result,
        key=lambda x: (
            x.line_number_old if x.line_number_old != -1 else x.line_number_new
        ),
    )


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
        line_number_old = (
            f"{entry.line_number_old}" if entry.line_number_old != -1 else "-"
        )
        line_number_new = (
            f"{entry.line_number_new}" if entry.line_number_new != -1 else "-"
        )
        if args.no_color:
            print(f"{line_number_old:>6} {line_number_new:>6} {entry.content}")
        else:
            if entry.line_number_old == -1:
                cprint(
                    f"{line_number_old:>6} {line_number_new:>6} {entry.content}",
                    "green",
                )  # Green for added lines
            elif entry.line_number_new == -1:
                cprint(
                    f"{line_number_old:>6} {line_number_new:>6} {entry.content}",
                    "light_yellow",
                )  # for removed lines
            else:
                print(f"{line_number_old:>6} {line_number_new:>6} {entry.content}")


if __name__ == "__main__":
    main()
