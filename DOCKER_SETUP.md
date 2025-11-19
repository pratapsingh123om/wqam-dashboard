# Docker Setup Guide for WQAM Dashboard

This guide will help you build and run the complete WQAM Dashboard with ML integration using Docker.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose (usually included with Docker Desktop)
- At least 4GB of available RAM
- Ports 8000, 5173, 5432, 6379, 9000, 9001 available

## Quick Start

### 1. Clone/Prepare the Project

Ensure you have:
- The ML model at `ml/model/water_model.pkl` (if you want ML features)
- All project files in place

### 2. Create Environment Files

Create `.env` files from the examples:

```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env
```

**Important**: Edit `backend/.env` and change the `SECRET_KEY` to a secure random string for production!

### 3. Build and Start Services

```bash
# Build all images and start services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

### 4. Access the Dashboard

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

### 5. Create Admin User

Once services are running, create an admin user:

```bash
# Execute in backend container
docker-compose exec backend python create_admin.py

# Or if you need to set username/password
docker-compose exec backend python create_admin.py --username admin --password yourpassword
```

## Service Details

### Backend Service
- **Port**: 8000
- **Health Check**: http://localhost:8000/api/health
- **API Docs**: http://localhost:8000/docs
- **Includes**: FastAPI, ML model integration, PostgreSQL, Redis

### Frontend Service
- **Port**: 5173
- **Technology**: React + TypeScript + Vite
- **Served by**: Nginx

### PostgreSQL Database
- **Port**: 5432
- **Database**: wqamdb
- **User**: wqam
- **Password**: wqam_pass
- **Data Persistence**: Stored in Docker volume

### Redis
- **Port**: 6379
- **Used for**: Background job queue (RQ)

### MinIO (Object Storage)
- **API Port**: 9000
- **Console Port**: 9001
- **Credentials**: minioadmin/minioadmin
- **Used for**: File storage (optional)

## Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop Services
```bash
docker-compose down
```

### Stop and Remove Volumes (clean slate)
```bash
docker-compose down -v
```

### Rebuild Specific Service
```bash
docker-compose build backend
docker-compose up -d backend
```

### Execute Commands in Containers
```bash
# Backend shell
docker-compose exec backend bash

# Run Python script
docker-compose exec backend python script.py

# Frontend shell
docker-compose exec frontend sh
```

### Check Service Status
```bash
docker-compose ps
```

## Troubleshooting

### Port Already in Use
If you get port conflicts:
1. Check what's using the port: `netstat -ano | findstr :8000` (Windows) or `lsof -i :8000` (Mac/Linux)
2. Stop the conflicting service or change ports in `docker-compose.yml`

### ML Model Not Found
If ML predictions aren't working:
1. Verify model exists: `ls ml/model/water_model.pkl`
2. Check backend logs: `docker-compose logs backend`
3. The system will work without ML, just without ML features

### Database Connection Issues
1. Ensure PostgreSQL container is running: `docker-compose ps postgres`
2. Check database URL in `backend/.env`
3. Wait a few seconds after starting for database to initialize

### Frontend Can't Connect to Backend
1. Check `VITE_API_URL` in `frontend/.env`
2. Ensure backend is running: `docker-compose ps backend`
3. Check CORS settings in `backend/main.py`

### Rebuild Everything
```bash
# Stop and remove everything
docker-compose down -v

# Remove images
docker-compose rm -f

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

## Development Mode

For development with hot-reload:

### Backend (Python)
The backend code is mounted as a volume, so changes are reflected. However, you may need to restart:
```bash
docker-compose restart backend
```

### Frontend (React)
The frontend is built into a static site. For development:
1. Run frontend locally: `cd frontend && npm run dev`
2. Or rebuild after changes: `docker-compose build frontend && docker-compose up -d frontend`

## Production Considerations

Before deploying to production:

1. **Change Secrets**: Update `SECRET_KEY` in `backend/.env`
2. **Database Password**: Use strong PostgreSQL password
3. **CORS**: Update `FRONTEND_URL` to your production domain
4. **HTTPS**: Use reverse proxy (nginx/traefik) for HTTPS
5. **Backups**: Set up database backups
6. **Monitoring**: Add health checks and monitoring
7. **Resource Limits**: Add resource limits in `docker-compose.yml`

## ML Model Location

The ML model should be at:
- **Host**: `ml/model/water_model.pkl`
- **Container**: `/app/../ml/model/water_model.pkl`

The model is mounted as a read-only volume, so updates require container restart.

## First Login

After creating an admin user, you can:
1. Go to http://localhost:5173
2. Login with your admin credentials
3. Upload water quality data (CSV/PDF/Excel)
4. View ML predictions and insights

## Support

If you encounter issues:
1. Check logs: `docker-compose logs`
2. Verify all services are running: `docker-compose ps`
3. Check environment variables are set correctly
4. Ensure ML model file exists if using ML features

