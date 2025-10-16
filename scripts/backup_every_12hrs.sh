#!/bin/bash

# ------------------------------------------------------------------
# Django Project Backup Script
# Can be run via cron
# Keeps only the 3 most recent backups
# ------------------------------------------------------------------

set -e

# ------------------------------
# Determine directories
# ------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../" && pwd)"
ENV_FILE="$PROJECT_DIR/.env"
LOG_DIR="$PROJECT_DIR/logs"
BACKUP_DIR="$PROJECT_DIR/backups"
LOG_FILE="$LOG_DIR/db_backup.log"
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_NAME="backup_$DATE"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# ------------------------------
# Ensure directories exist
# ------------------------------
mkdir -p "$LOG_DIR"
mkdir -p "$BACKUP_DIR"

# ------------------------------
# Load environment variables
# ------------------------------
if [[ ! -f "$ENV_FILE" ]]; then
    echo "[$(date)] .env file not found at $ENV_FILE" >> "$LOG_FILE"
    exit 1
fi

export $(grep -v '^#' "$ENV_FILE" | xargs)

# ------------------------------
# Start Backup
# ------------------------------
{
echo "[$(date)] Starting Django backup..."

# --- Database backup ---
PGPASSWORD="$DB_PASSWORD" pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" "$DB_NAME" > "$BACKUP_PATH.sql"

# --- Media backup excluding certificates ---
tar --exclude='certificates' -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_DIR" "$(basename "$BACKUP_PATH.sql")" -C "$MEDIA_ROOT" .

# Remove raw SQL dump
rm -f "$BACKUP_PATH.sql"

echo "[$(date)] Backup created: $BACKUP_PATH.tar.gz"

# ------------------------------
# Retention Policy: Keep 3 latest backups
# ------------------------------
TOTAL_BACKUPS=$(ls -1t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | wc -l)

if (( TOTAL_BACKUPS > 3 )); then
    echo "[$(date)] Removing old backups, keeping 3 most recent..." >> "$LOG_FILE"
    ls -1t "$BACKUP_DIR"/backup_*.tar.gz | tail -n +4 | while read OLD_BACKUP; do
        echo "Deleting old backup: $OLD_BACKUP" >> "$LOG_FILE"
        rm -f "$OLD_BACKUP"
    done
fi

echo "[$(date)] Backup completed successfully."
echo "------------------------------------------------------------"

} >> "$LOG_FILE" 2>&1
