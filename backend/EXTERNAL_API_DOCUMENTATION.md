# External API Integration Documentation

This document describes the external API integration endpoints for Google Places and Setlist.fm.

## Setup Instructions

### 1. Google Places API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Places API
   - Maps JavaScript API (optional, for frontend maps)
   - Geocoding API (optional, for address conversion)
4. Go to **Credentials** and create an API key
5. Add the API key to your `.env` file:
   ```
   GOOGLE_PLACES_API_KEY=your-api-key-here
   ```

**Important:** Restrict your API key by:
- API restrictions: Limit to Places API, Geocoding API
- Application restrictions: Set HTTP referrers for production

### 2. Setlist.fm API Setup

1. Create an account at [Setlist.fm](https://www.setlist.fm/)
2. Go to [API Settings](https://www.setlist.fm/settings/apps)
3. Create a new application
4. Copy the API key
5. Add the API key to your `.env` file:
   ```
   SETLISTFM_API_KEY=your-api-key-here
   ```

**Rate Limits:**
- Setlist.fm: 2 requests per second per IP address
- Google Places: Pay-as-you-go pricing (free tier available)

---

## API Endpoints

### Health Check

Check the status of external API integrations.

**Endpoint:** `GET /api/external/health`

**Authentication:** Not required

**Response:**
```json
{
  "google_places": "configured",
  "setlistfm": "configured"
}
```

---

## Google Places API Endpoints

### 1. Search Venues

Search for concert venues using Google Places API.

**Endpoint:** `GET /api/external/venues/search`

**Authentication:** Required (JWT)

**Query Parameters:**
- `query` (required): Search string (minimum 2 characters)
- `location` (optional): `lat,lng` for location bias
- `radius` (optional): Search radius in meters (default 50000)

**Example Request:**
```bash
curl -X GET 'http://localhost:5000/api/external/venues/search?query=madison+square+garden' \
  -H 'Cookie: access_token_cookie=your-jwt-token'
```

**Example Response:**
```json
{
  "venues": [
    {
      "place_id": "ChIJhRwB-yFawokR5Phil-QQ3zM",
      "name": "Madison Square Garden",
      "formatted_address": "4 Pennsylvania Plaza, New York, NY 10001, USA",
      "location": {
        "lat": 40.7505045,
        "lng": -73.9934387
      },
      "types": ["stadium", "establishment"],
      "rating": 4.5,
      "user_ratings_total": 48234
    }
  ],
  "count": 1
}
```

---

### 2. Autocomplete Venues

Get venue autocomplete suggestions as users type (faster than full search).

**Endpoint:** `GET /api/external/venues/autocomplete`

**Authentication:** Required (JWT)

**Query Parameters:**
- `input` (required): Search string (minimum 2 characters)
- `location` (optional): `lat,lng` for location bias

**Example Request:**
```bash
curl -X GET 'http://localhost:5000/api/external/venues/autocomplete?input=madison' \
  -H 'Cookie: access_token_cookie=your-jwt-token'
```

**Example Response:**
```json
{
  "suggestions": [
    {
      "place_id": "ChIJhRwB-yFawokR5Phil-QQ3zM",
      "description": "Madison Square Garden, Pennsylvania Plaza, New York, NY, USA",
      "main_text": "Madison Square Garden",
      "secondary_text": "Pennsylvania Plaza, New York, NY, USA",
      "types": ["stadium", "establishment"]
    }
  ],
  "count": 1
}
```

**Usage Tip:** Call this endpoint on every keystroke (with debouncing) to provide real-time suggestions as users type venue names.

---

### 3. Get Venue Details

Get detailed information about a specific venue by place_id.

**Endpoint:** `GET /api/external/venues/details/<place_id>`

**Authentication:** Required (JWT)

**Example Request:**
```bash
curl -X GET 'http://localhost:5000/api/external/venues/details/ChIJhRwB-yFawokR5Phil-QQ3zM' \
  -H 'Cookie: access_token_cookie=your-jwt-token'
```

**Example Response:**
```json
{
  "place_id": "ChIJhRwB-yFawokR5Phil-QQ3zM",
  "name": "Madison Square Garden",
  "formatted_address": "4 Pennsylvania Plaza, New York, NY 10001, USA",
  "location": "New York, NY",
  "latitude": 40.7505045,
  "longitude": -73.9934387,
  "phone": "(212) 465-6741",
  "website": "https://www.msg.com/",
  "rating": 4.5,
  "user_ratings_total": 48234,
  "types": ["stadium", "establishment"],
  "photos": [
    {
      "photo_reference": "ATtYBwKl...",
      "width": 4032,
      "height": 3024
    }
  ],
  "google_maps_url": "https://maps.google.com/?cid=3659...",
  "city": "New York",
  "state": "NY",
  "country": "United States"
}
```

---

### 4. Get Venue Photo

Get a venue photo URL by photo_reference.

**Endpoint:** `GET /api/external/venues/photo/<photo_reference>`

**Authentication:** Required (JWT)

**Query Parameters:**
- `max_width` (optional): Maximum width in pixels (default 400)

**Example Request:**
```bash
curl -X GET 'http://localhost:5000/api/external/venues/photo/ATtYBwKl...?max_width=800' \
  -H 'Cookie: access_token_cookie=your-jwt-token'
```

**Example Response:**
```json
{
  "photo_url": "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photo_reference=ATtYBwKl...&key=YOUR_API_KEY"
}
```

---

## Setlist.fm API Endpoints

### 1. Search Artists

Search for artists on Setlist.fm by name.

**Endpoint:** `GET /api/external/artists/search`

**Authentication:** Required (JWT)

**Query Parameters:**
- `query` (required): Artist name (minimum 2 characters)
- `sort` (optional): Sort method - `relevance` or `sortName` (default: `relevance`)

**Example Request:**
```bash
curl -X GET 'http://localhost:5000/api/external/artists/search?query=arctic+monkeys' \
  -H 'Cookie: access_token_cookie=your-jwt-token'
```

**Example Response:**
```json
{
  "artists": [
    {
      "mbid": "ada7a83c-e3e1-40f1-93f9-3e73dbc9298a",
      "name": "Arctic Monkeys",
      "sort_name": "Arctic Monkeys",
      "disambiguation": "",
      "url": "https://www.setlist.fm/setlists/arctic-monkeys-53d6ebd3.html"
    }
  ],
  "count": 1,
  "total": 1
}
```

**Note:** The `mbid` (MusicBrainz ID) is used to fetch artist details and setlists.

---

### 2. Get Artist Details

Get detailed information about an artist by MusicBrainz ID.

**Endpoint:** `GET /api/external/artists/<mbid>`

**Authentication:** Required (JWT)

**Example Request:**
```bash
curl -X GET 'http://localhost:5000/api/external/artists/ada7a83c-e3e1-40f1-93f9-3e73dbc9298a' \
  -H 'Cookie: access_token_cookie=your-jwt-token'
```

**Example Response:**
```json
{
  "mbid": "ada7a83c-e3e1-40f1-93f9-3e73dbc9298a",
  "name": "Arctic Monkeys",
  "sort_name": "Arctic Monkeys",
  "disambiguation": "",
  "url": "https://www.setlist.fm/setlists/arctic-monkeys-53d6ebd3.html"
}
```

---

### 3. Get Artist Setlists

Get setlists for an artist (paginated).

**Endpoint:** `GET /api/external/artists/<mbid>/setlists`

**Authentication:** Required (JWT)

**Query Parameters:**
- `page` (optional): Page number (default 1, 20 results per page)

**Example Request:**
```bash
curl -X GET 'http://localhost:5000/api/external/artists/ada7a83c-e3e1-40f1-93f9-3e73dbc9298a/setlists?page=1' \
  -H 'Cookie: access_token_cookie=your-jwt-token'
```

**Example Response:**
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
        "state": "NY",
        "country": "United States"
      },
      "tour": "The Car Tour",
      "info": "Opening night of North American leg",
      "url": "https://www.setlist.fm/setlist/arctic-monkeys/...",
      "songs": [
        {
          "name": "Do I Wanna Know?",
          "info": "",
          "tape": false
        },
        {
          "name": "Brianstorm",
          "info": "",
          "tape": false
        }
      ],
      "song_count": 20
    }
  ],
  "count": 1,
  "page": 1,
  "total_pages": 15
}
```

**Note:** `event_date` format is `dd-MM-yyyy` (e.g., "15-10-2024")

---

### 4. Get Setlist Details

Get detailed information about a specific setlist by ID.

**Endpoint:** `GET /api/external/setlists/<setlist_id>`

**Authentication:** Required (JWT)

**Example Request:**
```bash
curl -X GET 'http://localhost:5000/api/external/setlists/63e8d2bf' \
  -H 'Cookie: access_token_cookie=your-jwt-token'
