#!/usr/bin/env python

import argparse

from props import *

def main():
    parser = argparse.ArgumentParser(description="Find duplicate files in text files.")
    parser.add_argument("device_folders", type=str, nargs='+', help="Text files to compare against.")

    args = parser.parse_args()
    get_files_from_txt(args.device_folders, duplicate=True)

if __name__ == "__main__":
    main()
