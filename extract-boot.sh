#!/bin/bash

# # This script unpacks boot image

# Check if the script received arguments
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <AOSP-sources-path> <boot_image_file> <folder_to_unpack>"
    exit 1
fi

# Input
PATH="$1"/out/host/linux-x86/bin:$PATH:`dirname $0`
BOOT_IMG="$2"
UNPACK_FOLDER_BASE="$3"

if [[ ! -f "$BOOT_IMG" ]]; then
    echo "Error: File '$BOOT_IMG' not found!"
    exit 1
fi

# Extract the base name and target image name
BASE_NAME=$(basename "$BOOT_IMG" .img)
UNPACK_FOLDER="$UNPACK_FOLDER_BASE"/$BASE_NAME

mkdir -p "$UNPACK_FOLDER"

# write info file
avbtool info_image --image "$BOOT_IMG" > "$UNPACK_FOLDER/avbinfo.txt"

# Unpack the boot image
echo "Unpacking boot image..."
unpack_bootimg --boot_img "$BOOT_IMG" --out "$UNPACK_FOLDER"
if [ $? -ne 0 ]; then
    echo "Error: Failed to unpack boot image."
    exit 1
fi

cd "$UNPACK_FOLDER"

# get kernel information
if [[ -f kernel ]]; then
    strings kernel | grep "Linux version"
    extract-ikconfig kernel > kernel-config.txt
fi

# unpack ramdisk
RDISK=rdisk

mkdir -p $RDISK
cd $RDISK
lz4cat ../*ramdisk* | cpio -i
