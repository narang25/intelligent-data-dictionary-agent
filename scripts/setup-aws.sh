#!/bin/bash
# ================================================
# AWS EC2 Setup Script for Intelligent Data Dictionary
# Run this after SSHing into your EC2 instance
# ================================================

set -e

echo "🚀 Setting up Intelligent Data Dictionary on AWS..."

# ================================
# Step 1: Install Docker
# ================================
echo "📦 Installing Docker..."
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose plugin
sudo apt install docker-compose-plugin -y

# ================================
# Step 2: Install Git
# ================================
echo "📦 Installing Git..."
sudo apt install git -y

# ================================
# Step 3: Clone Repository
# ================================
echo "📥 Cloning repository..."
cd ~
git clone https://github.com/narang25/intelligent-data-dictionary-agent.git
cd intelligent-data-dictionary-agent

# ================================
# Step 4: Create .env File
# ================================
echo "📝 Creating environment file..."
echo "⚠️  Please edit .env with your actual values!"

cat > .env << 'EOF'
DATABASE_URL=postgresql://postgres:securepassword123@db:5432/intelligent_dictionary
DB_PASSWORD=securepassword123
REDIS_URL=redis://redis:6379/0
GROQ_API_KEY=REPLACE_WITH_YOUR_GROQ_API_KEY
SECRET_KEY=REPLACE_WITH_A_RANDOM_64_CHAR_STRING
CORS_ORIGINS=http://YOUR_EC2_PUBLIC_IP
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EOF

echo ""
echo "⚠️  IMPORTANT: Edit the .env file before proceeding!"
echo "   Run: nano .env"
echo ""
echo "   Replace:"
echo "   - GROQ_API_KEY with your actual Groq API key"
echo "   - SECRET_KEY with a random string"
echo "   - YOUR_EC2_PUBLIC_IP with your Elastic IP"
echo ""
echo "After editing .env, run: ./deploy.sh"
