# CIHRPT Deployment Guide

## Deploying CIHRPT on VPS (cihrpt.xeradb.com) with PostgreSQL

This guide provides step-by-step instructions for deploying the CIHRPT (CIHR Projects Tracker) Django application on your VPS with PostgreSQL database.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [PostgreSQL Installation & Configuration](#postgresql-installation--configuration)
4. [Application Deployment](#application-deployment)
5. [Web Server Configuration (Nginx + Gunicorn)](#web-server-configuration)
6. [SSL Certificate Setup](#ssl-certificate-setup)
7. [Process Management (Systemd)](#process-management)
8. [Environment Variables](#environment-variables)
9. [Database Migration](#database-migration)
10. [Static Files & Media](#static-files--media)
11. [Monitoring & Maintenance](#monitoring--maintenance)
12. [Troubleshooting](#troubleshooting)

## Prerequisites

- VPS with Ubuntu 20.04+ or similar Linux distribution
- Root or sudo access
- Domain pointing to your VPS (cihrpt.xeradb.com)
- Basic knowledge of Linux command line

## Server Setup

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git htop unzip
```

### 2. Create Application User

```bash
sudo adduser cihrpt
sudo usermod -aG sudo cihrpt
sudo su - cihrpt
```

### 3. Install Python and Development Tools

```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y build-essential libpq-dev
```

## PostgreSQL Installation & Configuration

### 1. Install PostgreSQL

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Create Database and User

```bash
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE cihrpt_production;
CREATE USER cihrpt_user WITH PASSWORD 'your_secure_password_here';
ALTER ROLE cihrpt_user SET client_encoding TO 'utf8';
ALTER ROLE cihrpt_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE cihrpt_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE cihrpt_production TO cihrpt_user;
\q
```

### 3. Configure PostgreSQL for Remote Connections (if needed)

```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
# Uncomment and modify:
# listen_addresses = 'localhost'

sudo nano /etc/postgresql/14/main/pg_hba.conf
# Add at the end:
# local   cihrpt_production    cihrpt_user                     md5

sudo systemctl restart postgresql
```

## Application Deployment

### 1. Clone Repository

```bash
cd /home/cihrpt
git clone https://github.com/choxos/CIHRPT.git
cd CIHRPT
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### 4. Update Requirements (if needed)

```bash
# Add to requirements.txt:
echo "gunicorn==21.2.0" >> requirements.txt
echo "psycopg2-binary==2.9.10" >> requirements.txt
```

## Environment Variables

### 1. Create Environment File

```bash
nano /home/cihrpt/CIHRPT/.env
```

### 2. Add Environment Variables

```env
# Database Configuration
DATABASE_URL=postgresql://cihrpt_user:Choxos10203040@localhost:5432/cihrpt_production

# Django Settings
SECRET_KEY='mf)d6dx=6)efzl_3vplj0@@0ml8=!h3wh*0^)7wk5j1%yr7s1q'
DEBUG=False
ALLOWED_HOSTS=cihrpt.xeradb.com,www.cihrpt.xeradb.com,91.99.161.136,localhost,127.0.0.1

# Security Settings
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True

# Static Files
STATIC_ROOT=/home/cihrpt/CIHRPT/staticfiles
MEDIA_ROOT=/home/cihrpt/CIHRPT/media

# Data Files
CIHRPT_DATA_DIR=/home/cihrpt/CIHRPT/cihr_projects_jsons
CIHRPT_CSV_FILE=/home/cihrpt/CIHRPT/cihr_projects.csv
```

### 3. Update Django Settings

```bash
nano cihrpt_project/settings.py
```

Add at the top:

```python
import os
from decouple import config
import dj_database_url

# Environment variables
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL')
    )
}

# Security settings (add these)
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
    SECURE_CONTENT_TYPE_NOSNIFF = config('SECURE_CONTENT_TYPE_NOSNIFF', default=True, cast=bool)
    SECURE_BROWSER_XSS_FILTER = config('SECURE_BROWSER_XSS_FILTER', default=True, cast=bool)

# Static files
STATIC_ROOT = config('STATIC_ROOT', default=os.path.join(BASE_DIR, 'staticfiles'))
MEDIA_ROOT = config('MEDIA_ROOT', default=os.path.join(BASE_DIR, 'media'))
MEDIA_URL = '/media/'

# Data directories
CIHRPT_DATA_DIR = config('CIHRPT_DATA_DIR', default=BASE_DIR / 'cihr_projects_jsons')
CIHRPT_CSV_FILE = config('CIHRPT_CSV_FILE', default=BASE_DIR / 'cihr_projects.csv')
```

## Database Migration

### 1. Run Migrations

```bash
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate
```

### 2. Create Superuser

```bash
python manage.py createsuperuser
```

### 3. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 4. Import Data

```bash
# Import CSV data first
python manage.py import_csv_only

# Then update with JSON analysis (if available)
python manage.py update_json_analysis --limit 100
```

## Web Server Configuration

### 1. Install Nginx

```bash
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 2. Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/cihrpt
```

```nginx
server {
    listen 80;
    server_name cihrpt.xeradb.com www.cihrpt.xeradb.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name cihrpt.xeradb.com www.cihrpt.xeradb.com;

    # SSL Configuration (will be updated by Certbot)
    ssl_certificate /etc/letsencrypt/live/cihrpt.xeradb.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cihrpt.xeradb.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Static files
    location /static/ {
        alias /home/cihrpt/CIHRPT/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/cihrpt/CIHRPT/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Security
    location ~ /\.(?!well-known).* {
        deny all;
    }
}
```

### 3. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/cihrpt /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificate Setup

### 1. Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 2. Obtain SSL Certificate

```bash
sudo certbot --nginx -d cihrpt.xeradb.com -d www.cihrpt.xeradb.com
```

### 3. Test Automatic Renewal

```bash
sudo certbot renew --dry-run
```

## Process Management

### 1. Create Gunicorn Service

```bash
sudo nano /etc/systemd/system/cihrpt.service
```

```ini
[Unit]
Description=CIHRPT Django Application
After=network.target

[Service]
User=cihrpt
Group=www-data
WorkingDirectory=/home/cihrpt/CIHRPT
Environment="PATH=/home/cihrpt/CIHRPT/venv/bin"
EnvironmentFile=/home/cihrpt/CIHRPT/.env
ExecStart=/home/cihrpt/CIHRPT/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind 127.0.0.1:8000 \
          cihrpt_project.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 2. Start and Enable Service

```bash
sudo systemctl daemon-reload
sudo systemctl start cihrpt
sudo systemctl enable cihrpt
sudo systemctl status cihrpt
```

## Static Files & Media

### 1. Set Proper Permissions

```bash
sudo chown -R cihrpt:www-data /home/cihrpt/CIHRPT
sudo chmod -R 755 /home/cihrpt/CIHRPT
sudo chmod -R 755 /home/cihrpt/CIHRPT/staticfiles
sudo chmod -R 755 /home/cihrpt/CIHRPT/media
```

### 2. Create Media Directory

```bash
mkdir -p /home/cihrpt/CIHRPT/media
```

## Monitoring & Maintenance

### 1. Log Monitoring

```bash
# Application logs
sudo journalctl -u cihrpt -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Regular Maintenance Script

```bash
nano /home/cihrpt/maintenance.sh
```

```bash
#!/bin/bash
cd /home/cihrpt/CIHRPT
source venv/bin/activate

# Pull latest changes
git pull origin main

# Install any new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart cihrpt
sudo systemctl reload nginx

echo "Deployment updated successfully!"
```

```bash
chmod +x /home/cihrpt/maintenance.sh
```

### 3. Database Backup Script

```bash
nano /home/cihrpt/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/cihrpt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U cihrpt_user cihrpt_production > $BACKUP_DIR/cihrpt_production_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete

echo "Backup completed: cihrpt_production_$DATE.sql"
```

```bash
chmod +x /home/cihrpt/backup.sh

# Add to crontab for daily backups
crontab -e
# Add: 0 2 * * * /home/cihrpt/backup.sh
```

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**
   ```bash
   sudo systemctl status cihrpt
   sudo journalctl -u cihrpt -n 50
   ```

2. **Permission Denied**
   ```bash
   sudo chown -R cihrpt:www-data /home/cihrpt/CIHRPT
   sudo chmod -R 755 /home/cihrpt/CIHRPT
   ```

3. **Database Connection Issues**
   ```bash
   sudo -u postgres psql -c "\l"
   sudo systemctl status postgresql
   ```

4. **Static Files Not Loading**
   ```bash
   python manage.py collectstatic --noinput
   sudo nginx -t && sudo systemctl reload nginx
   ```

### Performance Optimization

1. **Database Optimization**
   ```sql
   -- Connect to PostgreSQL and run:
   ANALYZE;
   REINDEX DATABASE cihrpt_production;
   ```

2. **Nginx Caching**
   Add to nginx config:
   ```nginx
   location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
       expires 1y;
       add_header Cache-Control "public, immutable";
   }
   ```

3. **Gunicorn Workers**
   Adjust workers based on CPU cores:
   ```bash
   # Formula: (2 x CPU cores) + 1
   # For 2 cores: --workers 5
   ```

## Security Checklist

- [ ] SSL certificate installed and auto-renewal configured
- [ ] Firewall configured (UFW)
- [ ] Database user has minimal privileges
- [ ] Debug mode disabled in production
- [ ] Strong passwords used
- [ ] Regular security updates applied
- [ ] Backup strategy implemented
- [ ] Log monitoring in place

## Final Steps

1. Test the application: https://cihrpt.xeradb.com
2. Verify SSL certificate
3. Test all functionality
4. Set up monitoring
5. Schedule regular backups
6. Document any custom configurations

Your CIHRPT application should now be successfully deployed on your VPS with PostgreSQL! 