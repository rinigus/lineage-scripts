# find-archive-matches.py - User Manual

## Overview

This script compares source archives against a Git repository to identify changes and help create minimal patches. It's commonly used for managing vendor-modified sources (e.g., Sony kernel modifications, manufacturer-provided drivers, or any third-party source releases) by comparing archived vendor sources against your Git repository.

## Problem Statement

Device manufacturers and third-party vendors often take upstream sources, apply their modifications, and later release updated sources that may include both their changes and upstream updates. This creates a challenge:

- **Vendor Archive**: Released source dump with vendor modifications
- **Working Repository**: Git-tracked sources with history
- **Goal**: Create minimal commits that isolate vendor changes while tracking version updates

## Prerequisites

- Python 3.x
- GitPython library (`pip install gitpython`)
- A Git repository with your sources
- Vendor source archive (unzipped directory)

## Basic Usage

```bash
./find-archive-matches.py <archive_path> <git_path> [options]
```

### Arguments

- `archive_path`: Path to the vendor's source archive directory
- `git_path`: Path to your Git repository (or subfolder within it)

### Options

- `--files <file1> <file2> ...`: Check only specific files (space-separated)
- `--diff` / `--no-diff`: Enable/disable diff analysis for non-matching files (default: disabled)
- `--copy-files`: Automatically copy differing/missing files to the Git repository
- `--make-merge-script`: Generate a shell script for manual merging
- `--merge-script-export-dir <path>`: Export directory for merge script operations

## Workflow Patterns

### Workflow 1: Initial Analysis

**Goal**: Understand what changed between vendor archive and your repository

```bash
./find-archive-matches.py \
    /path/to/vendor/archive \
    /path/to/git/repo
```

**Output**:
- Lists missing files/directories
- Identifies files that differ from HEAD
- For each differing file, searches commit history to find exact matches
- Reports the newest commit containing matching versions

**Use this when**: You first receive a vendor source dump and want to understand its relationship to your repository.

### Workflow 2: Detailed Diff Analysis

**Goal**: Find closest commits for files that don't have exact matches

```bash
./find-archive-matches.py \
    /path/to/vendor/archive \
    /path/to/git/repo \
    --diff
```

**Output**: Same as Workflow 1, but for files without exact matches, it reports:
- The commit with the smallest diff (fewest line changes)
- Number of lines changed in that closest match

**Use this when**: You need to understand how far vendor modifications have diverged from your repository history. While this is slower than running without `--diff`, it provides detailed information about the nature of changes that can be crucial for understanding vendor modifications.

**Note**: This mode is significantly slower for large archives as it performs diff analysis across all commits for each non-matching file. Running without `--diff` first gives you a fast overview of which files changed.

### Workflow 3: Automatic File Copy

**Goal**: Quickly update repository with vendor changes

```bash
./find-archive-matches.py \
    /path/to/vendor/archive \
    /path/to/git/repo \
    --copy-files
```

**What happens**:
1. Performs analysis (as in Workflow 1)
2. Copies all differing and missing files from archive to Git repository
3. Prints each copy operation

**Use this when**: The vendor archive is a straightforward update and you want to bulk-import changes. You'll still need to manually commit these changes.

### Workflow 4: Generating Merge Scripts for Separate Repository

**Goal**: Create a shell script for pushing changes to a separate export repository

```bash
./find-archive-matches.py \
    /path/to/vendor/archive \
    /path/to/git/repo \
    --make-merge-script \
    --merge-script-export-dir /path/to/export/repo
```

**Output**: Creates `merge-script.sh` that:
- Copies missing files to the export directory
- Calls `kernel-archive-merge-and-export.sh` for each differing file

**How it works with kernel-archive-merge-and-export.sh**:

