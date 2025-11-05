#!/bin/bash
# Geodraft Quick Start Script
# This script sets up Geodraft for development

set -e

echo "========================================="
echo "  Geodraft Quick Start"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created. Please review and update it if needed."
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Start Docker containers
echo "🚀 Starting Docker containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start (this may take a few minutes)..."
sleep 30

# Check if database is ready
echo "🔍 Checking database connection..."
until docker-compose exec -T db pg_isready -U postgres &> /dev/null; do
    echo "   Waiting for database..."
    sleep 5
done
echo "✓ Database is ready"
echo ""

# Run migrations
echo "📦 Running database migrations..."
docker-compose exec -T django python manage.py makemigrations versioned_editing
docker-compose exec -T django python manage.py migrate

echo ""
echo "📁 Collecting static files..."
docker-compose exec -T django python manage.py collectstatic --noinput

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "🎉 Geodraft is now running!"
echo ""
echo "Access the application at:"
echo "  • GeoNode:              http://localhost:8000"
echo "  • GeoServer:            http://localhost:8080/geoserver"
echo "  • API (Branches):       http://localhost:8000/versioned-editing/api/branches/"
echo "  • Admin Panel:          http://localhost:8000/admin/"
echo ""
echo "Next steps:"
echo "  1. Create a superuser:"
echo "     docker-compose exec django python manage.py createsuperuser"
echo ""
echo "  2. Log in to GeoNode and create groups"
echo "  3. Upload vector layers"
echo "  4. Start editing!"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f django"
echo ""
echo "To stop the services:"
echo "  docker-compose down"
echo ""
