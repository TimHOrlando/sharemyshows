#!/bin/bash

# ShareMyShows Setup Script
# Run this script to set up the development environment

set -e  # Exit on error

echo "=========================================="
echo "ShareMyShows Development Setup"
echo "=========================================="
echo ""

# Check if we're in WSL
if grep -qEi "(Microsoft|WSL)" /proc/version &> /dev/null ; then
    echo "✓ Running in WSL"
else
    echo "⚠ Not running in WSL. This script is optimized for WSL Ubuntu."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Docker
echo ""
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✓ Docker is installed"
    if docker ps &> /dev/null; then
        echo "✓ Docker is running"
    else
        echo "✗ Docker is not running. Please start Docker Desktop."
        exit 1
    fi
else
    echo "✗ Docker is not installed"
    echo "  Please install Docker Desktop for Windows with WSL2 integration"
    exit 1
fi

# Check Python
echo ""
echo "Checking Python..."
if command -v python3.11 &> /dev/null; then
    echo "✓ Python 3.11 is installed"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo "✓ Python $PYTHON_VERSION is installed"
    if (( $(echo "$PYTHON_VERSION < 3.9" | bc -l) )); then
        echo "⚠ Python 3.9+ is recommended"
    fi
else
    echo "✗ Python 3 is not installed"
    echo "  Run: sudo apt install python3.11 python3.11-venv python3-pip"
    exit 1
fi

# Navigate to backend directory
cd backend

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt --quiet
echo "✓ Dependencies installed"

# Create .env if it doesn't exist
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    
    # Generate random secret keys
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Replace placeholders in .env
    sed -i "s/change-this-to-a-random-secret-key-in-production/$SECRET_KEY/" .env
    sed -i "s/change-this-to-a-random-jwt-secret-in-production/$JWT_SECRET_KEY/" .env
    
    echo "✓ .env file created with random secrets"
else
    echo "✓ .env file already exists"
fi

# Start Docker containers
echo ""
echo "Starting Docker containers..."
cd ..
docker-compose up -d
echo "✓ Docker containers started"

# Wait for MySQL to be ready
echo ""
echo "Waiting for MySQL to be ready..."
sleep 10

# Check if containers are healthy
if docker-compose ps | grep -q "Up"; then
    echo "✓ Containers are running"
else
    echo "✗ Containers failed to start"
    docker-compose logs
    exit 1
fi

# Initialize database
echo ""
echo "Initializing database..."
cd backend
source venv/bin/activate

# Initialize Flask-Migrate if not already done
if [ ! -d "migrations" ]; then
    echo "Initializing Flask-Migrate..."
    flask db init
    echo "✓ Flask-Migrate initialized"
fi

# Create initial migration
echo "Creating database migration..."
flask db migrate -m "Initial migration"
echo "✓ Migration created"

# Apply migration
echo "Applying database migration..."
flask db upgrade
echo "✓ Database initialized"

# Run tests
echo ""
echo "Running tests..."
pytest -v
TEST_RESULT=$?

echo ""
echo "=========================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo "✓ Setup completed successfully!"
else
    echo "⚠ Setup completed but some tests failed"
fi
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. cd backend"
echo "2. source venv/bin/activate"
echo "3. flask run --debug"
echo ""
echo "Or run: ./run.sh"
echo ""
echo "View API at: http://localhost:5000/api/health"
echo "=========================================="
