#!/bin/bash
set -e

SRC_DIR="/root/backup"
DEST_DIR="/var/www/usche/assets"

echo "Copying media files from $SRC_DIR to $DEST_DIR excluding .gz and .bak files..."

# Copy files while excluding .gz and .bak
rsync -av --exclude='*.gz' --exclude='*.bak' "$SRC_DIR"/ "$DEST_DIR"/

echo "Setting permissions to 755 on $DEST_DIR..."
chmod -R 755 "$DEST_DIR"

echo "Done. All files copied and permissions set."
