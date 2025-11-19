# Quick Start with Docker

## 🚀 Fast Setup (5 minutes)

### Step 1: Create Environment Files

```bash
# Create backend .env file
cat > backend/.env << EOF
DATABASE_URL=postgresql://wqam:wqam_pass@postgres:5432/wqamdb
SECRET_KEY=change-this-secret-key-in-production-$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_URL=http://localhost:5173
REDIS_URL=redis://redis:6379/0
EOF

# Create frontend .env file
cat > frontend/.env << EOF
VITE_API_URL=http://localhost:8000
EOF
```

**Windows PowerShell:**
```powershell
# Backend
@"
DATABASE_URL=postgresql://wqam:wqam_pass@postgres:5432/wqamdb
SECRET_KEY=change-this-secret-key-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_URL=http://localhost:5173
REDIS_URL=redis://redis:6379/0
"@ | Out-File -FilePath backend\.env -Encoding utf8

# Frontend
@"
VITE_API_URL=http://localhost:8000
"@ | Out-File -FilePath frontend\.env -Encoding utf8
```

### Step 2: Build and Start

```bash
docker-compose up --build -d
```

### Step 3: Wait for Services (30 seconds)

```bash
# Check status
docker-compose ps

# Watch logs
docker-compose logs -f
```

### Step 4: Create Admin User

```bash
# Option 1: Use the register endpoint
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","role":"admin"}'

# Option 2: Or use Python script (if create_admin.py is updated)
docker-compose exec backend python create_admin.py
```

### Step 5: Access Dashboard

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

Login with:
- Username: `admin`
- Password: `admin123` (or what you set)

## 📋 Verify Everything Works

### Check Backend Health
```bash
curl http://localhost:8000/api/health
```

### Check ML Model Status
```bash
curl http://localhost:8000/api/ml/status
```

### Check Frontend
Open http://localhost:8000/docs in browser to see API documentation.

## 🛠️ Common Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart a service
docker-compose restart backend

# Stop everything
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Rebuild after code changes
docker-compose up --build -d
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000

# Mac/Linux
lsof -i :8000
```

Change ports in `docker-compose.yml` if needed.

### Database Not Ready
Wait 10-15 seconds after starting, then check:
```bash
docker-compose logs postgres
```

### ML Model Not Found
The system works without ML! Check logs:
```bash
docker-compose logs backend | grep -i "model"
```

### Frontend Can't Connect
1. Check `frontend/.env` has `VITE_API_URL=http://localhost:8000`
2. Rebuild frontend: `docker-compose build frontend`

## 📝 Next Steps

1. **Upload Data**: Go to Uploads page and upload a CSV/PDF
2. **View ML Insights**: Check the ML predictions panel
3. **Explore Reports**: See all generated reports
4. **Check Alerts**: View water quality alerts

## 🎯 Production Deployment

Before going to production:
1. Change `SECRET_KEY` in `backend/.env`
2. Use strong database passwords
3. Set up HTTPS (reverse proxy)
4. Configure proper CORS origins
5. Set up database backups

Enjoy your WQAM Dashboard! 🎉

