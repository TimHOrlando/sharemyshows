# ShareMyShows - Quick API Reference

Quick reference guide for the most commonly used external API and WebSocket endpoints.

---

## 🔍 Venue Search & Autocomplete

### Search Venues
```bash
GET /api/external/venues/autocomplete?input=madison
```

**Response:**
```json
{
  "suggestions": [
    {
      "place_id": "ChIJhRwB-yFawokR5Phil-QQ3zM",
      "description": "Madison Square Garden, Pennsylvania Plaza, New York, NY, USA",
      "main_text": "Madison Square Garden",
      "secondary_text": "Pennsylvania Plaza, New York, NY, USA"
    }
  ]
}
```

### Get Venue Details
```bash
GET /api/external/venues/details/ChIJhRwB-yFawokR5Phil-QQ3zM
```

**Response:**
```json
{
  "place_id": "ChIJhRwB-yFawokR5Phil-QQ3zM",
  "name": "Madison Square Garden",
  "formatted_address": "4 Pennsylvania Plaza, New York, NY 10001, USA",
  "latitude": 40.7505045,
  "longitude": -73.9934387,
  "phone": "(212) 465-6741",
  "website": "https://www.msg.com/"
}
```

---

## 🎤 Artist Search & Setlists

### Search Artists
```bash
GET /api/external/artists/search?query=arctic+monkeys
```

**Response:**
```json
{
  "artists": [
    {
      "mbid": "ada7a83c-e3e1-40f1-93f9-3e73dbc9298a",
      "name": "Arctic Monkeys",
      "url": "https://www.setlist.fm/setlists/arctic-monkeys-53d6ebd3.html"
    }
  ]
}
```

### Get Artist's Setlists
```bash
GET /api/external/artists/ada7a83c-e3e1-40f1-93f9-3e73dbc9298a/setlists
```

**Response:**
```json
{
  "setlists": [
    {
      "id": "63e8d2bf",
      "event_date": "15-10-2024",
      "artist": "Arctic Monkeys",
      "venue": {
        "name": "Madison Square Garden",
        "city": "New York",
        "state": "NY"
      },
      "songs": [
        { "name": "Do I Wanna Know?" },
        { "name": "Brianstorm" }
      ],
      "song_count": 20
    }
  ]
}
```

### Get Setlist Details
```bash
GET /api/external/setlists/63e8d2bf
```

**Response:**
```json
{
  "id": "63e8d2bf",
  "songs": [
    {
      "name": "Do I Wanna Know?",
      "set_name": "Set 1"
    },
    {
      "name": "505",
      "set_name": "Encore"
    }
  ]
}
```

---

## 💬 WebSocket Chat Events

### Connect & Join
```javascript
import { io } from 'socket.io-client';

// Connect
const socket = io('http://localhost:5000', {
  withCredentials: true
});

// Join show
socket.emit('join_show', { show_id: 1 });
```

### Listen for Events
```javascript
// Message history
socket.on('message_history', (data) => {
  setMessages(data.messages);
});

// New message
socket.on('new_message', (message) => {
  setMessages(prev => [...prev, message]);
});

// Active users
socket.on('active_users', (data) => {
  setActiveUsers(data.active_users);
});
```

### Send Message
```javascript
socket.emit('send_message', {
  show_id: 1,
  message: 'Amazing show!'
});
```

### Typing Indicator
```javascript
// Start typing
socket.emit('typing', {
  show_id: 1,
  is_typing: true
});

// Stop typing (after 2 seconds)
setTimeout(() => {
  socket.emit('typing', {
    show_id: 1,
    is_typing: false
  });
}, 2000);
```

### Leave Show
```javascript
socket.emit('leave_show', { show_id: 1 });
socket.disconnect();
```

---

## 🔄 Complete User Flow Example

### Creating a Show with External Data

