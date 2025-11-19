# 🐳 Docker Setup Guide - WQAM Dashboard

Complete guide to build and run the Water Quality Monitoring Dashboard with ML integration using Docker.

## 📋 Prerequisites

- **Docker Desktop** installed and running
- **Docker Compose** (included with Docker Desktop)
- **4GB+ RAM** available
- **Ports available**: 8000, 5173, 5432, 6379, 9000, 9001

## 🚀 Quick Start (Recommended)

### Option 1: Automated Setup Script

**Windows (PowerShell):**
```powershell
.\setup.ps1
```

**Mac/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

#### Step 1: Create Environment Files

**Backend** (`backend/.env`):
```env
DATABASE_URL=postgresql://wqam:wqam_pass@postgres:5432/wqamdb
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_URL=http://localhost:5173
REDIS_URL=redis://redis:6379/0
```

**Frontend** (`frontend/.env`):
```env
VITE_API_URL=http://localhost:8000
```

#### Step 2: Build and Start

```bash
# Build all services
docker-compose build

# Start all services in background
docker-compose up -d

# Or start with logs visible
docker-compose up
```

#### Step 3: Create Admin User

```bash
# Using the script
docker-compose exec backend python create_admin.py

# Or with custom credentials
docker-compose exec backend python create_admin.py myadmin mypassword123
```

#### Step 4: Access Dashboard

- **Frontend Dashboard**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

**Default Login:**
- Username: `admin`
- Password: `admin123` (or what you set)

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│  PostgreSQL │
│  (Nginx)    │     │  (FastAPI)  │     │  Database   │
│  Port 5173  │     │  Port 8000  │     │  Port 5432  │
└─────────────┘     └─────────────┘     └─────────────┘
                            │
                            ├────▶ Redis (Port 6379)
                            │
                            ├────▶ MinIO (Ports 9000, 9001)
                            │
                            └────▶ ML Model (/ml directory)
```

## 📦 Services

### Backend Service
- **Technology**: FastAPI (Python 3.11)
- **Port**: 8000
- **Features**: 
  - REST API
  - ML model integration
  - Authentication
  - File upload/analysis
- **Health Check**: http://localhost:8000/api/health

### Frontend Service
- **Technology**: React + TypeScript + Vite
- **Port**: 5173
- **Served by**: Nginx
- **Build**: Multi-stage Docker build

### PostgreSQL Database
- **Version**: PostgreSQL 15
- **Port**: 5432
- **Database**: wqamdb
- **Credentials**: wqam/wqam_pass
- **Persistence**: Docker volume

### Redis
- **Purpose**: Background job queue (RQ)
- **Port**: 6379
- **Persistence**: In-memory (optional: add volume)

### MinIO (Object Storage)
- **Purpose**: File storage
- **API Port**: 9000
- **Console Port**: 9001
- **Credentials**: minioadmin/minioadmin

## 🔧 Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Stop Services
```bash
# Stop (keeps volumes)
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Rebuild After Code Changes
```bash
# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Rebuild all
docker-compose build --no-cache
docker-compose up -d
```

### Execute Commands in Containers
```bash
# Backend shell
docker-compose exec backend bash

# Run Python script
docker-compose exec backend python script.py

# Frontend shell
docker-compose exec frontend sh

# Database shell
docker-compose exec postgres psql -U wqam -d wqamdb
```

### Check Service Status
```bash
docker-compose ps
```

## 🧪 Testing the Setup

### 1. Health Check
```bash
curl http://localhost:8000/api/health
# Expected: {"status":"ok"}
```

### 2. ML Model Status
```bash
curl http://localhost:8000/api/ml/status
# Expected: {"model_available": true/false, "model_path": "..."}
```

### 3. API Documentation
Open http://localhost:8000/docs in browser

### 4. Test Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## 🐛 Troubleshooting

### Port Already in Use

**Windows:**
```powershell
netstat -ano | findstr :8000
```

**Mac/Linux:**
```bash
lsof -i :8000
```

