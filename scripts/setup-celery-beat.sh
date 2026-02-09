[Service]
Type=simple

User=deploy
Group=deploy

WorkingDirectory=/var/www/usche-api

# Auto-create /var/log/celery
LogsDirectory=celery
LogsDirectoryMode=0755

ExecStart=/var/www/env/bin/celery -A usche_app beat \
  --loglevel=info \
  --logfile=/var/log/celery/beat.log

Restart=always
RestartSec=5
