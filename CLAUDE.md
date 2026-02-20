# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ShareMyShows is a social concert documentation platform (like Last.fm + Instagram for live music). Users can document shows, upload media, connect with friends, and discover concerts.

**Tech Stack:**
- **Backend:** Flask 3.0 + Flask-RESTX (Swagger) + SQLAlchemy + Flask-SocketIO + JWT auth
- **Frontend:** Next.js 14 + React 18 + TypeScript + Tailwind CSS (not yet implemented)
- **Database:** SQLite (dev) → PostgreSQL (production planned)
- **External APIs:** Google Places API, Setlist.fm API
- **Real-time:** Flask-SocketIO with eventlet

**Current Status:**
- Backend: 95% complete, production-ready with 67 documented API endpoints
- Frontend: 0% complete, directory exists but empty

## Development Commands

### Backend Setup & Running

```bash
# Initial setup
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and email credentials

# Initialize database (if needed)
python -c "from app import create_app; from app.models import db; app = create_app(); app.app_context().push(); db.create_all()"

# Run development server
python run.py
# Server: http://localhost:5000
# Swagger UI: http://localhost:5000/api/docs
```

### Database Operations

```bash
# View all users
sqlite3 instance/sharemyshows.db "SELECT id, username, email, mfa_enabled FROM users;"

# Clear test data
sqlite3 instance/sharemyshows.db "DELETE FROM users WHERE email LIKE '%test%';"

# Apply migrations
flask db upgrade

# Create new migration
flask db migrate -m "description"
```

### Frontend (When Implemented)

```bash
cd frontend
npm install
npm run dev  # http://localhost:3000
npm run build
npm run lint
```

## Architecture & Key Concepts

### Application Factory Pattern

The backend uses Flask's application factory (`backend/app/__init__.py:create_app()`). This:
- Initializes all extensions (SQLAlchemy, JWT, SocketIO, CORS, Flask-RESTX)
- Registers API namespaces dynamically with try/except fallbacks
- Exports `socketio` for use in `run.py`
- Configures Swagger UI at `/api/docs`

**Critical:** Always use `socketio.run(app)` in `run.py`, NOT `app.run()` for WebSocket support.

### Eventlet for Async I/O

The server uses eventlet for async networking. This requires:
- `eventlet.monkey_patch()` at the top of `run.py`
- Socket timeout handling for DNS lookups (see MFA email sending)
- `async_mode='eventlet'` in SocketIO initialization

### API Documentation Pattern

All routes use Flask-RESTX for automatic Swagger documentation:
- Route files: `backend/app/routes/*_swagger.py`
- Each file creates a namespace with `api = Namespace('name', description='...')`
- Models defined with `api.model()` for request/response documentation
- Decorators: `@api.doc()`, `@api.expect()`, `@api.response()`, `@api.marshal_with()`
- JWT auth: Use `@jwt_required()` decorator + document with `@api.doc(security='jwt')`

### Database Models

13 models in `backend/app/models/__init__.py`:
- `User` - Authentication with MFA fields (mfa_code, mfa_code_expires)
- `Show` - Concert records with venue/artist data
- `Artist`, `Venue` - Cached external API data
- `Photo`, `AudioRecording`, `VideoRecording` - Media files
- `Comment`, `Friendship`, `ChatMessage`, `ShowCheckin` - Social features
- `SetlistSong` - Setlist tracking

**Key relationships:**
- User → Shows, Photos, Audio, Video, Comments (one-to-many, cascade delete)
- Show → Photos, Audio, Video, Comments, SetlistSongs (one-to-many, cascade delete)
- Friendship → User bidirectional with status (pending/accepted/rejected)

### Multi-Factor Authentication (MFA)

Email-based MFA is fully implemented:
- 6-digit codes sent via Gmail SMTP
- Codes expire in 10 minutes (stored in `mfa_code_expires`)
- Single-use codes (cleared after verification)
- HTML email templates with click-to-verify buttons
- Flows: registration, login, enable from profile, disable from profile

**Email sending requires:**
- Gmail app password (not regular password) in `MAIL_PASSWORD`
- Socket timeout set to 30s to avoid DNS lookup failures with eventlet
- NO leading spaces in .env variables (Flask-Mail bug)

### File Uploads

Media files stored in `backend/uploads/{photos,audio,videos}/`:
- Upload handling via werkzeug `secure_filename()`
- Metadata stored in database (file_path, file_size, mime_type, dimensions, duration)
- File serving via `send_from_directory()`
- Video streaming endpoint at `/api/videos/stream/{id}`

### WebSocket Events

Real-time features via Flask-SocketIO (`backend/app/socket_events.py`):
- Connection management with session storage
- Events: join_show, leave_show, send_message, typing, user_online, user_offline
- Authentication via JWT in socket connection
- Room-based messaging for show-specific chats

### External API Integration

Two external APIs integrated (`backend/app/routes/external_apis_swagger.py`):

**Google Places API:**
- Venue search, autocomplete, details
- Requires `GOOGLE_PLACES_API_KEY` in .env
- Uses `googlemaps` Python client

**Setlist.fm API:**
- Artist search, setlists, concert data
- Requires `SETLISTFM_API_KEY` in .env
- Uses `requests` library with custom headers

## Configuration Management