**Solution**: Stop the conflicting service or change ports in `docker-compose.yml`

### Database Connection Errors

1. Wait 10-15 seconds after starting for database to initialize
2. Check PostgreSQL logs: `docker-compose logs postgres`
3. Verify `DATABASE_URL` in `backend/.env`
4. Try restarting: `docker-compose restart postgres backend`

### ML Model Not Found

**Symptoms**: ML predictions not working, `model_available: false`

**Solutions**:
1. Verify model exists: `ls ml/model/water_model.pkl`
2. Check volume mount: `docker-compose exec backend ls -la /ml/model/`
3. Check backend logs: `docker-compose logs backend | grep -i model`
4. **Note**: System works without ML, just without ML features

### Frontend Can't Connect to Backend

1. Check `VITE_API_URL` in `frontend/.env`
2. Verify backend is running: `docker-compose ps backend`
3. Check CORS settings in `backend/main.py`
4. Rebuild frontend: `docker-compose build frontend`

### Services Won't Start

1. Check Docker Desktop is running
2. Check available disk space: `docker system df`
3. Check logs: `docker-compose logs`
4. Try clean rebuild: `docker-compose down -v && docker-compose build --no-cache`

### Permission Errors (Linux/Mac)

```bash
# Fix ownership
sudo chown -R $USER:$USER .

# Or run with sudo (not recommended)
sudo docker-compose up
```

## 📊 Monitoring

### Check Resource Usage
```bash
docker stats
```

### View Container Details
```bash
docker-compose ps
docker inspect <container_name>
```

### Database Backup
```bash
# Backup
docker-compose exec postgres pg_dump -U wqam wqamdb > backup.sql

# Restore
docker-compose exec -T postgres psql -U wqam wqamdb < backup.sql
```

## 🔒 Production Considerations

Before deploying to production:

1. **Change Secrets**
   - Update `SECRET_KEY` in `backend/.env` (use strong random string)
   - Change database passwords
   - Update MinIO credentials

2. **Security**
   - Use HTTPS (reverse proxy: nginx/traefik)
   - Restrict CORS origins
   - Use environment-specific `.env` files
   - Enable database SSL

3. **Performance**
   - Add resource limits in `docker-compose.yml`
   - Configure database connection pooling
   - Enable Redis persistence if needed
   - Use production-grade Nginx config

4. **Monitoring**
   - Add health check endpoints
   - Set up logging aggregation
   - Monitor resource usage
   - Set up alerts

5. **Backups**
   - Automated database backups
   - Volume backups
   - ML model versioning

## 📝 Development Workflow

### Making Code Changes

**Backend:**
- Code is mounted as volume, changes are reflected
- Restart to apply: `docker-compose restart backend`
- Or rebuild: `docker-compose build backend && docker-compose up -d backend`

**Frontend:**
- Rebuild after changes: `docker-compose build frontend && docker-compose up -d frontend`
- Or run locally: `cd frontend && npm run dev`

### Adding Dependencies

**Backend:**
1. Add to `backend/requirements.txt`
2. Rebuild: `docker-compose build backend`

**Frontend:**
1. Add to `frontend/package.json`
2. Rebuild: `docker-compose build frontend`

## 🎯 Next Steps

1. **Upload Data**: Go to http://localhost:5173/uploads
2. **View ML Insights**: Check ML predictions panel
3. **Explore Reports**: See all generated reports
4. **Monitor Alerts**: View water quality alerts
5. **Customize**: Modify thresholds, add parameters

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

## 💡 Tips

- Use `docker-compose logs -f` to watch logs in real-time
- Keep `.env` files in `.gitignore` (already configured)
- Use Docker volumes for data persistence
- Regularly update base images for security
- Monitor disk usage: `docker system df`

## 🆘 Getting Help

If you encounter issues:
1. Check logs: `docker-compose logs`
2. Verify all services are running: `docker-compose ps`
3. Check environment variables
4. Review this troubleshooting section
5. Check GitHub issues (if applicable)

---

**Happy Monitoring! 🎉**

