#!/bin/bash
# ================================================
# Deploy Script - Run after setup-aws.sh
# ================================================

set -e

echo "🚀 Deploying Intelligent Data Dictionary..."

# Build and start all services
echo "🔨 Building containers..."
docker compose -f docker-compose.aws.yml build

echo "▶️  Starting services..."
docker compose -f docker-compose.aws.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 15

# Check if services are running
echo "📊 Service Status:"
docker compose -f docker-compose.aws.yml ps

# Initialize database
echo "🗄️  Initializing database..."
docker compose -f docker-compose.aws.yml exec api python -c "
from sqlalchemy import text
from app.core.database import engine
try:
    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        conn.commit()
    print('✅ pgvector extension enabled')
except Exception as e:
    print(f'⚠️  pgvector: {e}')
"

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "🌐 Access your app:"
echo "   Frontend: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "   API:      http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "   API Docs: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000/docs"
echo ""
echo "📝 Next Steps:"
echo "   1. Load sample data:"
echo "      docker compose -f docker-compose.aws.yml exec api python -c \"from app.admin.load_olist import run; run()\""
echo "   2. Generate documentation:"
echo "      docker compose -f docker-compose.aws.yml exec api python -c \"from app.admin.run_auto_doc import run; run()\""
echo "   3. Check logs:"
echo "      docker compose -f docker-compose.aws.yml logs -f api"
