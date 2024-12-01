#!/usr/bin/env python

import argparse
import difflib
import hashlib
import shutil
import time
from pathlib import Path
from git import Repo, InvalidGitRepositoryError


def closest_commit(archive_file, git_root, git_file_path):
    """Find closest commit to a provided archive file"""
    repo = Repo(git_root)

    if not archive_file.is_file():
        print(f'File missing: {archive_file}')
        return
    if not git_file_path.exists() or not git_file_path.is_file():
        print(f'File missing: {git_file_path}')
        return

    with open(archive_file, "rb") as f:
        archive_txt = f.read()
        archive_lines = archive_txt.decode().splitlines(keepends=True)

    relative_file = git_file_path.relative_to(git_root)
    print(f'Checking file: {relative_file}\n')

    file_commits = list(
        repo.iter_commits(
            paths=str((relative_file).as_posix())
        )
    )

    min_diff_commit = None
    min_diff_length = None
    min_diff_counter = None
    for counter, commit in enumerate(file_commits):
        try:
            blob = commit.tree / str(
                (relative_file).as_posix()
            )
        except:
            # probably removed in this commit
            continue

        git_txt = blob.data_stream.read()
        git_lines = git_txt.decode().splitlines(keepends=True)

        diff = difflib.unified_diff(
            git_lines,
            archive_lines,
            fromfile="InRepo",
            tofile="InArchive",
        )
        diff = "".join(diff)
        diff_length = len(diff.splitlines())
        if min_diff_length is None or min_diff_length > diff_length:
            min_diff_commit = commit
            min_diff_length = diff_length
            min_diff_counter = counter

        if diff_length == 0:
            break

    if min_diff_length == 0:
        print(
            f"Older file: {relative_file} -- matching commit: {min_diff_commit.hexsha} ({min_diff_counter} changes from head)"
        )
    else:
        print(f"Differing file without match: {relative_file}")
        print(f'Closest commit: {min_diff_commit.hexsha}')
        print(f'Difference in lines: {min_diff_length}')
        print(f'Commits from current checkout: {min_diff_counter}')


def find_git_root(path):
    """Find the root of the Git repository."""
    current_path = path.resolve()
    while current_path != current_path.parent:
        if (current_path / ".git").exists():
            return current_path
        current_path = current_path.parent
    raise InvalidGitRepositoryError(
        f"Could not find a Git repository at or above {path}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Find closest commit to a file from the archive."
    )
    parser.add_argument(
        "archive_path", type=Path, help="Path to the archive file."
    )
    parser.add_argument(
        "git_file_path", type=Path, help="Path to the Git repository file."
    )

    args = parser.parse_args()

    archive_path = args.archive_path.resolve()
    git_file_path = args.git_file_path.resolve()

    try:
        git_root = find_git_root(git_file_path)
        print(f"\nGit repository root: {git_root}\n")
    except InvalidGitRepositoryError as e:
        print(f"Error: {e}")
        return

    closest_commit(archive_path, git_root, git_file_path)

if __name__ == "__main__":
    main()
