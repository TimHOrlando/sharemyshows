# ShareMyShows (SMS) 🎸🎤

A social concert documentation platform for capturing, sharing, and reliving live music experiences.

## Tech Stack

- **Backend**: Flask 3.x + SQLAlchemy 2.x + Flask-JWT-Extended
- **Database**: MySQL 8.x + Redis
- **API**: RESTful with JWT authentication
- **Container**: Docker + Docker Compose

---

## Prerequisites for Windows 11 WSL (Ubuntu 22.04)

### 1. Update WSL Ubuntu
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Docker Desktop for Windows
1. Download Docker Desktop from https://www.docker.com/products/docker-desktop/
2. Install and enable WSL 2 integration
3. Open Docker Desktop → Settings → Resources → WSL Integration
4. Enable integration with Ubuntu 22.04
5. Click "Apply & Restart"

### 3. Verify Docker in WSL
```bash
docker --version
docker-compose --version
```

### 4. Install Python 3.11+ (if not already installed)
```bash
sudo apt install python3.11 python3.11-venv python3-pip -y
```

### 5. Install Git (if not already installed)
```bash
sudo apt install git -y
```

---

## Project Setup - Step by Step

### Step 1: Clone/Navigate to Project Directory
```bash
# If you have this in a git repo, clone it
# Otherwise, navigate to where you extracted the project
cd /path/to/sharemyshows
```

### Step 2: Create Python Virtual Environment
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate  # You should see (venv) in your prompt
```

### Step 3: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables
```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your preferred editor (nano, vim, or code)
nano .env

# The defaults should work for local development
# Just make sure to set a strong SECRET_KEY and JWT_SECRET_KEY
```

### Step 5: Start Docker Services
```bash
# Make sure you're in the project root directory
cd ..

# Start MySQL and Redis using Docker Compose
docker-compose up -d

# Verify containers are running
docker-compose ps

# You should see:
# - sharemyshows-mysql (port 3306)
# - sharemyshows-redis (port 6379)
```

### Step 6: Initialize the Database
```bash
cd backend
source venv/bin/activate  # If not already activated

# Run database migrations
flask db upgrade

# Or if that doesn't work:
python -m flask db upgrade
```

### Step 7: Run the Development Server
```bash
# Still in backend directory with venv activated
flask run --host=0.0.0.0 --port=5000 --debug

# Or use:
python app.py
```

### Step 8: Test the API
Open another WSL terminal and test:

```bash
# Health check
curl http://localhost:5000/api/health

# Register a new user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123!"
  }'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

---

## Common WSL Issues & Solutions

### Docker Not Found in WSL
**Problem**: `docker: command not found`
**Solution**: 
1. Make sure Docker Desktop is running on Windows
2. In Docker Desktop → Settings → Resources → WSL Integration
3. Enable your Ubuntu distribution
4. Restart WSL: `wsl --shutdown` (run in PowerShell), then reopen Ubuntu

### Port Already in Use
**Problem**: `Port 3306 is already allocated`
**Solution**:
```bash
# Stop the conflicting service
docker-compose down

# Or stop system MySQL if installed
sudo service mysql stop
```

### Permission Denied Errors
**Problem**: Permission errors when running docker commands
**Solution**:
```bash
# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker
```

### Can't Connect to MySQL from Host
**Problem**: Can't access MySQL from Windows tools (MySQL Workbench, etc.)
**Solution**: MySQL is running in WSL's network. Use `localhost:3306` from WSL, or:
1. Find WSL IP: `ip addr show eth0`
2. Use that IP from Windows (e.g., `172.x.x.x:3306`)

---

## Development Workflow

### Daily Development Routine
```bash
# 1. Start Docker services (if not already running)
docker-compose up -d

# 2. Activate virtual environment
cd backend
source venv/bin/activate

# 3. Run Flask dev server
flask run --debug

# 4. In another terminal, run tests
pytest tests/

# 5. When done for the day
docker-compose stop  # Stops containers but keeps data
# OR
docker-compose down  # Stops and removes containers (data persists in volumes)
```

