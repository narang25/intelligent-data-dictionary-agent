#!/bin/bash
set -e

echo "========================================="
echo "  IDD Deployment"
echo "========================================="

cd ~/idd

# Check .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Create it first:"
    echo ""
    echo 'cat > .env << EOF'
    echo 'DB_PASSWORD=your_secure_password_here'
    echo 'GROQ_API_KEY=your_groq_api_key'
    echo 'SECRET_KEY=your_secret_key_here'
    echo 'CORS_ORIGINS=http://YOUR_EC2_PUBLIC_IP'
    echo 'EOF'
    echo ""
    exit 1
fi

# Check docker-compose.deploy.yml exists
if [ ! -f docker-compose.deploy.yml ]; then
    echo "❌ docker-compose.deploy.yml not found!"
    exit 1
fi

echo "📥 Pulling images from Docker Hub..."
docker compose -f docker-compose.deploy.yml pull

echo ""
echo "🚀 Starting all services..."
docker compose -f docker-compose.deploy.yml up -d

echo ""
echo "⏳ Waiting for database to be ready..."
sleep 10

# Check if DB is up
for i in {1..30}; do
    if docker exec jarvis_db pg_isready -U postgres &> /dev/null; then
        echo "✅ Database is ready!"
        break
    fi
    echo "   Waiting for DB... ($i/30)"
    sleep 2
done

echo ""
echo "🔍 Checking service status..."
docker compose -f docker-compose.deploy.yml ps

echo ""
echo "========================================="
echo "  ✅ Services are running!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Run:  ./init-data.sh   (to load olist data & generate docs)"
echo "  2. Visit: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'YOUR_EC2_IP')"
echo ""
