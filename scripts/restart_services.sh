#!/bin/bash

# Services to restart
SERVICES=(
  "celery-worker"
  "celery-beat"
  "gunicorn_usche"
)

echo "Restarting services..."

for SERVICE in "${SERVICES[@]}"; do
  echo "Restarting $SERVICE..."
  sudo systemctl restart "$SERVICE"
  # Optionally, check status
  sudo systemctl status "$SERVICE" --no-pager | head -n 10
done

echo "All services restarted successfully."
