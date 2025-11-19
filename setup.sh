#!/bin/bash
# Quick setup script for WQAM Dashboard

set -e

echo "🚀 Setting up WQAM Dashboard with Docker..."

# Create backend .env if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend/.env..."
    cat > backend/.env << EOF
DATABASE_URL=postgresql://wqam:wqam_pass@postgres:5432/wqamdb
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_URL=http://localhost:5173
REDIS_URL=redis://redis:6379/0
EOF
    echo "✅ Created backend/.env"
else
    echo "ℹ️  backend/.env already exists"
fi

# Create frontend .env if it doesn't exist
if [ ! -f frontend/.env ]; then
    echo "📝 Creating frontend/.env..."
    cat > frontend/.env << EOF
VITE_API_URL=http://localhost:8000
EOF
    echo "✅ Created frontend/.env"
else
    echo "ℹ️  frontend/.env already exists"
fi

# Check if ML model exists
if [ -f "ml/model/water_model.pkl" ]; then
    echo "✅ ML model found at ml/model/water_model.pkl"
else
    echo "⚠️  ML model not found at ml/model/water_model.pkl"
    echo "   The system will work but ML features will be disabled"
fi

echo ""
echo "🔨 Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "👤 Creating admin user..."
docker-compose exec -T backend python create_admin.py admin admin123 || echo "⚠️  Could not create admin user automatically"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Access the dashboard:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "🔑 Login credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📋 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop: docker-compose down"
echo "   Restart: docker-compose restart"

