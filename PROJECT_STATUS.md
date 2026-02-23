# ShareMyShows - Project Status

**Last Updated:** February 22, 2026

---

## Completed Features

### Backend (Flask 3.0 + Flask-RESTX)

**Authentication & User Management**
- User registration with email/username/password
- Login with JWT tokens (header + cookie support)
- Email-based MFA (6-digit codes, 10-min expiry, HTML templates)
- Password reset flow (request, email link, reset)
- Temporary password system for in-app password changes
- Profile management with theme preference persistence
- 7 themes: forest, sage, dark, light, midnight, concert, purple

**Show/Concert Management**
- Full CRUD for show records (artist, venue, date, notes, rating)
- Show feed from accepted friends (paginated)
- Search/filter by artist, venue, year, past/upcoming
- Show check-in/check-out with presence tracking

**Setlist System**
- Manual song add/edit/delete with ordering
- Auto-populate from Setlist.fm API (primary source)
- Concert Archives HTML scraper as fallback source
- MusicBrainz backfill for duration and songwriter metadata
- Song metadata: duration, songwriter, is_cover, original_artist, with_artist
- Bulk song add support
- Fire-and-forget background processing from frontend

**Media Management**
- Photo upload with PIL thumbnail generation (300x300)
- Audio recording upload with metadata
- Video upload (mp4, mov, avi, mkv, webm, flv) with streaming endpoint
- Secure file serving via `send_from_directory()`
- Photos search and sort state management

**Social Features**
- Friend requests (send, accept, reject, remove)
- User search by username/email
- Comments on shows and photos (authorization: owner or accepted friend)
- Real-time chat per show via WebSocket (persisted to DB, last 50 on join)
- Typing indicators

**Find My Friends (Location Sharing)**
- Live GPS sharing at shows via WebSocket (`update_location` / `stop_location`)
- Privacy: broadcasts only to accepted friends (per-SID targeted emits)
- Location persisted to `ShowCheckin` model, cleared on stop/disconnect
- REST fallback for initial friend location fetch
- Disconnect cleanup (clear location, notify friends)

**Dashboard & Analytics**
- Stats: total shows, artists, venues, media counts (2-min cache)
- Top artists by show count with Wikipedia descriptions (MusicBrainz background backfill)
- Top venues by show count (no hard limit)
- Recent photos, audio, videos, comments

**External API Integration**
- Google Places: venue search, autocomplete, details, photos
- Setlist.fm: artist search, artist details, setlists by date
- Concert Archives: HTML scraping for setlist fallback
- MusicBrainz: song duration + songwriter lookup

**Infrastructure**
- 67+ documented API endpoints across 10 namespaces
- Full Swagger UI at `/api/docs`
- Flask-SocketIO with eventlet async mode
- SQLite (dev) with Flask-Migrate for schema management
- Application factory pattern with graceful namespace registration

### Frontend (Next.js 14 + React 18 + TypeScript + Tailwind)

**Pages (All Implemented)**
- `/` - Landing page with dashboard redirect
- `/login` - Login with password visibility toggle, MFA flow
- `/register` - Registration with optional MFA
- `/verify-mfa` - 6-digit code entry with resend
- `/forgot-password` - Password reset request
- `/reset-password` - New password with token
- `/dashboard` - Stats cards, recent activity, quick actions
- `/shows` - Show list with filters, AddShowModal
- `/shows/[id]` - Show detail with tabs: setlist, photos, videos, comments, Friends Here (today only)
- `/feed` - Friends' shows paginated feed
- `/photos` - Photo gallery by show date with search/sort
- `/videos` - Video library with streaming
- `/comments` - All comments across shows
- `/artists` - Top artists by show count
- `/venues` - Top venues by show count
- `/friends` - Friends list, pending requests, user search

**Components**
- `Navbar` - Top navigation with auth state and user menu
- `AddShowModal` - Multi-step: venue search (Google Places) -> artist search (Setlist.fm) -> date/notes/rating
- `ProtectedRoute` - Auth guard with login redirect
- `ThemeSwitcher` - 7-theme selector using CSS variables
- `SettingsModal` - Theme, MFA toggle, password change, logout
- `FriendMapModal` - Google Maps with friend markers, walking directions, InfoWindow
- `PasswordRequirements` - Real-time password strength indicator

**Real-time Features**
- WebSocket connection per show (chat, presence, typing indicators)
- Continuous GPS tracking with `watchPosition` + 20s emit interval
- Friends Here tab (today's shows only, accepted friends only)
- View Friends on Map with Google Maps integration
- Walking directions to selected friend (Google Directions API)

**Theming**
- CSS variable-based system (bg-primary, text-accent, etc.)
- All pages converted from hardcoded purple to theme-aware classes
- 7 themes persisted to backend user preference

### Deployment & Packaging

- Docker Compose with MySQL 8.0 + Redis 7
- Celery worker/beat skeleton (commented, ready to activate)
- `.env.example` with all required variables documented
- Postman collection for API testing
- Project documentation suite (CLAUDE.md, README, installation guide, API docs, WebSocket docs)

---

## In Progress

*No features currently in active development.*

---

## Planned / Not Yet Implemented

**Frontend Polish**
- Loading states and skeleton screens
- Error boundary components
- Form validation improvements
- Responsive design refinements
- Animations and transitions
- Accessibility audit

**Media Enhancements**
- Video duration extraction (ffmpeg integration)
- Audio waveform visualization
- Media lightbox/gallery viewer
- Cloud file storage (S3, CloudFlare R2)

**Social Expansion**
- Push notifications / in-app notification center
- SMS MFA (Twilio integration - currently stubbed)
- User profile pages (view other users' public shows)
- Activity feed with friend actions

**Production Readiness**
- PostgreSQL migration (production database)
- CI/CD pipeline
- Rate limiting on API endpoints
- Structured logging and monitoring
- SSL/TLS configuration
- Nginx reverse proxy setup
- Database backup strategy
- Production WSGI server (gunicorn + eventlet worker)

**Potential Features**
- Ticketmaster integration for upcoming show discovery
- Spotify integration for artist data
- Show statistics and year-in-review
- Export/share show history
- QR code check-in at venues

---

## Technical Reference

**Running the Project**
```bash
# Backend
cd backend && source venv/bin/activate && python run.py
# http://localhost:5000 | Swagger: http://localhost:5000/api/docs

# Frontend
cd frontend && npm run dev
# http://localhost:3000
```

**Key Environment Variables**
- Backend: `FLASK_ENV`, `SECRET_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL`, `GOOGLE_PLACES_API_KEY`, `SETLISTFM_API_KEY`, `MAIL_*`
- Frontend: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`

**Database:** SQLite (dev) at `backend/instance/sharemyshows.db` | 13 models

---

*This document is updated at the end of each development session.*
