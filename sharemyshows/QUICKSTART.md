# ShareMyShows - Quick Start Guide 🚀

Get ShareMyShows running on your WSL Ubuntu 22.04 in 5 minutes!

## Prerequisites Check

Before starting, make sure you have:

- ✅ Windows 11 with WSL Ubuntu 22.04
- ✅ Docker Desktop for Windows (with WSL integration enabled)
- ✅ Python 3.9+ installed in WSL

---

## Option 1: Automated Setup (Recommended)

Run the automated setup script:

```bash
cd /path/to/sharemyshows
./setup.sh
```

This script will:
1. Check all prerequisites
2. Create Python virtual environment
3. Install all dependencies
4. Start Docker containers (MySQL + Redis)
5. Initialize the database
6. Run tests to verify everything works

**That's it!** If successful, skip to "Testing the API" below.

---

## Option 2: Manual Setup

If you prefer to set up manually:

### 1. Start Docker Services

```bash
docker-compose up -d
```

Verify containers are running:
```bash
docker-compose ps
```

You should see:
- `sharemyshows-mysql` (healthy)
- `sharemyshows-redis` (healthy)

### 2. Set Up Python Environment

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and change these values:
# SECRET_KEY=<generate-random-key>
# JWT_SECRET_KEY=<generate-random-key>

# Generate random keys with Python:
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Initialize Database

```bash
# Initialize Flask-Migrate
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

### 5. Run the Server

```bash
flask run --host=0.0.0.0 --port=5000 --debug
```

**Or use the run script:**

```bash
cd ..
./run.sh
```

---

## Testing the API

### Health Check

```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "database": "healthy",
  "redis": "healthy",
  "environment": "development"
}
```

### Register a User

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "johndoe",
    "password": "SecurePass123!"
  }'
```

### Login

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

Save the `access_token` from the response!

### Create an Artist

```bash
# Replace YOUR_TOKEN with the access_token from login
curl -X POST http://localhost:5000/api/artists \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Taylor Swift"
  }'
```

### Create a Venue

```bash
curl -X POST http://localhost:5000/api/venues \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Madison Square Garden",
    "location": "4 Pennsylvania Plaza, New York, NY 10001",
    "city": "New York",
    "state": "NY",
    "country": "USA",
    "latitude": 40.7505,
    "longitude": -73.9934
  }'
```

### Create a Show

```bash
curl -X POST http://localhost:5000/api/shows \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "venue_id": 1,
    "show_date": "2024-12-31",
    "show_time": "20:00:00",
    "title": "New Years Eve Concert",
    "notes": "Amazing show!",
    "is_public": true,
    "artist_ids": [1]
  }'
```

### Get Your Shows

```bash
curl http://localhost:5000/api/shows/my-shows \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Stopping the Application

### Stop the Flask server:
Press `Ctrl+C` in the terminal

### Stop Docker containers:
```bash
docker-compose stop
```

### Stop and remove containers:
```bash
docker-compose down
```

### Stop and remove everything including data (⚠️ WARNING):
```bash
docker-compose down -v  # This deletes the database!
```

---

## Next Development Session

When you return to development:

```bash
# 1. Start Docker (if not running)
docker-compose up -d

# 2. Start Flask
./run.sh

# Or manually:
cd backend
source venv/bin/activate
flask run --debug
```

---

## Running Tests

```bash
cd backend
source venv/bin/activate
pytest -v
```

With coverage:
```bash
pytest --cov=app --cov-report=html tests/
# Open htmlcov/index.html in browser
```

---

## Troubleshooting

### Can't connect to MySQL?

```bash
# Check if MySQL is running
docker-compose ps

# View MySQL logs
docker-compose logs mysql

# Restart MySQL
docker-compose restart mysql
```

### Permission denied on scripts?

```bash
chmod +x setup.sh run.sh
```

### Port 3306 already in use?

```bash
# Stop system MySQL if installed
sudo service mysql stop

# Or change port in docker-compose.yml
```

### Flask can't find modules?

Make sure venv is activated:
```bash
source backend/venv/bin/activate
```

---

## What's Next?

Now that Phase 1 is running, you can:

1. ✅ Explore the API endpoints
2. ✅ Run the test suite
3. ✅ Start building the frontend (React/React Native)
4. ✅ Add more features from Phase 2:
   - Photo upload
   - Audio recording
   - Setlist management
   - Comments

---

## Project Structure Quick Reference

```
sharemyshows/
├── backend/
│   ├── app/
│   │   ├── models/      # Database models
│   │   ├── routes/      # API endpoints
│   │   ├── utils/       # Helper functions
│   │   └── __init__.py  # App factory
│   ├── tests/           # Test files
│   ├── config/          # Configuration
│   ├── app.py           # Entry point
│   └── requirements.txt # Dependencies
├── docker-compose.yml   # Docker services
├── setup.sh            # Automated setup
└── run.sh              # Start server
```

---

## Need Help?

- Check the main README.md for detailed documentation
- Review the architecture document
- Run tests to verify setup: `pytest -v`
- Check Docker logs: `docker-compose logs`

**Happy coding! 🎸🎤🎶**