```

**Example Response:**
```json
{
  "id": "63e8d2bf",
  "event_date": "15-10-2024",
  "artist": {
    "mbid": "ada7a83c-e3e1-40f1-93f9-3e73dbc9298a",
    "name": "Arctic Monkeys",
    "sort_name": "Arctic Monkeys"
  },
  "venue": {
    "name": "Madison Square Garden",
    "city": "New York",
    "state": "NY",
    "state_code": "NY",
    "country": "United States",
    "country_code": "US",
    "coordinates": {
      "lat": 40.7505045,
      "long": -73.9934387
    }
  },
  "tour": "The Car Tour",
  "info": "Opening night of North American leg",
  "url": "https://www.setlist.fm/setlist/arctic-monkeys/...",
  "songs": [
    {
      "name": "Do I Wanna Know?",
      "info": "",
      "tape": false,
      "set_name": "Set 1"
    },
    {
      "name": "Brianstorm",
      "info": "",
      "tape": false,
      "set_name": "Set 1"
    },
    {
      "name": "505",
      "info": "",
      "tape": false,
      "set_name": "Encore"
    }
  ],
  "song_count": 20
}
```

---

## Integration with Show Creation

### Recommended User Flow

1. **Venue Selection:**
   - User starts typing venue name
   - Call `/api/external/venues/autocomplete` with each keystroke (debounced)
   - Display autocomplete suggestions
   - When user selects venue, call `/api/external/venues/details/<place_id>`
   - Store venue details in database when creating show

2. **Artist Selection:**
   - User types artist name
   - Call `/api/external/artists/search?query=...`
   - Display artist suggestions with MusicBrainz IDs
   - Store artist name and MBID when creating show

3. **Setlist Import (Optional):**
   - After show is created, offer to import setlist
   - Call `/api/external/artists/<mbid>/setlists`
   - Let user select a setlist from the artist's recent shows
   - Call `/api/external/setlists/<setlist_id>` to get full details
   - Bulk create setlist songs using `/api/shows/<show_id>/setlist`

### Example: Creating a Show with External Data

```javascript
// Step 1: Search and select venue
const venueResponse = await fetch('/api/external/venues/autocomplete?input=madison');
const venues = await venueResponse.json();
const selectedVenue = venues.suggestions[0];

