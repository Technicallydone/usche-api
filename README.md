### Installation

1. Create the project directory:

   ```bash
   mkdir project
   cd project
   ```

2. Create a virtual environment to isolate our package dependencies locally:

   ```bash
   python3 -m venv env
   ```

3. Activate the virtual environment:

   ```bash
   source env/bin/activate # On Windows use `env\Scripts\activate`

   ```

4. Clone the repository:

   ```bash
   git clone https://github.com/Technicallydone/usche_api.git
   cd university-api
   ```

5. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Create a `.env` file in the root of your project directory. Copy the contents of `.env.example` and replace the placeholder values with your actual database credentials:

```bash
SECRET_KEY=your_secret_key
ENGINE=django.db.backends.mysql
DB_NAME=your_database_name  # Use the name you created in MySQL
DB_USER=root
DB_PASSWORD=your_mysql_password # Your MySQL root password (or other user)
DB_HOST=localhost
DB_PORT=3306

DEBUG=True
APP_BASE=http://127.0.0.1:8000
SPEAKER_BASE_URL=http://127.0.0.1:8000/v1/speaker/Speakers/speaker-image
SPONSOR_LOGO_BASE_URL=http://127.0.0.1:8000/v1/sponsor/sponsors/sponsor-logo
ABSTRACT_DOCUMENT_URL=http://127.0.0.1:8000/v1/abstract/abstracts/abstract-document
PAYMENT_SLIP_URL=http://127.0.0.1:8000/v1/payment/payments/payment-slip
FRONTEND_BASE_URL=http://localhost:5173

STATIC_URL=/static/
STATIC_ROOT=/path/to/assets/static/  # You might want to create this directory later

MEDIA_URL=/media/
MEDIA_ROOT=/path/to/assets/media    # You might want to create this directory later

# Email settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=duma.duhosting.tz
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=usche@usche.ac.tz
EMAIL_HOST_PASSWORD=your_email_password # Your email password
DEFAULT_FROM_EMAIL=usche@usche.ac.tz

MAIL_TOKEN=SWknpd2iGvOAurlhvr6MFCTDMtQVO1CzaoNpNFEaLvc
MAIL_ENDPOINT=https://nbtsms.kedeshlimited.com/mail/send/

# Third part mail conf
SPARK_POST_API_KEY=f5ab4fd27d6d634a3b6207912c79853d08447623
SPARK_POST_FROM_EMAIL=info@email.usche.ac.tz
SPARK_POST_API=https://api.sparkpost.com/api/v1/transmissions

# Queue
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
```

7. Current active branch is v2, you need to checkout to v2 branch using

```bash
git checkout v2
```

8. Make migrations

```bash
python manage.py makemigrations
```

9. Migrate your migrations

```bash
python manage.py migrate
```

10. You have successfully installed app, you can run your application

```bash
python manage.py runserver
```

# This application uses celery to automate tasks on background prevending blocking of requests. you will need to start the celery

11. Open separate terminal windows (make sure the virtual environment is activated in each) and run:

# Start the Celery worker

```bash
celery -A usche_app worker --loglevel=info
```

# Start the Celery beat scheduler

```bash
celery -A usche_app beat --loglevel=info
```

Remember: Celery Beat will not function if the Celery worker is started.

# Start Celery Flower (optional monitoring tool)

```bash
celery -A usche_app flower --address=127.0.0.1 --port=5555
```

You can access Flower at http://127.0.0.1:5555/

Celery Documentation: https://docs.celeryq.dev/en/stable/
Celery Beat schedules tasks to be executed by the worker.
# usche-api
