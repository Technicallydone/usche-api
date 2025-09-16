#!/bin/bash
set -e

echo "Starting Django migrations script..."

# Go to project root
echo "Changing directory to /var/www/usche"
cd /var/www/usche             

# Activate virtual environment
echo "Activating virtual environment..."
source env/bin/activate

# Go to Django API directory
echo "Changing directory to /var/www/usche/usche-api"
cd /var/www/usche/usche-api

# Run makemigrations
echo "Running makemigrations..."
python3 manage.py makemigrations

# Run migrate
echo "Applying migrations..."
python3 manage.py migrate

echo "Migrations completed successfully!"