Environment variables in `backend/.env` (see `.env.example`):
- `FLASK_ENV`, `SECRET_KEY`, `JWT_SECRET_KEY`
- `DATABASE_URL` - SQLite for dev, PostgreSQL for prod
- `CORS_ORIGINS` - Comma-separated list
- `GOOGLE_PLACES_API_KEY`, `SETLISTFM_API_KEY`
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD` - Gmail SMTP
- `FRONTEND_URL` - For email verification links

Config classes in `backend/config/config.py`:
- `DevelopmentConfig` - DEBUG=True, SQLite
- `ProductionConfig` - DEBUG=False, JWT_COOKIE_SECURE=True
- `TestingConfig` - In-memory SQLite

## Common Workflows

### Adding a New API Endpoint

1. Create or edit a `*_swagger.py` file in `backend/app/routes/`
2. Define request/response models with `api.model()`
3. Create endpoint with `@api.route()`, `@api.doc()`, `@api.expect()`, `@api.marshal_with()`
4. Add JWT protection with `@jwt_required()` if needed
5. Ensure namespace is imported in `backend/app/__init__.py`
6. Test in Swagger UI at `http://localhost:5000/api/docs`

### Adding a Database Field

1. Add column to model in `backend/app/models/__init__.py`
2. Create migration: `flask db migrate -m "description"`
3. Review generated migration in `backend/migrations/versions/`
4. Apply migration: `flask db upgrade`
5. Update API models/serialization if needed

### Testing MFA Flow

1. Start server: `python run.py`
2. Use Swagger UI or script: `python backend/scripts/test_mfa.py`
3. Check your email for 6-digit code
4. Verify code via `/api/auth/verify-mfa`
5. Check database: `sqlite3 instance/sharemyshows.db "SELECT mfa_enabled, mfa_code FROM users WHERE email='your@email.com';"`

### Debugging Email Issues

```bash
# Test email configuration
python backend/scripts/test_direct_email.py

# Check .env file (no leading spaces!)
cat backend/.env | grep MAIL

# Verify Flask-Mail config loading
python -c "from app import create_app; app = create_app(); print(app.config.get('MAIL_USERNAME'))"
```

### Adding WebSocket Event

1. Add handler in `backend/app/socket_events.py`
2. Use `@socketio.on('event_name')` decorator
3. Access user via `current_user` (if authenticated)
4. Emit responses with `emit('event_name', data)` or `emit(..., room=room_id)`
5. Test in browser console with `socket.io-client`

## Important Constraints

### Flask-RESTX Namespace Registration

`backend/app/__init__.py` uses try/except blocks to register namespaces. This allows:
- Graceful fallback to blueprint versions if swagger files don't exist
- Incremental migration from blueprints to swagger
- Don't remove the try/except pattern when all swagger files exist

### Eventlet Compatibility

- Always use `eventlet.monkey_patch()` before imports in `run.py`
- Increase socket timeout to 30s for SMTP operations
- Use `socketio.run()` not `app.run()`
- Async mode must be `'eventlet'`

### JWT Token Location

JWT tokens supported in both headers and cookies:
- Headers: `Authorization: Bearer <token>`
- Cookies: `access_token_cookie` (set by backend)
- Frontend should handle both methods

### File Path Security

- Always use `werkzeug.utils.secure_filename()` for uploads
- Store files outside the web root (`backend/uploads/`)
- Serve via `send_from_directory()` not static files
- Validate file types and sizes before saving

### CORS Configuration

CORS origins from .env (`CORS_ORIGINS=http://localhost:3000,http://localhost:5173`):
- Supports credentials (cookies)
- Allows Content-Type and Authorization headers
- Applied to both Flask and SocketIO

## Production Deployment Considerations

- Migrate to PostgreSQL (update `DATABASE_URL`)
- Set `JWT_COOKIE_SECURE=True` (HTTPS only)
- Use strong `SECRET_KEY` and `JWT_SECRET_KEY`
- Configure proper email provider (not Gmail)
- Set up file storage (S3, CloudFlare R2, etc.)
- Use production WSGI server (gunicorn with eventlet worker)
- Configure nginx reverse proxy
- Enable SSL/TLS certificates
- Set up monitoring and logging
- Implement rate limiting
- Add database backups

## Documentation Files

- `COMPLETE_PROJECT_SUMMARY.md` - Comprehensive project overview (1,415 lines)
- `backend/README.md` - Basic API reference
- `backend/INSTALLATION_GUIDE.md` - Setup instructions
- `backend/EXTERNAL_API_DOCUMENTATION.md` - Google Places & Setlist.fm guide
- `backend/WEBSOCKET_DOCUMENTATION.md` - WebSocket events guide

## API Endpoint Summary

**67 total endpoints across 10 namespaces:**
- `/api/auth` - 9 endpoints (register, login, verify-mfa, logout, profile/mfa, etc.)
- `/api/shows` - 11 endpoints (CRUD, search, checkin, attendees, upcoming/past)
- `/api/external` - 9 endpoints (venue search/autocomplete, artist search, setlists)
- `/api/photos` - 6 endpoints (upload, list, get, update, delete)
- `/api/audio` - 5 endpoints (upload, list, get, update, delete)
- `/api/videos` - 6 endpoints (upload, list, get, update, delete, stream)
- `/api/comments` - 4 endpoints (create, list, update, delete)
- `/api/friends` - 7 endpoints (request, accept, reject, remove, list, search)
- `/api/dashboard` - 7 endpoints (stats, counts, recent, top venues/artists, calendar)
- `/api/chat` - 3 endpoints (conversations, messages, send)

All documented at `http://localhost:5000/api/docs`