### Database Management
```bash
# Access MySQL CLI
docker-compose exec mysql mysql -u sms_user -p
# Password: sms_password (from docker-compose.yml)

# View logs
docker-compose logs -f mysql
docker-compose logs -f redis

# Reset database (WARNING: deletes all data)
docker-compose down -v  # -v removes volumes
docker-compose up -d
flask db upgrade
```

### Code Quality Tools
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/

# Format code
black app/
isort app/

# Lint code
flake8 app/
pylint app/
```

---

## Project Structure

```
sharemyshows/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask app factory
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── show.py
│   │   │   ├── artist.py
│   │   │   └── venue.py
│   │   ├── routes/              # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── shows.py
│   │   │   ├── artists.py
│   │   │   └── venues.py
│   │   ├── schemas/             # Pydantic/Marshmallow schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   └── show.py
│   │   └── utils/               # Helper functions
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       └── validators.py
│   ├── migrations/              # Alembic migrations
│   ├── tests/                   # Test files
│   ├── config/
│   │   └── config.py           # Configuration classes
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example            # Example environment variables
│   ├── .env                    # Your local env (git-ignored)
│   └── app.py                  # Application entry point
├── docker-compose.yml          # Docker services
├── .gitignore
└── README.md                   # This file
```

---

## API Documentation

Once the server is running, visit:
- http://localhost:5000/api/docs (coming in Phase 2)

### Available Endpoints (Phase 1)

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user (requires token)
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info (requires token)

#### Shows
- `GET /api/shows` - List all shows (with pagination)
- `POST /api/shows` - Create new show
- `GET /api/shows/{id}` - Get show details
- `PUT /api/shows/{id}` - Update show
- `DELETE /api/shows/{id}` - Delete show

#### Artists
- `GET /api/artists` - List all artists
- `POST /api/artists` - Create artist
- `GET /api/artists/{id}` - Get artist details

#### Venues
- `GET /api/venues` - List all venues
- `POST /api/venues` - Create venue
- `GET /api/venues/{id}` - Get venue details

---

## Environment Variables

Key variables in `.env`:

```bash
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-this
DEBUG=True

# Database
DATABASE_URL=mysql+pymysql://sms_user:sms_password@localhost:3306/sharemyshows

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret-change-this
JWT_ACCESS_TOKEN_EXPIRES=900    # 15 minutes
JWT_REFRESH_TOKEN_EXPIRES=604800  # 7 days

# Security
BCRYPT_LOG_ROUNDS=12
```

---

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html tests/
# Open htmlcov/index.html in browser
```

---

## Troubleshooting

### MySQL Connection Errors
```bash
# Check if MySQL is running
docker-compose ps

# Check MySQL logs
docker-compose logs mysql

# Restart MySQL
docker-compose restart mysql
```

### Redis Connection Errors
```bash
# Test Redis connection
redis-cli -h localhost -p 6379 ping
# Should return: PONG

# Or using docker
docker-compose exec redis redis-cli ping
```

### Flask Won't Start
```bash
# Make sure venv is activated
source venv/bin/activate

# Check if all dependencies are installed
pip install -r requirements.txt

# Check for syntax errors
python -m py_compile app.py
```

---

## Next Steps After Phase 1

- [ ] Phase 2: Photo/audio upload with S3
- [ ] Phase 2: Setlist management
- [ ] Phase 2: Comment system
- [ ] Phase 3: Theme system
- [ ] Phase 4: Social features (friends, followers)
- [ ] Phase 5: Real-time features (WebSocket, check-ins)

---

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and test: `pytest`
3. Commit: `git commit -m "Add feature"`
4. Push: `git push origin feature/your-feature`

---

## License

[Add your license here]

---

## Support

For issues or questions, contact [your-email@example.com]

---

**Happy coding! 🚀**
