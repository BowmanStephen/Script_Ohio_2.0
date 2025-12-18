#!/bin/bash
# Start Audit API Server for React Dashboard

echo "🚀 Starting Audit API Server..."

# Check if required dependencies are installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask dependencies..."
    pip install flask flask-cors
fi

# Change to project root
cd "$(dirname "$0")/.."

# Create logs directory if it doesn't exist
mkdir -p logs/audit_api

# Start the API server
echo "🔌 Starting API server on http://localhost:5001"
echo "📊 API endpoints will be available at:"
echo "   GET  http://localhost:5001/api/audit/health"
echo "   GET  http://localhost:5001/api/audit/summary"
echo "   GET  http://localhost:5001/api/audit/alerts"
echo "   GET  http://localhost:5001/api/audit/metrics"
echo "   GET  http://localhost:5001/api/audit/categories"
echo "   POST http://localhost:5001/api/audit/trigger"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Run the API server
python3 api_server/audit_api.py --host 0.0.0.0 --port 5001 \
    2>&1 | tee "logs/audit_api/api_server_$(date +%Y%m%d_%H%M%S).log"