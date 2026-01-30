# Deployment Guide

This guide covers deploying the Habits Factory application using Docker Compose with PostgreSQL and Gunicorn.

## Prerequisites

- Docker and Docker Compose installed
- A Unix-like system (Linux, macOS) or Windows with WSL2
- A production-ready PostgreSQL instance or use the included Docker service

## Setup Steps

### 1. Prepare Environment Variables

Copy the template and configure for your environment:

```bash
cp .env.example .env
```

Edit `.env` with your production values:

```env
SECRET_KEY=your-very-secret-key-min-50-chars
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_NAME=habitsfactory
DB_USER=postgres
DB_PASSWORD=your-secure-db-password
DB_HOST=db
DB_PORT=5432

CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
SECURE_SSL_REDIRECT=True
VITE_API_URL=https://yourdomain.com/api
```

### 2. Generate Django Secret Key

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Copy the output and set it in `.env` as `SECRET_KEY`.

### 3. Build and Start Services

```bash
# Build images
docker-compose build

# Start services in detached mode
docker-compose up -d

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### 4. Verify Services

The application will be accessible at:
- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:5173
- **Database**: localhost:5432

### 5. Database Migrations

Migrations run automatically on container startup via the entrypoint script. To run manually:

```bash
docker-compose exec backend python manage.py migrate
```

### 6. Create Superuser (Optional)

```bash
docker-compose exec backend python manage.py createsuperuser
```

## Production Deployment

### With Nginx Reverse Proxy

For production, add an Nginx service to handle SSL termination and reverse proxying:

```yaml
# Add to docker-compose.yml
nginx:
  image: nginx:alpine
  container_name: habitsfactory_nginx
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - ./ssl:/etc/nginx/ssl:ro
  depends_on:
    - backend
    - frontend
  networks:
    - habitsfactory_network
```

### SSL Certificates

Use Let's Encrypt with Certbot:

```bash
certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

Copy certificates to `./ssl/` directory.

### Environment Variable Configuration

Update `.env` for production:

```env
SECURE_SSL_REDIRECT=True
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Useful Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Execute commands in container
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py shell

# Collect static files manually
docker-compose exec backend python manage.py collectstatic --noinput

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Restart services
docker-compose restart

# Rebuild images
docker-compose build --no-cache
```

## Database Backup & Restore

### Backup

```bash
docker-compose exec db pg_dump -U postgres habitsfactory > backup.sql
```

### Restore

```bash
docker-compose exec -T db psql -U postgres habitsfactory < backup.sql
```

## Troubleshooting

### Database Connection Issues

```bash
# Test database connection
docker-compose exec backend python manage.py dbshell

# Check database logs
docker-compose logs db
```

### Static Files Not Loading

```bash
# Force collect static files
docker-compose exec backend python manage.py collectstatic --clear --noinput
```

### Port Already in Use

Change ports in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Change host port from 8000 to 8001
```

### Container Won't Start

```bash
# View detailed logs
docker-compose logs backend

# Rebuild without cache
docker-compose build --no-cache

# Check Docker image
docker images
```

## Performance Tuning

### Gunicorn Workers

Adjust `docker-compose.yml` backend command:

```bash
gunicorn --workers 8 --worker-class gevent ...  # For CPU-bound
gunicorn --workers 2 --worker-class gthread ... # For I/O-bound
```

Rule of thumb: `workers = (2 * num_cores) + 1`

### Database Connection Pooling

Consider adding pgBouncer for connection pooling in high-traffic scenarios.

## Security Checklist

- [ ] Set unique, strong `SECRET_KEY`
- [ ] Set strong `DB_PASSWORD`
- [ ] Configure `ALLOWED_HOSTS` correctly
- [ ] Enable `SECURE_SSL_REDIRECT` in production
- [ ] Use HTTPS with valid certificates
- [ ] Update `CORS_ALLOWED_ORIGINS` to your domain only
- [ ] Set `DEBUG=False`
- [ ] Configure firewall rules
- [ ] Regular database backups
- [ ] Monitor logs for errors

## Monitoring & Logging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Health Checks

Services have health checks configured:

```bash
docker-compose ps  # Shows health status
```

## Scaling

For production with multiple instances, consider:

1. **Load Balancing**: Use Docker Swarm or Kubernetes
2. **Database**: Use managed PostgreSQL service (AWS RDS, DigitalOcean, etc.)
3. **Static Files**: Serve from CDN or S3
4. **Caching**: Add Redis service for session/cache
5. **Background Tasks**: Add Celery + Redis for async tasks
