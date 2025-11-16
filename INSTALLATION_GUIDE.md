# Backend Enhancement Files - Installation Guide

This package contains all the new files and modifications for the backend enhancements.

## 📦 What's Included

### New Files (Add to your repository)
1. `app/routes/external_apis.py` - Google Places & Setlist.fm integration
2. `app/socket_events.py` - WebSocket/Socket.IO event handlers
3. `EXTERNAL_API_DOCUMENTATION.md` - Complete external API guide
4. `WEBSOCKET_DOCUMENTATION.md` - Complete WebSocket guide
5. `BACKEND_ENHANCEMENTS_SUMMARY.md` - Session summary

### Modified Files (Replace in your repository)
1. `requirements.txt` - Added 5 new dependencies
2. `.env.example` - Added Google Places and Setlist.fm API keys
3. `app/__init__.py` - Registered external_api blueprint and SocketIO
4. `run.py` - Updated to use socketio.run()

## 🚀 Installation Steps

### 1. Update Your Repository

```bash
# Navigate to your project
cd /path/to/sharemyshows/backend

# Copy new route file
cp external_apis.py app/routes/

# Copy socket events file
cp socket_events.py app/

# Replace modified files
cp requirements.txt .
cp .env.example .
cp run.py .
cp app/__init__.py app/

# Copy documentation
cp EXTERNAL_API_DOCUMENTATION.md .
cp WEBSOCKET_DOCUMENTATION.md .
cp BACKEND_ENHANCEMENTS_SUMMARY.md .
```

### 2. Install New Dependencies

```bash
# Activate your virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install new packages
pip install -r requirements.txt

# Verify installation
pip list | grep -E "googlemaps|socketio|eventlet"
```

### 3. Configure API Keys

```bash
# Copy .env.example to .env if you haven't already
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Add these lines to your `.env`:
```bash
GOOGLE_PLACES_API_KEY=your-google-places-api-key
SETLISTFM_API_KEY=your-setlistfm-api-key
```

**Get API Keys:**
- **Google Places:** https://console.cloud.google.com/apis/credentials
  - Enable: Places API, Maps JavaScript API, Geocoding API
- **Setlist.fm:** https://www.setlist.fm/settings/apps

### 4. Test the Backend

```bash
# Start the server
python run.py

# You should see:
# * Running on http://0.0.0.0:5000
# * Eventlet started
```

### 5. Test API Endpoints

```bash
# Test health check
curl http://localhost:5000/api/external/health

# Test venue search (requires authentication)
# First, get your JWT token by logging in, then:
curl -X GET 'http://localhost:5000/api/external/venues/search?query=madison' \
  -H 'Cookie: access_token_cookie=YOUR_JWT_TOKEN'

# Test artist search
curl -X GET 'http://localhost:5000/api/external/artists/search?query=radiohead' \
  -H 'Cookie: access_token_cookie=YOUR_JWT_TOKEN'
```

### 6. Test WebSocket

Open browser console and run:
```javascript
const socket = io('http://localhost:5000', { withCredentials: true });

socket.on('connected', (data) => {
  console.log('Connected:', data);
  socket.emit('join_show', { show_id: 1 });
});

socket.on('message_history', (data) => {
  console.log('Message history:', data);
});

socket.emit('send_message', { show_id: 1, message: 'Test message!' });
```

## 📝 Git Commit

```bash
git add .
git commit -m "Add external API integrations and WebSocket support

- Add Google Places API integration for venue search/autocomplete
- Add Setlist.fm API integration for artist/setlist data
- Add Flask-SocketIO for real-time chat
- Add comprehensive documentation for external APIs and WebSockets
- Update requirements with new dependencies
- Update app initialization for SocketIO support"

git push origin main
```

## 📚 What Changed?

### New Functionality
- **Google Places API** (5 endpoints)
  - Venue search
  - Venue autocomplete
  - Venue details
  - Venue photos
  
- **Setlist.fm API** (4 endpoints)
  - Artist search
  - Artist details
  - Artist setlists
  - Setlist details

- **WebSocket Chat** (11 events)
  - Real-time messaging
  - User presence
  - Typing indicators
  - Message history

### Modified Files
- `app/__init__.py`: Added SocketIO initialization and external_api blueprint registration
- `run.py`: Changed from `app.run()` to `socketio.run(app)` for WebSocket support
- `requirements.txt`: Added googlemaps, requests, Flask-SocketIO, python-socketio, eventlet
- `.env.example`: Added Google Places and Setlist.fm API key placeholders

## 🎯 Next Steps

1. **Frontend Integration:**
   - Install `socket.io-client` in your frontend
   - Build venue autocomplete component
   - Create real-time chat UI
   - Implement setlist import feature

2. **Read Documentation:**
   - `EXTERNAL_API_DOCUMENTATION.md` for API usage
   - `WEBSOCKET_DOCUMENTATION.md` for chat integration
   - `BACKEND_ENHANCEMENTS_SUMMARY.md` for complete overview

3. **Test Everything:**
   - Create a test show with venue autocomplete
   - Import a setlist from Setlist.fm
   - Test real-time chat with multiple browser windows

## 🐛 Troubleshooting

**Problem:** `ModuleNotFoundError: No module named 'googlemaps'`
**Solution:** Run `pip install -r requirements.txt`

**Problem:** WebSocket connection fails
**Solution:** Make sure you're using `socketio.run()` in run.py, not `app.run()`

**Problem:** "Google Places API not configured"
**Solution:** Add `GOOGLE_PLACES_API_KEY` to your `.env` file

**Problem:** "Setlist.fm API not configured"
**Solution:** Add `SETLISTFM_API_KEY` to your `.env` file

## 📖 Additional Resources

- Google Places API Docs: https://developers.google.com/maps/documentation/places/web-service
- Setlist.fm API Docs: https://api.setlist.fm/docs/
- Socket.IO Docs: https://socket.io/docs/v4/
- Flask-SocketIO Docs: https://flask-socketio.readthedocs.io/

## ✅ Verification Checklist

- [ ] All new files copied to project
- [ ] Modified files updated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] API keys added to `.env`
- [ ] Server starts without errors
- [ ] Health check responds: `curl http://localhost:5000/api/external/health`
- [ ] Can test external API endpoints with authentication
- [ ] WebSocket connects in browser console
- [ ] Documentation files reviewed

---

**You're all set!** Your backend now has powerful external API integrations and real-time chat capabilities. Time to build the frontend! 🚀
