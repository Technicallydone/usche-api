#!/bin/bash
set -e

# -----------------------------
# CONFIGURATION
# -----------------------------
BACKUP_ARCHIVE="/Users/mcharo/projects/usche/backup_2026-01-30_12-00-01.tar.gz"
TMP_DIR="/tmp/db_restore_$(date +%s)"
DB_NAME="usche_db_v2"
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
# EXTRACT BACKUP
# -----------------------------
echo "Extracting backup archive..."
tar -xzvf "$BACKUP_ARCHIVE" -C "$TMP_DIR"

# -----------------------------
# FIND BACKUP FILE
# -----------------------------
SQL_FILE=$(find "$TMP_DIR" -type f -name "*.sql" | head -n 1)
BAK_FILE=$(find "$TMP_DIR" -type f -name "*.bak" | head -n 1)

if [[ -z "$SQL_FILE" && -z "$BAK_FILE" ]]; then
  echo "❌ No .sql or .bak database file found in archive!"
  exit 1
fi

# -----------------------------
# CHECK IF DATABASE EXISTS
# -----------------------------
DB_EXISTS=$(psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -tAc \
  "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")

if [ "$DB_EXISTS" != "1" ]; then
  echo "Database '$DB_NAME' does not exist. Creating it..."
  psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d postgres \
    -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
else
  echo "Database '$DB_NAME' already exists."
fi

# -----------------------------
# RESTORE DATABASE
# -----------------------------
if [ -n "$SQL_FILE" ]; then
  echo "Restoring from SQL dump: $SQL_FILE"
  psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" < "$SQL_FILE"
else
  echo "Restoring from BAK dump: $BAK_FILE"
  pg_restore -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" \
    -d "$DB_NAME" --no-owner --clean --verbose "$BAK_FILE"
fi

# -----------------------------
# CLEANUP
# -----------------------------
echo "Cleaning up temporary files..."
rm -rf "$TMP_DIR"

echo "✅ Done! Database '$DB_NAME' has been restored successfully."
