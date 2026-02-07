#!/bin/bash
set -e

# -----------------------------
# CONFIG
# -----------------------------
ARCHIVE="/var/www/backup_2026-01-30_12-00-01.tar.gz"
DEST_DIR="/var/www/assets/media"
TMP_DIR="/tmp/usche_restore_$(date +%s)"

# -----------------------------
# PRE-CHECKS
# -----------------------------
if [ ! -f "$ARCHIVE" ]; then
  echo "❌ Backup archive not found: $ARCHIVE"
  exit 1
fi

# -----------------------------
# CREATE DIRECTORIES
# -----------------------------
echo "Creating temp directory: $TMP_DIR"
mkdir -p "$TMP_DIR"

echo "Creating destination directory: $DEST_DIR"
mkdir -p "$DEST_DIR"

# -----------------------------
# EXTRACT ARCHIVE
# -----------------------------
echo "Extracting archive..."
tar -xzvf "$ARCHIVE" -C "$TMP_DIR"

# -----------------------------
# COPY FILES (EXCLUDING .bak & .sql)
# -----------------------------
echo "Copying extracted files to assets (excluding .bak and .sql)..."

rsync -av \
  --exclude='*.bak' \
  --exclude='*.sql' \
  "$TMP_DIR"/ \
  "$DEST_DIR"/

# -----------------------------
# SET PERMISSIONS
# -----------------------------
echo "Setting permissions to 755..."
chmod -R 755 "$DEST_DIR"

# -----------------------------
# CLEAN UP
# -----------------------------
echo "Cleaning up temp files..."
rm -rf "$TMP_DIR"

echo "✅ Done! Archive extracted and media restored to $DEST_DIR"
