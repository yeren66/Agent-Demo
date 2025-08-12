#!/bin/bash
# Start ngrok to expose local development server

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed. Please install it first:"
    echo "   brew install ngrok  # macOS"
    echo "   or download from https://ngrok.com/"
    exit 1
fi

# Check if port 8080 is in use
if lsof -i :8080 > /dev/null; then
    echo "✅ Service detected on port 8080"
else
    echo "⚠️  No service detected on port 8080. Make sure to start the gateway first:"
    echo "   docker-compose -f docker/docker-compose.yml up gateway"
    echo ""
    echo "Starting ngrok anyway..."
fi

echo "🚀 Starting ngrok tunnel for port 8080..."
echo ""
echo "📋 Once ngrok starts:"
echo "   1. Copy the HTTPS forwarding URL (e.g., https://abc123.ngrok-free.app)"
echo "   2. Configure GitHub App Webhook:"
echo "      - Go to: https://github.com/settings/apps/mooctestagent"
echo "      - Update Webhook URL: https://your-url.ngrok-free.app/api/webhook"
echo "      - Events: Issues, Issue comments"
echo "      - Secret: use WEBHOOK_SECRET from your .env file"
echo "   3. Test in an Issue: @mooctestagent fix this bug"
echo ""
echo "🛑 Press Ctrl+C to stop ngrok"
echo ""

# Start ngrok
ngrok http 8080
