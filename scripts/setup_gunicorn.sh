#!/bin/bash
set -e

SERVICE_NAME="gunicorn_usche"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

echo "Starting Gunicorn service setup..."

# Create systemd service file
echo "Creating systemd service file at $SERVICE_FILE"
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=gunicorn daemon for USCHE Django app
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/usche-api
ExecStart=/var/www/env/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/gunicorn.sock usche_app.wsgi:application
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd to pick up new service
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable service to start on boot
echo "Enabling $SERVICE_NAME to start on boot..."
sudo systemctl enable $SERVICE_NAME

# Start Gunicorn service
echo "Starting $SERVICE_NAME..."
sudo systemctl start $SERVICE_NAME

# Check status
echo "Checking status of $SERVICE_NAME..."
sudo systemctl status $SERVICE_NAME --no-pager

echo "Gunicorn service setup completed successfully!"
