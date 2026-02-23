#!/bin/bash

# ShareMyShows - Start Development Server
# This script starts the Flask development server

set -e

echo "=========================================="
echo "ShareMyShows - Starting Development Server"
echo "=========================================="

# Check if Docker containers are running
if ! docker ps | grep -q "sharemyshows-mysql"; then
    echo ""
    echo "Starting Docker containers..."
    docker-compose up -d
    echo "Waiting for MySQL to be ready..."
    sleep 5
fi

# Navigate to backend and activate venv
cd backend

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

source venv/bin/activate

echo ""
echo "Starting Flask development server..."
echo "API will be available at: http://localhost:5000"
echo "Health check: http://localhost:5000/api/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Start Flask with hot reload
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000 --debug
