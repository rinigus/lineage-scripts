#!/bin/bash

set -e

# Function to print usage instructions
usage() {
    echo "Usage: $0 <export-kernel> <directory_A_archive> <relative_file_path>"
    echo "Compares contents of archive directory file with git repository, applies as a patch and exports the result"
    exit 1
}

# Check if correct number of arguments
if [ $# -ne 3 ]; then
    usage
fi

EXPORT=$1
ARCHIVE_DIR=$2
FILE=$3

COMM_ID_HEAD=`git rev-parse HEAD`

echo "Going to export result to:" $EXPORT
echo "Archive directory:" $ARCHIVE_DIR
echo "File:" $FILE
echo Current head commit ID: $COMM_ID_HEAD

output=`find-closest-commit.py $ARCHIVE_DIR/$FILE $FILE | grep "Closest commit"`
COMM_TO_GO=${output#Closest commit: }

echo Closest commit is $COMM_TO_GO

# Checkout the closest commit and prepare for the merge
git checkout $COMM_TO_GO
cp $ARCHIVE_DIR/$FILE $FILE
git diff
git add $FILE
git commit -m "Apply Sony changes"

# Attempt the merge and handle conflicts
if ! git merge -m "Merge back" $COMM_ID_HEAD; then
    echo "Merge conflict detected. Dropping into shell for resolution."
    echo "Resolve conflicts and run 'git merge --continue' when done, or 'git merge --abort' to cancel."
    bash
    # Check the status after exiting the shell
    if git diff --name-only --diff-filter=U | grep -q "$FILE"; then
        echo "Conflict not resolved. Exiting."
        exit 1
    fi
fi

# Export the final file
cp $FILE $EXPORT/$FILE
git checkout $COMM_ID_HEAD

echo
echo "Done: Merged changes for $FILE"
echo
