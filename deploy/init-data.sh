#!/bin/bash
set -e

echo "========================================="
echo "  IDD Data Initialization"
echo "========================================="

cd ~/idd

# Step 1: Download Olist dataset CSVs into a local folder
echo "📥 Downloading Olist dataset..."
mkdir -p datasets/olist

OLIST_BASE="https://raw.githubusercontent.com/olist/work-at-olist-data/master"
FILES=(
    "olist_customers_dataset.csv"
    "olist_sellers_dataset.csv"
    "olist_products_dataset.csv"
    "olist_orders_dataset.csv"
    "olist_order_items_dataset.csv"
    "olist_order_payments_dataset.csv"
    "olist_order_reviews_dataset.csv"
    "olist_geolocation_dataset.csv"
)

# Try the official repo first, fall back to kaggle mirror
for file in "${FILES[@]}"; do
    if [ -f "datasets/olist/$file" ]; then
        echo "   ✅ $file already exists, skipping"
    else
        echo "   📦 Downloading $file..."
        curl -sL "${OLIST_BASE}/${file}" -o "datasets/olist/$file" 2>/dev/null || true
        
        # Check if download succeeded (file should be > 100 bytes)
        if [ ! -s "datasets/olist/$file" ] || [ $(wc -c < "datasets/olist/$file") -lt 100 ]; then
            echo "   ⚠️  Direct download failed for $file"
            echo "   ℹ️  You may need to download from Kaggle: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
            rm -f "datasets/olist/$file"
        fi
    fi
done

# Check if we got the files
CSV_COUNT=$(ls datasets/olist/*.csv 2>/dev/null | wc -l)
if [ "$CSV_COUNT" -lt 8 ]; then
    echo ""
    echo "⚠️  Only $CSV_COUNT/8 CSV files downloaded."
    echo "   Please download the Olist dataset manually from:"
    echo "   https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
    echo ""
    echo "   Place all CSV files in: ~/idd/datasets/olist/"
    echo "   Then re-run this script."
    echo ""
    read -p "Continue anyway? (y/N): " confirm
    if [ "$confirm" != "y" ]; then
        exit 1
    fi
fi

echo ""
echo "✅ Dataset files ready: $CSV_COUNT files"

# Step 2: Copy CSV files into the running API container
echo ""
echo "📋 Copying dataset into API container..."
docker exec jarvis_api mkdir -p /app/datasets/olist
docker cp datasets/olist/. jarvis_api:/app/datasets/olist/

echo "✅ Files copied to container"

# Step 3: Initialize DB tables
echo ""
echo "🗄️  Creating database tables..."
docker exec jarvis_api python -c "
from app.core.database import engine
from app.domain.models import Base
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
    conn.commit()
Base.metadata.create_all(bind=engine)
print('✅ Tables created')
"

# Step 4: Load Olist data
echo ""
echo "📦 Loading Olist data into PostgreSQL..."
docker exec jarvis_api python -m app.admin.load_olist

# Step 5: Run auto-documentation
echo ""
echo "📝 Generating AI documentation (this may take a few minutes)..."
docker exec jarvis_api python -m app.admin.run_auto_doc

echo ""
echo "========================================="
echo "  ✅ Data initialization complete!"
echo "========================================="
echo ""
echo "Your app is ready at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'YOUR_EC2_IP')"
echo ""
