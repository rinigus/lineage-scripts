#!/bin/bash

set -e

# Function to print usage instructions
usage() {
    echo "Usage: $0 <directory_A_archive> <directory_B_git>"
    echo "Compares contents of archive directory with git repositories"
    exit 1
}

# Check if correct number of arguments
if [ $# -ne 2 ]; then
    usage
fi

# Validate input directories
ARCHIVE_DIR=$(realpath "$1")
GIT_DIR=$(realpath "$2")

if [ ! -d "$ARCHIVE_DIR" ]; then
    echo "Error: Archive directory $ARCHIVE_DIR does not exist"
    exit 1
fi

if [ ! -d "$GIT_DIR" ]; then
    echo "Error: Git directory $GIT_DIR does not exist"
    exit 1
fi

RESULT_FILE=$(mktemp)

# helper function for messages stored in RESULT
print_result() {
    echo $*
    echo $* >> "$RESULT_FILE"
}

# Function to recursively find files/dirs in A not present in B
find_missing_items() {
    local archive_path="$1"
    local git_path="$2"    
    
    echo "=== Files/Directories in Archive Not in Git Repository ==="
    
    # Find directories in archive that are not in git
    find "$archive_path" -type d | while read -r archive_dir; do
        # Skip the root directory itself
        if [ "$archive_path" = "$archive_dir"  ]; then
            continue
        fi
        relative_dir=${archive_dir#$archive_path/}
        git_equivalent_dir="$git_path/$relative_dir"
               
        if [ ! -d "$git_equivalent_dir" ] && [ -n "$relative_dir" ]; then
            print_result "Missing directory: $relative_dir"
        fi
    done

    # Find files in archive that are not in git
    find "$archive_path" -type f | while read -r archive_file; do
        relative_file=${archive_file#$archive_path/}
        git_equivalent_file="$git_path/$relative_file"
        
        if [ ! -e "$git_equivalent_file" ]; then
            print_result "Missing file: $relative_file"
        fi
    done
}

# Function to recursively compare files
compare_files() {
    local archive_path="$1"
    local git_path="$2"
    local first_match_timestamp=0
    local first_match_commit=""
    
    echo "=== File Version Comparisons ==="
    
    # Find files in archive that exist in git
    find "$archive_path" -type f | while read -r archive_file; do
        local relative_file=${archive_file#$archive_path/}
        local git_file="$git_path/$relative_file"
        
        # Check if file exists in git repo
        if [ -e "$git_file" ]; then
            # First, check if files are different
            if ! cmp -s "$archive_file" "$git_file"; then
                pushd "$(dirname "$git_file")" > /dev/null
                local filename=$(basename "$git_file")
                
                # Calculate sha256 for archive file
                local archive_sha=$(sha256sum "$archive_file" | cut -d' ' -f1)

                # Find the first matching commit
                local first_match=""
                local counter=0
                
                # Iterate through commits that touched this file
                while IFS= read -r commit && [ -z "$first_match" ]; do
                    # Get the file version at this commit
                    local commit_sha=$(git show "$commit:./$filename" | sha256sum | cut -d' ' -f1)
                    counter=$((counter+1))
                
                    # Compare shasums
                    if [ "$archive_sha" = "$commit_sha" ]; then
                        first_match="$commit"
    
                        # Get commit timestamp
                        local commit_timestamp=$(git log -1 --format=%ct "$commit")
                        if [ "$commit_timestamp" -gt "$first_match_timestamp" ]; then
                            first_match_timestamp="$commit_timestamp"
                            first_match_commit="$commit"
                        fi
                    fi
                done < <(git rev-list HEAD -- "$filename")
                
                # Process results
                if [ -n "$first_match" ]; then
                    echo "Older file: $relative_file -- matching commit: $first_match ($counter changes from head)"
                else
                    print_result "Differing file without match: $relative_file"
                fi
                popd > /dev/null
            fi           
        fi
    done
}

# Run the comparison functions

find_missing_items "$ARCHIVE_DIR" "$GIT_DIR"

echo

compare_files "$ARCHIVE_DIR" "$GIT_DIR"

echo
echo "=== Main differences ==="
cat "$RESULT_FILE" | sort

rm "$RESULT_FILE"
