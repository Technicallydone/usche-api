#!/bin/bash
# ------------------------------------------------------------------
# Remove cron job for Django backup_every_12hrs.sh
# ------------------------------------------------------------------

set -e

# Path to backup script
BACKUP_SCRIPT="$(dirname "$(realpath "$0")")/backup_every_12hrs.sh"

# Remove cron job
crontab -l 2>/dev/null \
    | grep -v "$BACKUP_SCRIPT" \
    | crontab -

echo "Backup cron job removed successfully."
