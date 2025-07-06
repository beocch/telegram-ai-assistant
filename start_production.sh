#!/bin/bash

# Telegram AI Assistant - Production Startup Script
# This script starts the bot in production mode with Docker Compose

echo "🚀 Starting Telegram AI Assistant in PRODUCTION mode..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file from env.example and configure your settings."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose not found!"
    echo "Please install Docker Compose and try again."
    exit 1
fi

echo "✅ Environment check passed"

# Create necessary directories
mkdir -p data logs

echo "🐳 Starting services with Docker Compose..."

# Start all services
docker-compose up -d

# Check if services started successfully
if [ $? -eq 0 ]; then
    echo "✅ Services started successfully!"
    echo ""
    echo "📊 Service Status:"
    docker-compose ps
    echo ""
    echo "📋 Useful commands:"
    echo "  View logs: docker-compose logs -f bot"
    echo "  Stop services: docker-compose down"
    echo "  Restart bot: docker-compose restart bot"
    echo "  View all logs: docker-compose logs"
    echo ""
    echo "🤖 Bot is now running in production mode!"
    echo "Check the logs above for any startup issues."
else
    echo "❌ Failed to start services!"
    echo "Check the error messages above."
    exit 1
fi 