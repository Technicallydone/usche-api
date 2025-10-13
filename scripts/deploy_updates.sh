#!/bin/bash
set -e

DJANGO_DIR="/var/www/usche/usche-api"
VENV_ACTIVATE="/var/www/usche/env/bin/activate"
SERVICE_NAME="gunicorn_usche"
CELERY_SERVICE="celery-v2"
CELERY_BEAT_SERVICE="celery-beat-v2"

echo "Starting Django deployment..."

# Step 1: Go to Django project directory
echo "Changing directory to $DJANGO_DIR"
cd $DJANGO_DIR

# Step 2: Ask whether to pull latest changes
read -p "Do you want to pull latest changes from GitHub? (y/n): " PULL
if [[ "$PULL" == "y" || "$PULL" == "Y" ]]; then
    echo "Pulling latest changes from GitHub..."
    git pull origin main
else
    echo "Skipping Git pull."
fi

# Step 3: Activate virtual environment
echo "Activating virtual environment..."
source $VENV_ACTIVATE

# Step 4: Run migrations
echo "Running makemigrations..."
python3 manage.py makemigrations

echo "Running migrate..."
python3 manage.py migrate

# Step 5: Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Step 6: Restart services

echo "Restarting Gunicorn service: $SERVICE_NAME"
sudo systemctl restart $SERVICE_NAME

echo "Restarting Celery service: $CELERY_SERVICE"
sudo systemctl restart $CELERY_SERVICE

echo "Restarting Celery Beat service: $CELERY_BEAT_SERVICE"
sudo systemctl restart $CELERY_BEAT_SERVICE

# Step 7: Show status
echo "Checking Gunicorn service status..."
sudo systemctl status $SERVICE_NAME --no-pager

echo "Checking Celery service status..."
sudo systemctl status $CELERY_SERVICE --no-pager

echo "Checking Celery Beat service status..."
sudo systemctl status $CELERY_BEAT_SERVICE --no-pager

echo "Django deployment completed successfully."
