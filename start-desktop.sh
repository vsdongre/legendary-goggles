#!/bin/bash

# Start the Electron desktop app
cd /app/frontend
echo "🖥️ Starting LAN E-Learning Desktop Application..."
echo "📡 Backend running at: ${REACT_APP_BACKEND_URL:-http://localhost:8001}"
echo "🚀 Launching desktop app..."

# Set environment variable to indicate this is the desktop version
export ELECTRON_IS_DEV=false

# Start Electron
yarn electron