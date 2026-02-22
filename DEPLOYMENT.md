# Deployment Guide - Intelligent Data Dictionary

## Local Development

### Option 1: Run Everything with Docker
```bash
# Build and start all services
docker-compose up --build

# Access:
# - Frontend: http://localhost:5173 (dev server) or http://localhost:80 (nginx)
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Option 2: Run Frontend Separately (Development)
```bash
# Terminal 1: Start backend services
docker-compose up db redis api

# Terminal 2: Start frontend dev server
cd frontend
npm install
npm run dev

# Access: http://localhost:5173
```

---

## Production Deployment

### Prerequisites
- Linux server (Ubuntu 22.04 recommended)
- Docker & Docker Compose installed
- Domain name (optional, for SSL)
- Groq API key

### Step 1: Clone Repository
```bash
git clone https://github.com/narang25/intelligent-data-dictionary-agent.git
cd intelligent-data-dictionary-agent
```

### Step 2: Configure Environment
```bash
# Copy example env file
cp .env.example .env.prod

# Edit with your values
nano .env.prod
```

Required variables:
```env
DB_PASSWORD=secure_random_password
GROQ_API_KEY=your_groq_api_key
JWT_SECRET=generate_with_openssl_rand_hex_32
```

### Step 3: Build & Deploy
```bash
# Build all containers
docker-compose -f docker-compose.prod.yml build

# Start in detached mode
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Step 4: Initialize Database
```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Load sample data (optional)
docker-compose -f docker-compose.prod.yml exec api python -m app.admin.load_olist

# Generate documentation
docker-compose -f docker-compose.prod.yml exec api python -c "from app.admin.run_auto_doc import run; run()"
```

### Step 5: Verify Deployment
```bash
# Check health endpoint
curl http://localhost/api/health

# Check frontend
curl http://localhost
```

---

## Cloud Deployment Options

### Option A: AWS EC2

1. **Launch EC2 Instance**
   - AMI: Ubuntu 22.04 LTS
   - Instance type: t3.medium (minimum)
   - Storage: 30GB SSD
   - Security Group: Allow ports 22, 80, 443

2. **Install Docker**
   ```bash
   sudo apt update
   sudo apt install docker.io docker-compose -y
   sudo usermod -aG docker $USER
   ```

3. **Deploy**
   ```bash
   git clone <repo>
   cd intelligent-data-dictionary
   cp .env.example .env.prod
   # Edit .env.prod
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Configure SSL (Optional)**
   ```bash
   # Install Certbot
   sudo apt install certbot
   sudo certbot certonly --standalone -d yourdomain.com
   ```

### Option B: DigitalOcean Droplet

1. **Create Droplet**
   - Image: Docker on Ubuntu
   - Size: 2GB RAM / 2 vCPUs
   - Region: Closest to users

2. **Deploy**
   ```bash
   ssh root@your-droplet-ip
   git clone <repo>
   cd intelligent-data-dictionary
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Option C: Railway.app (Easiest)

1. Connect GitHub repository
2. Add environment variables in Railway dashboard
3. Railway auto-deploys on push

### Option D: Render.com

1. Create Web Service for API
2. Create Static Site for Frontend
3. Create PostgreSQL database
4. Add Redis instance

---

## SSL/HTTPS Setup with Let's Encrypt

### Update nginx.conf for SSL
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # ... rest of config
}
```

### Mount certificates in docker-compose
```yaml
frontend:
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro
```

---

## Monitoring & Maintenance

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f api
```

### Restart Services
```bash
docker-compose -f docker-compose.prod.yml restart api
```

### Update Deployment
```bash
git pull origin main
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Backup Database
```bash
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres intelligent_dictionary > backup.sql
```

### Restore Database
```bash
cat backup.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres intelligent_dictionary
```

---

## Troubleshooting

### Container not starting
```bash
docker-compose -f docker-compose.prod.yml logs api
```

### Database connection issues
```bash
docker-compose -f docker-compose.prod.yml exec api python -c "from app.core.database import engine; print(engine.connect())"
```

### Frontend not loading
```bash
# Check nginx logs
docker-compose -f docker-compose.prod.yml logs frontend

# Check if API is accessible
docker-compose -f docker-compose.prod.yml exec frontend curl http://api:8000/health
```

---

## Architecture in Production

```
                    ┌─────────────────────────────────────┐
                    │           Load Balancer             │
                    │         (Optional: AWS ALB)         │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Docker Host (EC2/Droplet)                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     Frontend (Nginx) :80/:443                      │ │
│  │                    Serves React SPA + Proxies /api                 │ │
│  └───────────────────────────────┬────────────────────────────────────┘ │
│                                  │                                      │
│                                  ▼                                      │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      API (FastAPI) :8000                           │ │
│  │              Handles /chat, /auth, /health endpoints               │ │
│  └───────────────────────────────┬────────────────────────────────────┘ │
│                                  │                                      │
│              ┌───────────────────┼───────────────────┐                  │
│              ▼                   ▼                   ▼                  │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐        │
│  │   PostgreSQL     │ │      Redis       │ │  Celery Worker   │        │
│  │   + pgvector     │ │   (task queue)   │ │  (background)    │        │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
```
