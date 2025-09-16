#!/bin/bash
set -e

SRC_DIR="/root/backup"
DEST_DIR="/var/www/usche/assets/media"

# Create destination directory if it doesn't exist
if [ ! -d "$DEST_DIR" ]; then
  echo "Creating destination directory: $DEST_DIR"
  mkdir -p "$DEST_DIR"
fi

echo "Copying media files from $SRC_DIR to $DEST_DIR excluding .gz and .bak files..."
rsync -av --exclude='*.gz' --exclude='*.bak' "$SRC_DIR"/ "$DEST_DIR"/

echo "Setting permissions to 755 on $DEST_DIR..."
chmod -R 755 "$DEST_DIR"

echo "Done. All files copied and permissions set."
