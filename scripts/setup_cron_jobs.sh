#!/bin/bash
# ------------------------------------------------------------------
# Setup cron job for Django backup_every_12hrs.sh
# ------------------------------------------------------------------

set -e

# Path to backup script
BACKUP_SCRIPT="$(dirname "$(realpath "$0")")/backup_every_12hrs.sh"

# Log file
LOG_DIR="$(dirname "$(realpath "$0")")/../logs"
mkdir -p "$LOG_DIR"
BACKUP_LOG="$LOG_DIR/db_backup.log"

# Helper function to safely add a cron job if it doesn't already exist
add_cron_job() {
    local job="$1"
    local tmpfile
    tmpfile=$(mktemp)
    crontab -l 2>/dev/null > "$tmpfile" || true

    if grep -Fq "$job" "$tmpfile"; then
        echo "[SKIP] Cron job already exists: $job"
    else
        echo "$job" >> "$tmpfile"
        crontab "$tmpfile"
        echo "[ADD] Cron job added: $job"
    fi

    rm -f "$tmpfile"
}

# Add cron job: every 12 hours
add_cron_job "0 */12 * * * $BACKUP_SCRIPT >> $BACKUP_LOG 2>&1"

echo "Backup cron job configured successfully."
