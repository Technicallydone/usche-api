#!/bin/bash
SERVICE_FILE="/etc/systemd/system/celery-v2.service"

echo "Creating Celery Worker v2 service..."

sudo tee $SERVICE_FILE > /dev/null <<EOL
[Unit]
Description=Celery Worker Service v2
After=network.target redis.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/var/www/usche/usche-api
ExecStart=/var/www/usche/env/bin/celery -A usche_app worker --loglevel=info --logfile=/var/log/celeryv2.log
Restart=always
TimeoutStartSec=600

[Install]
WantedBy=multi-user.target
EOL

echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Enabling Celery Worker v2..."
sudo systemctl enable celery-v2

echo "Starting Celery Worker v2..."
sudo systemctl start celery-v2

echo "Celery Worker v2 setup complete ✅"
