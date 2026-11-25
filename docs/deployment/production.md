# Production Deployment Guide

## Overview

This guide covers deploying My Life AI to a Linux VPS using Docker Compose with production configurations.

## Server Requirements

- **OS**: Ubuntu 22.04+ / Debian 12+ / RHEL 9+
- **CPU**: 2+ vCPUs
- **RAM**: 4GB+ (8GB recommended)
- **Storage**: 20GB+ SSD
- **Network**: Public IPv4, domain name with DNS configured

## Pre-Deployment Setup

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Install Docker Compose v2
sudo apt install docker-compose-plugin

# Verify installations
docker --version
docker compose version

# Logout and login for group changes
newgrp docker
```

### 2. Firewall Configuration

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Check status
sudo ufw status
```

### 3. Domain & SSL (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is set up automatically
sudo certbot renew --dry-run
```

## Deployment Steps

### 1. Clone Repository

```bash
# Create deployment user (optional but recommended)
sudo adduser --disabled-password --gecos "" mylife
sudo usermod -aG docker mylife

# Switch to deployment user
sudo su - mylife

# Clone repository
git clone git@github.com:LearnerAnuprash/MyLifeAi.git
cd MyLifeAi
```

### 2. Configure Environment

```bash
# Copy production environment templates
cp backend/.env.example backend/.env.production
cp frontend/.env.example frontend/.env.production
cp docker-compose.yml docker-compose.prod.yml

# Generate secure secrets
# SECRET_KEY (64+ random chars)
openssl rand -base64 48

# Database password
openssl rand -base64 32

# Edit production environment files
nano backend/.env.production
nano frontend/.env.production
```

### 3. Backend Production Environment (.env.production)

```bash
# Required - CHANGE THESE
SECRET_KEY=your-generated-64-char-secret-key
DATABASE_URL=postgresql+asyncpg://mylife:your-db-password@postgres:5432/mylife
REDIS_URL=redis://redis:6379/0

# Security
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# CORS - Your production domain
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# AI Providers (add your keys)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Email (configure for production)
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=your-email@domain.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=My Life AI

# Rate limiting
RATE_LIMIT_REQUESTS=200
RATE_LIMIT_WINDOW=1minute
```

### 4. Frontend Production Environment (.env.production)

```bash
VITE_API_URL=https://yourdomain.com/graphql
VITE_WS_URL=wss://yourdomain.com/graphql
VITE_APP_NAME=My Life AI
VITE_APP_VERSION=0.1.0
```

### 5. Production Docker Compose (docker-compose.prod.yml)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: mylife-postgres-prod
    environment:
      POSTGRES_DB: mylife
      POSTGRES_USER: mylife
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    secrets:
      - db_password
    networks:
      - mylife-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mylife -d mylife"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: mylife-redis-prod
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - mylife-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 5s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    container_name: mylife-backend-prod
    env_file:
      - backend/.env.production
    environment:
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    volumes:
      - ./backend/uploads:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - mylife-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    container_name: mylife-celery-worker-prod
    env_file:
      - backend/.env.production
    environment:
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - mylife-network
    restart: unless-stopped
    command: celery -A app.workers.celery_app worker --loglevel=warning --concurrency=4
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    container_name: mylife-celery-beat-prod
    env_file:
      - backend/.env.production
    environment:
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
    volumes:
      - celery_beat_data:/app/celerybeat-schedule
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - mylife-network
    restart: unless-stopped
    command: celery -A app.workers.celery_app beat --loglevel=warning --scheduler celery.beat.PersistentScheduler --schedule=/app/celerybeat-schedule

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production
    container_name: mylife-frontend-prod
    env_file:
      - frontend/.env.production
    depends_on:
      - backend
    networks:
      - mylife-network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: mylife-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on:
      - frontend
      - backend
    networks:
      - mylife-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  celery_beat_data:

secrets:
  db_password:
    file: ./secrets/db_password.txt

networks:
  mylife-network:
    driver: bridge
```

### 6. Nginx Configuration

Create `nginx/nginx.conf`:

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;
    
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    upstream frontend {
        server frontend:80;
    }
    
    upstream backend {
        server backend:8000;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    
    include /etc/nginx/conf.d/*.conf;
}
```

Create `nginx/conf.d/default.conf`:

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # GraphQL API
    location /graphql {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for subscriptions
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
    
    # Health check
    location /health {
        proxy_pass http://backend;
        access_log off;
    }
    
    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        proxy_pass http://frontend;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 7. Secrets Setup

```bash
# Create secrets directory
mkdir -p secrets

# Generate database password
openssl rand -base64 32 > secrets/db_password.txt

# Generate Redis password
openssl rand -base64 32 > secrets/redis_password.txt

# Set permissions
chmod 600 secrets/*.txt
```

### 8. Deploy

```bash
# Build and start
docker compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Check status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

## Maintenance

### Backup Database

```bash
# Create backup
docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U mylife mylife > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress
gzip backup_*.sql

# Restore
gunzip -c backup_20261124_120000.sql.gz | docker compose -f docker-compose.prod.yml exec -T postgres psql -U mylife mylife
```

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and deploy
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Run migrations if needed
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Log Rotation

```bash
# Configure logrotate
sudo tee /etc/logrotate.d/mylife <<EOF
/var/lib/docker/containers/*/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
```

### Monitoring

```bash
# Check container health
docker compose -f docker-compose.prod.yml ps

# Resource usage
docker stats --no-stream

# Check application logs
docker compose -f docker-compose.prod.yml logs --tail=100 backend
docker compose -f docker-compose.prod.yml logs --tail=100 frontend
```

## Security Checklist

- [ ] Strong SECRET_KEY (64+ chars)
- [ ] Strong database password
- [ ] Strong Redis password
- [ ] HTTPS with valid TLS certificate
- [ ] Security headers in Nginx
- [ ] Rate limiting enabled
- [ ] Firewall configured (only 80, 443, 22)
- [ ] Regular security updates
- [ ] Database backups scheduled
- [ ] Log monitoring configured
- [ ] API keys stored securely (not in repo)

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs service-name

# Check resource limits
docker compose -f docker-compose.prod.yml top service-name
```

### Database Connection Issues

```bash
# Test connection
docker compose -f docker-compose.prod.yml exec backend python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql://mylife:password@postgres:5432/mylife')
    print(await conn.fetchval('SELECT 1'))
    await conn.close()
asyncio.run(test())
"
```

### SSL Certificate Issues

```bash
# Renew certificate
sudo certbot renew --nginx

# Check certificate
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -text -noout
```