```javascript
// 1. Search for venue
const venueResponse = await fetch(
  '/api/external/venues/autocomplete?input=madison',
  { credentials: 'include' }
);
const venues = await venueResponse.json();
const venue = venues.suggestions[0];

// 2. Get venue details
const detailsResponse = await fetch(
  `/api/external/venues/details/${venue.place_id}`,
  { credentials: 'include' }
);
const venueDetails = await detailsResponse.json();

// 3. Search for artist
const artistResponse = await fetch(
  '/api/external/artists/search?query=arctic+monkeys',
  { credentials: 'include' }
);
const artists = await artistResponse.json();
const artist = artists.artists[0];

// 4. Create show
const showResponse = await fetch('/api/shows', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    artist_name: artist.name,
    artist_mbid: artist.mbid,
    venue_name: venueDetails.name,
    venue_location: venueDetails.location,
    place_id: venueDetails.place_id,
    address: venueDetails.formatted_address,
    latitude: venueDetails.latitude,
    longitude: venueDetails.longitude,
    date: '2024-11-16',
    time: '20:00',
    notes: 'Concert night!'
  })
});
const show = await showResponse.json();

// 5. Optional: Import setlist
const setlistsResponse = await fetch(
  `/api/external/artists/${artist.mbid}/setlists`,
  { credentials: 'include' }
);
const setlists = await setlistsResponse.json();
const latestSetlist = setlists.setlists[0];

// Get full setlist
const setlistResponse = await fetch(
  `/api/external/setlists/${latestSetlist.id}`,
  { credentials: 'include' }
);
const setlist = await setlistResponse.json();

// Add songs to show
for (const song of setlist.songs) {
  await fetch(`/api/shows/${show.id}/setlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      title: song.name,
      notes: song.info || ''
    })
  });
}

// 6. Join chat
socket.emit('join_show', { show_id: show.id });
```

---

## 🎨 React Component Examples

### Venue Autocomplete Hook

```javascript
import { useState, useEffect } from 'react';

export function useVenueAutocomplete(query) {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!query || query.length < 2) {
      setSuggestions([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const response = await fetch(
          `/api/external/venues/autocomplete?input=${encodeURIComponent(query)}`,
          { credentials: 'include' }
        );
        const data = await response.json();
        setSuggestions(data.suggestions || []);
      } catch (error) {
        console.error('Venue search error:', error);
      } finally {
        setLoading(false);
      }
    }, 300); // Debounce 300ms

    return () => clearTimeout(timer);
  }, [query]);

  return { suggestions, loading };
}
```

### Chat Hook

```javascript
import { useEffect, useState, useRef } from 'react';
import { io } from 'socket.io-client';

export function useShowChat(showId) {
  const [messages, setMessages] = useState([]);
  const [activeUsers, setActiveUsers] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    if (!showId) return;

    socketRef.current = io('http://localhost:5000', {
      withCredentials: true
    });

    const socket = socketRef.current;

    socket.on('connect', () => {
      setIsConnected(true);
      socket.emit('join_show', { show_id: showId });
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
    });

    socket.on('message_history', (data) => {
      setMessages(data.messages);
    });

    socket.on('new_message', (message) => {
      setMessages(prev => [...prev, message]);
    });

    socket.on('active_users', (data) => {
      setActiveUsers(data.active_users);
    });

    return () => {
      if (socket.connected) {
        socket.emit('leave_show', { show_id: showId });
        socket.disconnect();
      }
    };
  }, [showId]);

  const sendMessage = (message) => {
    if (socketRef.current && message.trim()) {
      socketRef.current.emit('send_message', {
        show_id: showId,
        message: message.trim()
      });
    }
  };

  return { messages, activeUsers, isConnected, sendMessage };
}
```

---

## ⚡ Common Patterns

### Debounced Search
```javascript
const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => clearTimeout(timer);
  }, [value, delay]);
  
  return debouncedValue;
};

// Usage
const [query, setQuery] = useState('');
const debouncedQuery = useDebounce(query, 300);

useEffect(() => {
  if (debouncedQuery.length >= 2) {
    // Fetch autocomplete suggestions
  }
}, [debouncedQuery]);
```

### Error Handling
```javascript
const fetchWithErrorHandling = async (url, options = {}) => {
  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'include'
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    // Show user-friendly error message
    return null;
  }
};
```

---

## 🔐 Authentication

All endpoints require JWT authentication via HTTP-only cookies.

**Login first:**
```javascript
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    username: 'user',
    password: 'pass'
  })
});
```

**Then use credentials: 'include' on all requests:**
```javascript
fetch('/api/external/venues/search?query=madison', {
  credentials: 'include'  // Important!
});
```

---

## 🎯 Testing Commands

```bash
# Health check
curl http://localhost:5000/api/external/health

# With authentication
curl -X GET 'http://localhost:5000/api/external/venues/search?query=red+rocks' \
  -H 'Cookie: access_token_cookie=YOUR_JWT_TOKEN'

# WebSocket (browser console)
const socket = io('http://localhost:5000', { withCredentials: true });
socket.emit('join_show', { show_id: 1 });
socket.emit('send_message', { show_id: 1, message: 'Test!' });
```

---

## 📚 Full Documentation

- **External APIs:** See `EXTERNAL_API_DOCUMENTATION.md`
- **WebSockets:** See `WEBSOCKET_DOCUMENTATION.md`
- **Session Summary:** See `BACKEND_ENHANCEMENTS_SUMMARY.md`

---

**Happy Coding! 🚀**
