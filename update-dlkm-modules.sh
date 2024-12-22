#!/bin/bash

# Exit on any error
set -e

# Function to print error messages and exit
error_exit() {
    echo "Error: $1" >&2
    exit 1
}

# Detect the directory of this script
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# Locate the copy-modules script
COPY_MODULES="$SCRIPT_DIR/copy-modules.sh"

# Check if copy-modules exists and is executable
if [[ ! -x "$COPY_MODULES" ]]; then
    error_exit "The 'copy-modules' script was not found in '$SCRIPT_DIR' or is not executable."
fi

# Check for sufficient arguments
if [[ $# -ne 2 ]]; then
    error_exit "Usage: $0 <path-to-raw-img> <path-to-source-modules>"
fi

RAW_IMG="$1"
SOURCE_MODULES="$2"

# Validate the raw image
if [[ ! -f "$RAW_IMG" ]]; then
    error_exit "Raw image '$RAW_IMG' not found."
fi

# Validate the source modules folder
if [[ ! -d "$SOURCE_MODULES" ]]; then
    error_exit "Source modules folder '$SOURCE_MODULES' not found."
fi

# Mount point for the original and new images
MOUNT_POINT_ORIG="/mnt/dlkm_orig"
MOUNT_POINT_NEW="/mnt/dlkm_new"

# Create mount points if they don't exist
sudo mkdir -p "$MOUNT_POINT_ORIG" "$MOUNT_POINT_NEW"

# Set up a loop device for the original image
LOOP_DEVICE_ORIG=$(sudo losetup -fP --show "$RAW_IMG")
echo "Loop device for original image: $LOOP_DEVICE_ORIG"

# Mount the original image read-only
echo "Mounting original image read-only to $MOUNT_POINT_ORIG..."
sudo mount -o ro "$LOOP_DEVICE_ORIG" "$MOUNT_POINT_ORIG"

# Calculate the size of the new image
IMAGE_SIZE=$(du -sb "$MOUNT_POINT_ORIG" | awk '{print $1}')
RESERVED_SPACE=$((IMAGE_SIZE / 4))
NEW_IMAGE_SIZE=$((IMAGE_SIZE + RESERVED_SPACE))
echo "Creating new image of size: $NEW_IMAGE_SIZE bytes (including $RESERVED_SPACE reserved space)"

# Create a new empty image file
NEW_IMG="${RAW_IMG%.img}-updated.img"
dd if=/dev/zero of="$NEW_IMG" bs=1 count=0 seek="$NEW_IMAGE_SIZE"

# Format the new image as EXT4
echo "Formatting new image as EXT4..."
mkfs.ext4 -F -m 0 \
    -b 4096 -I 256 \
    -O ext_attr,dir_index,filetype,extent,sparse_super,large_file,huge_file,uninit_bg,dir_nlink,extra_isize,^has_journal,^resize_inode,^metadata_csum,^64bit,^flex_bg \
    -L vendor_dlkm "$NEW_IMG"

# Set up a loop device for the new image
LOOP_DEVICE_NEW=$(sudo losetup -fP --show "$NEW_IMG")
echo "Loop device for new image: $LOOP_DEVICE_NEW"

# Mount the new image read-write
echo "Mounting new image read-write to $MOUNT_POINT_NEW..."
sudo mount "$LOOP_DEVICE_NEW" "$MOUNT_POINT_NEW"

# Copy data from the original image to the new image
echo "Copying data from original image to new image..."
sudo rsync -a "$MOUNT_POINT_ORIG/" "$MOUNT_POINT_NEW/"

sudo du -sh "$MOUNT_POINT_ORIG/" "$MOUNT_POINT_NEW/"

# Unmount the original image
echo "Unmounting original image..."
sudo umount "$MOUNT_POINT_ORIG"
sudo losetup -d "$LOOP_DEVICE_ORIG"

# Define the path to the destination modules inside the new image
DEST_MODULES="$MOUNT_POINT_NEW/lib/modules"

# Ensure the destination modules folder exists
if [[ ! -d "$DEST_MODULES" ]]; then
    error_exit "Modules folder '$DEST_MODULES' not found inside the new image."
fi

# # Use the copy-modules script to update the modules
# echo "Updating kernel modules using '$COPY_MODULES'..."
# sudo "$COPY_MODULES" "$SOURCE_MODULES" "$DEST_MODULES"

df -h $MOUNT_POINT_NEW
df $MOUNT_POINT_NEW

# Unmount the new image
echo "Unmounting new image..."
sudo umount "$MOUNT_POINT_NEW"
sudo losetup -d "$LOOP_DEVICE_NEW"

# Shrink the new image to the minimum required size
echo "Shrinking new image to the minimum required size..."
e2fsck -f "$NEW_IMG"
resize2fs -M "$NEW_IMG"

# # Reserve 5% space
# echo "Reserving 5% free space in the filesystem..."
# resize2fs "$NEW_IMG" "$NEW_IMAGE_SIZE"

# Cleanup
echo "Cleaning up mount points..."
sudo rmdir "$MOUNT_POINT_ORIG" "$MOUNT_POINT_NEW"

tune2fs -O ^has_journal,^resize_inode,^metadata_csum,^64bit,^flex_bg "$NEW_IMG" || true
e2fsck -f "$NEW_IMG"

echo "New image created successfully: $NEW_IMG"
