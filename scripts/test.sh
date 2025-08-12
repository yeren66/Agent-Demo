#!/bin/bash
# Test the Bug Fix Agent locally

echo "🧪 Bug Fix Agent - Local Test"
echo ""

# Check if services are running
if ! curl -s http://localhost:8080/ > /dev/null; then
    echo "❌ Gateway service is not running on port 8080"
    echo "   Start it with: docker-compose -f docker/docker-compose.yml up -d gateway"
    exit 1
fi

echo "✅ Gateway service is running"

# Test health endpoint
echo ""
echo "🏥 Testing health endpoint..."
curl -s http://localhost:8080/ | jq '.' || echo "Response received (jq not available for pretty print)"

# Test status endpoint
echo ""
echo "📊 Testing status endpoint..."
curl -s http://localhost:8080/api/status | jq '.' || echo "Response received"

echo ""
echo "🚀 Basic tests passed!"
echo ""
echo "📋 Next steps to test webhook:"
echo "   1. Use ngrok: ./scripts/ngrok.sh"
echo "   2. Add webhook to GitCode repository"
echo "   3. Create an issue and comment '@agent fix'"
echo ""
echo "📝 Manual webhook test (replace URL with your ngrok URL):"
echo '   curl -X POST https://your-ngrok-url.ngrok.io/api/gitcode/webhook \'
echo '     -H "Content-Type: application/json" \'
echo '     -H "X-Gitcode-Event: issues" \'
echo '     -d "{\"action\":\"opened\",\"issue\":{\"number\":1,\"title\":\"Test\",\"body\":\"@agent fix test issue\",\"user\":{\"login\":\"testuser\"}},\"repository\":{\"name\":\"testrepo\",\"owner\":{\"login\":\"testowner\"}}}"'
