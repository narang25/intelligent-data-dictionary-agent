#!/bin/bash
set -e

echo "========================================="
echo "  IDD EC2 Deployment Setup"
echo "========================================="

# Step 0: Add swap space (critical for t2.micro with 1GB RAM)
if [ ! -f /swapfile ]; then
    echo "💾 Creating 2GB swap file (essential for 1GB RAM instances)..."
    sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
    echo "✅ Swap enabled (2GB)"
else
    echo "✅ Swap already exists"
fi
free -h

# Step 1: Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    sudo yum update -y
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker ec2-user
    echo "✅ Docker installed. You may need to log out and back in for group changes."
fi

# Step 2: Install Docker Compose plugin if not present
if ! docker compose version &> /dev/null; then
    echo "📦 Installing Docker Compose plugin..."
    sudo mkdir -p /usr/local/lib/docker/cli-plugins
    sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
        -o /usr/local/lib/docker/cli-plugins/docker-compose
    sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    echo "✅ Docker Compose installed."
fi

echo ""
echo "Docker version: $(docker --version)"
echo "Compose version: $(docker compose version)"

# Step 3: Create app directory
mkdir -p ~/idd
cd ~/idd

echo ""
echo "✅ Setup complete! Now run:"
echo "   cd ~/idd"
echo "   # Create .env file (see instructions)"
echo "   # Copy docker-compose.deploy.yml"
echo "   # Then: ./deploy.sh"
