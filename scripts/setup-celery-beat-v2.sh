#!/bin/bash
SERVICE_FILE="/etc/systemd/system/celery-beat-v2.service"

echo "Creating Celery Beat v2 service..."

sudo tee $SERVICE_FILE > /dev/null <<EOL
[Unit]
Description=Celery Beat Service v2
After=network.target redis.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/root/project/usche_app
ExecStart=/root/project/usche_env/bin/celery -A usche_app beat --loglevel=info --logfile=/var/log/celerybeat-v2.log
Restart=always
TimeoutStartSec=600

[Install]
WantedBy=multi-user.target
EOL

echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Enabling Celery Beat v2..."
sudo systemctl enable celery-beat-v2

echo "Starting Celery Beat v2..."
sudo systemctl start celery-beat-v2

echo "Celery Beat v2 setup complete ✅"
