#!/usr/bin/env python

import argparse
import difflib
import hashlib
import shutil
from pathlib import Path
from git import Repo, InvalidGitRepositoryError

Messages = []
FilesWithoutMatch = []


def print_result(message):
    """Print and store the result message."""
    print(message)
    Messages.append(message)


def is_git_related(path):
    return ".git" in path.parts


def sha256sum(file_path):
    """Calculate the SHA-256 checksum of a file."""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def find_first_tag_for_commit(repo, commit):
    """
    Find the first tag that contains the given commit.

    :param repo: GitPython Repo object
    :param commit: GitPython Commit object
    :return: Tag object or None if no tag contains the commit
    """
    tags = sorted(repo.tags, key=lambda t: t.commit.committed_date)

    # Iterate through all tags in the repository
    first_tag = None
    for tag in tags:
        if repo.is_ancestor(commit, tag.commit) or tag.commit == commit:
            first_tag = tag
            print("Tag with the commit:", tag)

    return first_tag


def find_missing_items(archive_path, git_root, git_subfolder):
    """Recursively find files/directories in archive that are not present in Git repository."""
    print("=== Files/Directories in Archive Not in Git Repository ===")

    for archive_item in archive_path.rglob("*"):
        relative_path = archive_item.relative_to(archive_path)
        if is_git_related(relative_path):
            continue

        git_equivalent = git_root / git_subfolder / relative_path

        if archive_item.is_dir():
            if not git_equivalent.is_dir():
                print_result(f"Missing directory: {relative_path}")
        elif archive_item.is_file():
            if not git_equivalent.exists():
                print_result(f"Missing file: {relative_path}")
                FilesWithoutMatch.append(relative_path)


def compare_files(archive_path, git_root, git_subfolder, useDiff):
    """Compare files between an archive and a Git repository."""
    first_match_commit = None
    first_min_diff_commit = None
    repo = Repo(git_root)

    print("=== File Version Comparisons ===")

    for archive_file in archive_path.rglob("*"):
        if archive_file.is_file():
            relative_file = archive_file.relative_to(archive_path)
            if is_git_related(relative_file):
                continue

            git_file = git_root / git_subfolder / relative_file

            if git_file.exists() and git_file.is_file():
                with open(archive_file, "rb") as f:
                    archive_txt = f.read()
                    archive_sha = hashlib.sha256(archive_txt).hexdigest()
                    if useDiff:
                        archive_lines = archive_txt.decode().splitlines(keepends=True)

                if archive_sha != sha256sum(git_file):
                    file_commits = list(
                        repo.iter_commits(
                            paths=str((git_subfolder / relative_file).as_posix())
                        )
                    )

                    matching_commit = None
                    min_diff_commit = None
                    min_diff_length = None
                    for counter, commit in enumerate(file_commits, start=1):
                        try:
                            blob = commit.tree / str(
                                (git_subfolder / relative_file).as_posix()
                            )
                        except:
                            # probably removed in this commit
                            continue
                        git_txt = blob.data_stream.read()
                        commit_sha = hashlib.sha256(git_txt).hexdigest()

                        if archive_sha == commit_sha:
                            matching_commit = commit

                            # if commit_timestamp > first_match_timestamp:
                            if first_match_commit is None or repo.is_ancestor(
                                first_match_commit, commit
                            ):
                                first_match_commit = commit

                            break
                        elif useDiff:
                            git_lines = git_txt.decode().splitlines(keepends=True)
                            diff = difflib.unified_diff(
                                git_lines,
                                archive_lines,
                                fromfile="InRepo",
                                tofile="InArchive",
                            )
                            diff = "".join(diff)
                            diff_lenght = len(diff.splitlines())
                            if min_diff_length is None or min_diff_length > diff_lenght:
                                min_diff_commit = commit
                                min_diff_length = diff_lenght

                    if matching_commit:
                        print(
                            f"Older file: {relative_file} -- matching commit: {matching_commit.hexsha} ({counter} changes from head)"
                        )
                    else:
                        print_result(
                            f"Differing file without match: {relative_file}"
                            + (
                                f"-- closest commit: {min_diff_commit.hexsha} (lines changed {min_diff_length})"
                                if useDiff
                                else ""
                            )
                        )
                        FilesWithoutMatch.append(relative_file)
                        if first_min_diff_commit is None or repo.is_ancestor(
                            first_min_diff_commit, min_diff_commit
                        ):
                            first_min_diff_commit = min_diff_commit

    print()
    print(
        "Newest commit with matching files:",
        first_match_commit.hexsha if first_match_commit else "None",
    )
    print(
        "Newest commit with smallest differences for non-matching files:",
        first_min_diff_commit.hexsha if first_min_diff_commit else "None",
    )
    if first_match_commit is not None and first_min_diff_commit is not None:
        if repo.is_ancestor(first_min_diff_commit, first_match_commit):
            print(f"{first_match_commit.hexsha} is newer")
        else:
            print(f"{first_min_diff_commit.hexsha} is newer")


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
        description="Compare files and directories between an archive and a Git repository."
    )
    parser.add_argument(
        "archive_path", type=Path, help="Path to the archive directory."
    )
    parser.add_argument(
        "git_path", type=Path, help="Path to the Git repository or its subfolder."
    )
    parser.add_argument("--diff", default=False, action=argparse.BooleanOptionalAction)
    parser.add_argument("--copy-files", action="store_true")

    args = parser.parse_args()

    archive_path = args.archive_path.resolve()
    git_path = args.git_path.resolve()

    if not archive_path.is_dir():
        print(f"Error: Archive path '{archive_path}' is not a directory.")
        return

    try:
        git_root = find_git_root(git_path)
        git_subfolder = git_path.relative_to(git_root)
        print(f"\nGit repository root: {git_root}\n")
    except InvalidGitRepositoryError as e:
        print(f"Error: {e}")
        return

    # Perform missing items check
    find_missing_items(archive_path, git_root, git_subfolder)

    print()

    # Perform file comparison
    compare_files(archive_path, git_root, git_subfolder, args.diff)

    print()
    print("\n".join(sorted(Messages)))

    # copy files if requested
    if args.copy_files:
        print()
        print("Copy files\n")
        for f in sorted(FilesWithoutMatch):
            print(archive_path / f, "-->", git_path / f)
            shutil.copy(archive_path / f, git_path / f)


if __name__ == "__main__":
    main()
