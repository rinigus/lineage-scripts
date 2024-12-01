#!/usr/bin/env python

import argparse

from props import *

def check_files(device_folders, files):
    """Retrieve all file names listed in the specified text files."""
    for txt_file in device_folders:
        all_lines = []
        print(f'Opening: {txt_file}')
        with open(os.path.join(txt_file, "proprietary-files.txt"), 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or \
                   line.find(";") > 0 or line in files or \
                   (line.startswith("-") and line[1:] in files) :
                    all_lines.append(line)
                else:
                    print("Missing in the system:", line)
        #print("\n".join(all_lines))
        print()

        # with open(os.path.join(txt_file, "proprietary-files.txt"), 'w') as f:
        #     f.write("\n".join(all_lines))
        #     f.write("\n")

def main():
    parser = argparse.ArgumentParser(description="Drop properties not present in the system")
    parser.add_argument("device_folders", type=str, nargs='+', help="Text files to compare against.")

    args = parser.parse_args()
    files = set()
    for f in get_files_from_folder(".", verbose=False):
        files.add(f[2:])

    check_files(args.device_folders, files)

if __name__ == "__main__":
    main()