// Step 2: Get venue details
const venueDetails = await fetch(`/api/external/venues/details/${selectedVenue.place_id}`);
const venue = await venueDetails.json();

// Step 3: Search and select artist
const artistResponse = await fetch('/api/external/artists/search?query=arctic+monkeys');
const artists = await artistResponse.json();
const selectedArtist = artists.artists[0];

// Step 4: Create show with external data
const showData = {
  artist_name: selectedArtist.name,
  artist_mbid: selectedArtist.mbid,  // Optional: store for setlist lookup
  venue_name: venue.name,
  venue_location: venue.location,
  place_id: venue.place_id,
  address: venue.formatted_address,
  latitude: venue.latitude,
  longitude: venue.longitude,
  date: '2024-10-15',
  time: '20:00',
  notes: 'Amazing show!'
};

const createResponse = await fetch('/api/shows', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(showData)
});

const show = await createResponse.json();

// Step 5: Optional - Import setlist
const setlistsResponse = await fetch(`/api/external/artists/${selectedArtist.mbid}/setlists`);
const setlists = await setlistsResponse.json();
const latestSetlist = setlists.setlists[0];

// Import songs from setlist
for (const song of latestSetlist.songs) {
  await fetch(`/api/shows/${show.id}/setlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: song.name,
      notes: song.info || ''
    })
  });
}
```

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid parameters (e.g., query too short)
- `401 Unauthorized`: Missing or invalid JWT token
- `404 Not Found`: Resource not found (artist, setlist, etc.)
- `500 Internal Server Error`: Server or API error
- `503 Service Unavailable`: API key not configured

Error responses include details:
```json
{
  "error": "Failed to search venues",
  "details": "API key is invalid"
}
```

---

## Rate Limiting & Best Practices

1. **Debouncing:** For autocomplete endpoints, wait 300-500ms after user stops typing before making API call

2. **Caching:** Consider caching venue and artist data in your database to reduce API calls

3. **Error Recovery:** Handle API failures gracefully - allow manual entry if external APIs are unavailable

4. **Batch Operations:** When importing setlists with many songs, consider adding a progress indicator

5. **API Key Security:** Never expose API keys in frontend code - all calls go through your backend

---

## Testing

Test the external API health:
```bash
curl http://localhost:5000/api/external/health
```

Test venue search:
```bash
curl -X GET 'http://localhost:5000/api/external/venues/search?query=red+rocks' \
  -H 'Cookie: access_token_cookie=YOUR_JWT_TOKEN'
```

Test artist search:
```bash
curl -X GET 'http://localhost:5000/api/external/artists/search?query=radiohead' \
  -H 'Cookie: access_token_cookie=YOUR_JWT_TOKEN'
```

---

## Next Steps

1. Add the API keys to your `.env` file
2. Test the endpoints using curl or Postman
3. Integrate venue autocomplete into the frontend show creation form
4. Add artist search to improve artist data quality
5. Implement optional setlist import feature

For real-time features (WebSockets for chat), see `WEBSOCKET_DOCUMENTATION.md`.
