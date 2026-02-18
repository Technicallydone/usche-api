#!/bin/bash

SERVICE_FILE="/etc/systemd/system/celery-beat.service"

echo "Creating Celery Beat service..."

sudo tee "$SERVICE_FILE" > /dev/null <<EOL
[Unit]
Description=Celery Beat Service v2
After=network.target redis.service

[Service]
Type=simple

User=deploy
Group=deploy

WorkingDirectory=/var/www/usche-api

# Auto-create /var/log/celery
LogsDirectory=celery
LogsDirectoryMode=0755

# Optional: ensure virtualenv is used
Environment="PATH=/var/www/env/bin:/usr/bin"
Environment="PYTHONUNBUFFERED=1"

ExecStart=/var/www/env/bin/celery -A usche_app beat \
  --loglevel=info \
  --logfile=/var/log/celery/beat.log

Restart=always
RestartSec=5
TimeoutStartSec=600

[Install]
WantedBy=multi-user.target
EOL

echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Enabling Celery Beat..."
sudo systemctl enable celery-beat

echo "Restarting Celery Beat..."
sudo systemctl restart celery-beat

echo "Celery Beat setup complete"
