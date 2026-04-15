#!/bin/bash
# RAKSHAK Startup Script
echo "🛡️  Starting RAKSHAK - Disaster Intelligence System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Install deps if needed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt -q
fi

# Start FastAPI in background
echo "🚀 Starting FastAPI backend on port 8000..."
python main.py &
FASTAPI_PID=$!
sleep 2

# Start Streamlit
echo "🌐 Starting Streamlit UI on port 8501..."
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Cleanup on exit
trap "kill $FASTAPI_PID 2>/dev/null" EXIT
