#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to print an error message and exit
error_exit() {
    echo "Error: $1" >&2
    exit 1
}

# Check if exactly two arguments are provided
if [[ $# -ne 2 ]]; then
    error_exit "Usage: $0 <source_folder> <destination_folder>"
fi

# Assign arguments to variables
SOURCE_FOLDER="$1"
DEST_FOLDER="$2"

# Validate that the source folder exists and is a directory
if [[ ! -d "$SOURCE_FOLDER" ]]; then
    error_exit "Source folder '$SOURCE_FOLDER' does not exist or is not a directory."
fi

# Validate that the destination folder exists and is a directory
if [[ ! -d "$DEST_FOLDER" ]]; then
    error_exit "Destination folder '$DEST_FOLDER' does not exist or is not a directory."
fi

# Get the list of .ko files in the destination folder
DEST_MODULES=($(find "$DEST_FOLDER" -maxdepth 1 -type f -name "*.ko"))
if [[ ${#DEST_MODULES[@]} -eq 0 ]]; then
    error_exit "No .ko files found in the destination folder."
fi

MISSING_MODULES=""
# Iterate over destination modules and copy them from the source folder
for MODULE in "${DEST_MODULES[@]}"; do
    MODULE_NAME=$(basename "$MODULE")  # Extract the file name
    SOURCE_MODULE="$SOURCE_FOLDER/$MODULE_NAME"  # Path in the source folder

    # Check if the module exists in the source folder
    if [[ -f "$SOURCE_MODULE" ]]; then
        cp -v "$SOURCE_MODULE" "$DEST_FOLDER/"
    else
        echo "Module '$MODULE_NAME' not found in the source folder."
        #error_exit "Module '$MODULE_NAME' not found in the source folder."
        MISSING_MODULES="$MISSING_MODULES $MODULE_NAME"
    fi
done

if [[ -z "${MISSING_MODULES}" ]]; then
    echo "All matching modules copied successfully."
else
    echo "Missing modules $MISSING_MODULES skipped."
fi
