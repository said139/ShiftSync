# ShiftSync — Production Deployment Guide (Ubuntu Server, PostgreSQL, Gunicorn & Nginx)

This guide covers deploying **ShiftSync** on **Ubuntu 22.04 / 24.04 LTS** using **PostgreSQL**, **Gunicorn** (WSGI application server), and **Nginx** (reverse proxy and static asset server).

---

## 1. Install Operating System Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip postgresql postgresql-contrib nginx nodejs npm git
```

---

## 2. Configure PostgreSQL Database

```bash
sudo -u postgres psql
```

Inside the `psql` prompt:

```sql
CREATE USER shiftsync_user WITH PASSWORD 'StrongProductionPassword!2026';
CREATE DATABASE shiftsync_db OWNER shiftsync_user;
ALTER ROLE shiftsync_user SET client_encoding TO 'utf8';
ALTER ROLE shiftsync_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE shiftsync_user SET timezone TO 'UTC';
\q
```

---

## 3. Set Up Backend & NLP Models

```bash
sudo mkdir -p /var/www/shiftsync
sudo chown -R $USER:$USER /var/www/shiftsync
git clone <repository-url> /var/www/shiftsync
cd /var/www/shiftsync

python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install gunicorn
```

Create `/var/www/shiftsync/.env` from `.env.example`:

```ini
POSTGRES_DB=shiftsync_db
POSTGRES_USER=shiftsync_user
POSTGRES_PASSWORD=StrongProductionPassword!2026
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

DJANGO_SECRET_KEY=<generate-64-char-random-secret>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=shiftsync.example.com,127.0.0.1
CORS_ALLOWED_ORIGINS=https://shiftsync.example.com

NLP_PROVIDER=auto
NLP_LOW_CONFIDENCE_THRESHOLD=60.0
```

Apply migrations, fine-tune/verify NLP artifacts, and collect static files:

```bash
cd /var/www/shiftsync/backend
../.venv/bin/python manage.py migrate
../.venv/bin/python nlp_service/train_transformer.py
../.venv/bin/python manage.py collectstatic --noinput
```

---

## 4. Build React Production Frontend

```bash
cd /var/www/shiftsync/frontend
npm ci
npm run build
```

This outputs the production static bundle to `/var/www/shiftsync/frontend/dist`.

---

## 5. Configure Gunicorn Systemd Service

Create `/etc/systemd/system/shiftsync.service`:

```ini
[Unit]
Description=ShiftSync Gunicorn Daemon
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/shiftsync/backend
EnvironmentFile=/var/www/shiftsync/.env
ExecStart=/var/www/shiftsync/.venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/shiftsync.sock \
    --timeout 60 \
    shiftsync_backend.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start Gunicorn:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now shiftsync.service
```

---

## 6. Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/shiftsync`:

```nginx
server {
    listen 80;
    server_name shiftsync.example.com;

    root /var/www/shiftsync/frontend/dist;
    index index.html;

    # Proxy REST API & OpenAPI Docs to Gunicorn
    location /api/ {
        include proxy_params;
        proxy_pass http://unix:/run/shiftsync.sock;
    }

    location /django-admin/ {
        include proxy_params;
        proxy_pass http://unix:/run/shiftsync.sock;
    }

    location /static/ {
        alias /var/www/shiftsync/backend/staticfiles/;
    }

    # React Router SPA Fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Enable the site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/shiftsync /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```
