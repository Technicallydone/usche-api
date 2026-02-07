y3l#!/bin/bash
set -euo pipefail

# -----------------------------
# CONFIGURATION
# -----------------------------
BACKUP_ARCHIVE="/var/www/backup_2026-01-30_12-00-01.tar.gz"
TMP_DIR="/tmp/db_restore_$(date +%s)"
DB_NAME="usche_db"
DB_USER="usche"
DB_PASSWORD="usche@2026"
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
# FIND DATABASE FILE
# -----------------------------
SQL_FILE=$(find "$TMP_DIR" -type f -name "*.sql" | head -n 1)
DUMP_FILE=$(find "$TMP_DIR" -type f \( -name "*.bak" -o -name "*.dump" \) | head -n 1)

if [[ -z "$SQL_FILE" && -z "$DUMP_FILE" ]]; then
  echo "❌ No .sql, .bak, or .dump database file found in archive!"
  rm -rf "$TMP_DIR"
  exit 1
fi

# -----------------------------
# CREATE DATABASE IF IT DOESN'T EXIST
# -----------------------------
DB_EXISTS=$(psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -tAc \
  "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")

if [ "$DB_EXISTS" != "1" ]; then
  echo "Database '$DB_NAME' does not exist. Creating it..."
  sudo -i -u postgres psql -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
else
  echo "Database '$DB_NAME' already exists."
fi

# -----------------------------
# RESTORE DATABASE
# -----------------------------
if [ -n "$SQL_FILE" ]; then
  echo "Restoring database from SQL dump: $SQL_FILE"
  psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" < "$SQL_FILE"
elif [ -n "$DUMP_FILE" ]; then
  echo "Restoring database from dump: $DUMP_FILE"
  pg_restore -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" \
    -d "$DB_NAME" --no-owner --clean --verbose "$DUMP_FILE"
fi

# -----------------------------
# CLEANUP
# -----------------------------
echo "Cleaning up temporary files..."
rm -rf "$TMP_DIR"
unset PGPASSWORD

echo "✅ Done! Database '$DB_NAME' has been restored successfully."
