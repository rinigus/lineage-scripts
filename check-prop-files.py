#!/usr/bin/env python

import argparse

from props import *

def find_missing_files(folder, device_folders):
    """Find and print files in the folder not listed in the text files."""
    folder_files = get_files_from_folder(folder)
    device_folders_entries = get_files_from_txt(device_folders)

    missing_files = sorted(folder_files - device_folders_entries)  # Case-sensitive comparison
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
    parser.add_argument("folder", type=str, help="Folder containing files to check (recursively).")
    parser.add_argument("device_folders", type=str, nargs='+', help="Text files to compare against.")

    args = parser.parse_args()
    find_missing_files(args.folder, args.device_folders)

if __name__ == "__main__":
    main()
