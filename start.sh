#!/bin/bash

# Polymarket Position Notifier - Docker Startup Script

echo "🚀 Starting Polymarket Position Notifier with Docker..."

# Check if Docker is running and accessible
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running or not accessible!"
    echo "💡 Try running: sudo systemctl start docker"
    echo "💡 Or add your user to docker group: sudo usermod -aG docker $USER"
    echo "💡 Then log out and log back in, or run: newgrp docker"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Please copy env.template to .env and fill in your configuration:"
    echo "   cp env.template .env"
    echo "   nano .env"
    exit 1
fi

# Check if uv.lock exists (for dependency consistency)
if [ ! -f uv.lock ]; then
    echo "⚠️  uv.lock not found. Running uv sync to generate it..."
    if command -v uv &> /dev/null; then
        uv sync
    else
        echo "⚠️  uv not found locally, will install in Docker container"
    fi
fi

# Create log directory if it doesn't exist
mkdir -p log

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🎯 Starting services..."
docker-compose up -d

echo "✅ Services started successfully!"
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "📋 Useful Commands:"
echo "  View logs:           sudo docker-compose logs -f notification-service"
echo "  Stop services:       sudo docker-compose down"
echo "  Restart service:     sudo docker-compose restart notification-service"
echo "  View all logs:       sudo docker-compose logs -f"
echo "  Shell into service:  sudo docker-compose exec notification-service bash"