For each differing file, the merge script:
1. Uses `find-closest-commit.py` to identify the closest historical commit
2. Checks out that commit (vendor's likely base version)
3. Applies vendor changes from the archive
4. Commits the changes with message "Apply Sony changes"
5. Merges back to HEAD, handling conflicts if needed
6. Exports the final merged file to the export repository
7. Returns to HEAD

**Use this when**: You want to push vendor modifications to a separate repository with proper merge commits and conflict resolution. This is particularly useful when you need to maintain separate repositories for different purposes (e.g., development vs. release).

### Workflow 5: Targeted File Analysis

**Goal**: Check specific files only

```bash
./find-archive-matches.py \
    /path/to/vendor/archive \
    /path/to/git/repo \
    --files drivers/video/fbdev.c arch/arm/boot/dts/device.dts \
    --diff
```

**Use this when**: You're investigating specific subsystems or components.

## Practical Example: Sony Kernel Workflow

### Setup

You have:
- `/vendor/sony-kernel-2024/` - Latest Sony source dump
- `/work/kernel-main/` - Your main Git repository with history
- `/work/kernel-export/` - Export repository for publishing changes

### Step 1: Initial Analysis

```bash
cd /work
./find-archive-matches.py \
    /vendor/sony-kernel-2024/kernel \
    /work/kernel-main/kernel
```

Review output to understand:
- Which files Sony added (missing from Git)
- Which files Sony modified (differing files)
- Which commit in history matches the vendor's base

### Step 2: Detailed Investigation

If you need more details about the changes:

```bash
./find-archive-matches.py \
    /vendor/sony-kernel-2024/kernel \
    /work/kernel-main/kernel \
    --diff
```

This shows you the closest commits for files without exact matches and helps understand the scope of modifications.

### Step 3: Create Minimal Patches

For files with matching commits in history:
```bash
# The script tells you: "Older file: drivers/video/fbdev.c -- matching commit: abc123 (15 changes from head)"
cd /work/kernel-main
git diff abc123 HEAD -- drivers/video/fbdev.c > /tmp/vendor-base.patch
```

For files without matches, the script reports the closest commit which helps you understand the starting point.

### Step 4: Merge in Working Copy

```bash
cd /work/kernel-merge
git checkout -b sony-2024-updates

# Copy vendor files
../find-archive-matches.py \
    /vendor/sony-kernel-2024/kernel \
    /work/kernel-merge/kernel \
    --copy-files

# Review changes
git diff

# Create logical commits
git add drivers/sony/
git commit -m "Add changes from Sony Xperia kernel v5.15.2024"

git add drivers/video/
git commit -m "Update framebuffer driver to Sony version 2024"
```

### Step 5: Export to Separate Repository

```bash
./find-archive-matches.py \
    /vendor/sony-kernel-2024/kernel \
    /work/kernel-main/kernel \
    --make-merge-script \
    --merge-script-export-dir /work/kernel-export

# Review the generated merge-script.sh
cat merge-script.sh

# Execute the merge script
bash merge-script.sh
```

The merge script will:
- Handle each file individually by finding its closest commit
- Apply vendor changes
- Merge back to current state
- Export results to your export repository

## Understanding the Output

### File Version Comparisons

```
Older file: drivers/video/fbdev.c -- matching commit: a1b2c3d (10 changes from head)
```
- File in archive matches historical version
- 10 commits have modified this file since

```
Differing file without match: drivers/sony/camera.c
```
- No exact match found in Git history
- Vendor made modifications to this file

```
Differing file without match: drivers/sony/camera.c -- closest commit: x9y8z7w (lines changed 45)
```
- With `--diff` enabled
- Closest historical version is 45 lines different

### Summary Output

```
Newest commit with matching files: a1b2c3d
Newest commit with smallest differences for non-matching files: x9y8z7w
```

These commits help you identify:
- The vendor's likely base version (matching commit)
- Where to start when creating minimal patches (newest common ancestor)

## Tips and Best Practices

1. **Start with fast overview**: Run without `--diff` first to quickly identify changed files
2. **Use `--diff` when needed**: Enable it when you need detailed change analysis or use with `--files` for specific files
3. **Review before copying**: Use analysis mode first, then decide whether to use `--copy-files`
4. **Create topic branches**: Separate vendor changes by subsystem for cleaner history
5. **Keep vendor archives**: Maintain original vendor sources for reference
6. **Document base versions**: Note which commits correspond to vendor releases
7. **Version your commit messages**: Include vendor version information (e.g., "Add changes from version 2024.1.0")
8. **Test merge scripts**: Review generated `merge-script.sh` before executing

## Technical Details

### How Matching Works

1. Calculate SHA-256 of archive file
2. Iterate through Git history for that file path
3. Calculate SHA-256 of each historical version
4. When checksums match, report that commit
5. Track the newest (most recent) matching commit across all files

### Path Resolution

The script automatically:
- Finds the Git repository root
- Determines subfolder relative to root
- Matches archive structure to Git structure
- Handles nested subdirectories

### What Gets Compared

- All regular files in the archive
- `.git` directories are automatically excluded
- Binary files are compared by checksum only (no diff analysis)

### Progress Reporting

For large archives, the script shows progress every 60 seconds:
```
-- Files left to compare 1500; estimated amount of minutes till the end: 12 minutes
```

## Integration with kernel-archive-merge-and-export.sh

When using `--make-merge-script`, the generated script calls `kernel-archive-merge-and-export.sh` for each differing file. This helper script:

1. **Finds closest commit**: Uses `find-closest-commit.py` to identify the vendor's base version
2. **Creates isolated change**: Checks out the base commit and applies vendor changes
3. **Merges forward**: Merges the changes back to HEAD
4. **Handles conflicts**: Drops you into a shell for manual conflict resolution if needed
5. **Exports result**: Copies the merged file to your export repository

This approach creates clean, reviewable commits that clearly separate vendor changes from your own modifications.

---

**Script**: find-archive-matches.py  
**Use case**: Source archive comparison and integration  
**Common applications**: Vendor kernels, third-party drivers, manufacturer source releases