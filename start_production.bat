@echo off
REM Telegram AI Assistant - Production Startup Script for Windows
REM This script starts the bot in production mode with Docker Compose

echo 🚀 Starting Telegram AI Assistant in PRODUCTION mode...

REM Check if .env file exists
if not exist .env (
    echo ❌ Error: .env file not found!
    echo Please create .env file from env.example and configure your settings.
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker Compose not found!
    echo Please install Docker Compose and try again.
    pause
    exit /b 1
)

echo ✅ Environment check passed

REM Create necessary directories
if not exist data mkdir data
if not exist logs mkdir logs

echo 🐳 Starting services with Docker Compose...

REM Start all services
docker-compose up -d

REM Check if services started successfully
if errorlevel 1 (
    echo ❌ Failed to start services!
    echo Check the error messages above.
    pause
    exit /b 1
) else (
    echo ✅ Services started successfully!
    echo.
    echo 📊 Service Status:
    docker-compose ps
    echo.
    echo 📋 Useful commands:
    echo   View logs: docker-compose logs -f bot
    echo   Stop services: docker-compose down
    echo   Restart bot: docker-compose restart bot
    echo   View all logs: docker-compose logs
    echo.
    echo 🤖 Bot is now running in production mode!
    echo Check the logs above for any startup issues.
)

pause 