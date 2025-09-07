#!/bin/bash
set -e

DJANGO_DIR="/var/www/usche/usche-api"
VENV_ACTIVATE="/var/www/usche/env/bin/activate"
SERVICE_NAME="gunicorn_usche"

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

# Step 5: Restart Gunicorn
echo "Restarting Gunicorn service: $SERVICE_NAME"
sudo systemctl restart $SERVICE_NAME

# Step 6: Show status
echo "Checking Gunicorn service status..."
sudo systemctl status $SERVICE_NAME --no-pager

echo "Django deployment completed successfully."
