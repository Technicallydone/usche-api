#!/bin/bash
set -e

# -----------------------------
# CONFIGURATION
# -----------------------------
BACKUP_ARCHIVE="/Users/mcharo/projects/usche/server_backup/new_backup_20251004.tar.gz"
TMP_DIR="/tmp/db_restore_$(date +%s)"
DB_NAME="usche_db_v3"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_HOST="localhost"
DB_PORT="5432"

# -----------------------------
# EXPORT PASSWORD FOR PSQL
# -----------------------------
export PGPASSWORD="$DB_PASSWORD"

# -----------------------------
# CREATE TEMP DIRECTORY
# -----------------------------
mkdir -p "$TMP_DIR"
echo "Created temporary directory $TMP_DIR"

# -----------------------------
# UNZIP BACKUP
# -----------------------------
echo "Extracting backup archive..."
tar -xzvf "$BACKUP_ARCHIVE" -C "$TMP_DIR"

# -----------------------------
# FIND THE .BAK FILE
# -----------------------------
BAK_FILE=$(find "$TMP_DIR" -type f -name "*.bak" | head -n 1)
if [ -z "$BAK_FILE" ]; then
  echo "No .bak file found in the archive!"
  exit 1
fi
echo "Found backup file: $BAK_FILE"

# -----------------------------
# CHECK IF DATABASE EXISTS
# -----------------------------
DB_EXISTS=$(psql -U $DB_USER -h $DB_HOST -p $DB_PORT -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")
if [ "$DB_EXISTS" != "1" ]; then
  echo "Database '$DB_NAME' does not exist. Creating it..."
  psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
else
  echo "Database '$DB_NAME' already exists."
fi

# -----------------------------
# RESTORE BACKUP
# -----------------------------
echo "Restoring backup into '$DB_NAME'..."
pg_restore -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME --no-owner --clean --verbose "$BAK_FILE"

# -----------------------------
# CLEANUP
# -----------------------------
echo "Cleaning up temporary files..."
rm -rf "$TMP_DIR"

echo "Done! Database '$DB_NAME' has been restored successfully."
