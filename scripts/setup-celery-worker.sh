#!/bin/bash

SERVICE_FILE="/etc/systemd/system/celery-worker.service"

echo "Creating Celery Worker service..."

sudo tee "$SERVICE_FILE" > /dev/null <<EOL
[Unit]
Description=Celery Worker Service v2
After=network.target redis.service

[Service]
Type=simple

User=deploy
Group=deploy

WorkingDirectory=/var/www/usche-api

# Auto-create /var/log/celery with correct permissions
LogsDirectory=celery
LogsDirectoryMode=0755

ExecStart=/var/www/env/bin/celery -A usche_app worker \
  --loglevel=info \
  --logfile=/var/log/celery/worker.log

Restart=always
RestartSec=5
TimeoutStartSec=600

[Install]
WantedBy=multi-user.target
EOL

echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Enabling Celery Worker..."
sudo systemctl enable celery-worker

echo "Restarting Celery Worker..."
sudo systemctl restart celery-worker

echo "Celery Worker setup complete"
