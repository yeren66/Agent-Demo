#!/bin/bash
# Development setup script

echo "🚀 Bug Fix Agent - Development Setup"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your GitCode token and other settings."
else
    echo "✅ .env file already exists"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start services
echo ""
echo "🔨 Building Docker images..."
docker-compose -f docker/docker-compose.yml build

echo ""
echo "🚀 Starting services..."
docker-compose -f docker/docker-compose.yml up -d gateway redis

echo ""
echo "✅ Services started!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env file with your GitCode token"
echo "   2. Run './scripts/ngrok.sh' to expose webhook endpoint"
echo "   3. Add webhook in your GitCode repository settings"
echo "   4. Test by commenting '@agent fix' in an issue"
echo ""
echo "🔗 Service URLs:"
echo "   Gateway: http://localhost:8080"
echo "   Health:  http://localhost:8080/"
echo "   Redis:   localhost:6379"
echo ""
echo "📊 To view logs:"
echo "   docker-compose -f docker/docker-compose.yml logs -f gateway"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose -f docker/docker-compose.yml down"
