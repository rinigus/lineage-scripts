#!/bin/bash

# This script unpacks dtbo image

set -e

# Check if the script received arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <dtbo_image_file> <folder_to_unpack>"
    exit 1
fi

# Input
DTBO_IMG="$1"
UNPACK_FOLDER_BASE="$2"

if [[ ! -f "$DTBO_IMG" ]]; then
    echo "Error: File '$DTBO_IMG' not found!"
    exit 1
fi

# Extract the base name and target image name
BASE_NAME=$(basename "$DTBO_IMG" .img)
UNPACK_FOLDER="$UNPACK_FOLDER_BASE"/$BASE_NAME

rm -rf "$UNPACK_FOLDER" || echo Remove of folder failed
mkdir -p "$UNPACK_FOLDER"

# Unpack dtbo image
echo "Unpacking dtbo image..."
extract-dtb -o "$UNPACK_FOLDER" "$DTBO_IMG"

cd "$UNPACK_FOLDER"
counter=1
for file in *.dtb; do 
    # Use printf to zero-pad the number
    s=$(printf "%02d.dts" $counter)
    dtc -I dtb -O dts -o "$s" "$file" -@
    ((counter++))
done


