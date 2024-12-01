#!/usr/bin/env python

import argparse

from props import *

def find_from_old_files(root, currentprop, oldprop):
    rom = get_files_from_folder(root)
    old = get_files_from_txt(oldprop)
    current = get_files_from_txt(currentprop)

    diff = sorted(old - current)
    missing_files = []
    for file in diff:
        if file in rom:
            missing_files.append(file)

    if missing_files:
        print("Missing files:\n")
        for f in missing_files:
            print(f, get_file_info(f))
        print("\nList of missing files again:\n")
        print("\n".join(missing_files))
    else:
        print("All files are present in the text files.")

def main():
    parser = argparse.ArgumentParser(description="Check missing files in text files.")
    parser.add_argument("--root", type=str, help="Folder containing ROM files.")
    parser.add_argument("--new", type=str, nargs='+', help="Text files to compare against.")
    parser.add_argument("--old", type=str, nargs='+', help="Text files to compare against.")

    args = parser.parse_args()
    find_from_old_files(args.root, args.new, args.old)

if __name__ == "__main__":
    main()
