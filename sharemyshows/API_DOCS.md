# ShareMyShows API Documentation

Base URL: `http://localhost:5000/api`

## Table of Contents

1. [Authentication](#authentication)
2. [Shows](#shows)
3. [Artists](#artists)
4. [Venues](#venues)

---

## Authentication

### Register User

**POST** `/auth/register`

Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "SecurePass123!"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

**Response:** `201 Created`
```json
{
  "message": "User created successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "is_verified": false,
    "created_at": "2024-01-01T00:00:00"
  }
}
```

---

### Login

**POST** `/auth/login`

Authenticate and receive JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Login successful",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "mfa_enabled": false,
    "is_verified": false
  }
}
```

**Token Expiration:**
- Access Token: 15 minutes
- Refresh Token: 7 days

---

### Refresh Token

**POST** `/auth/refresh`

Get a new access token using refresh token.

**Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### Logout

**POST** `/auth/logout`

Logout and revoke current token.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Logout successful"
}
```

---

### Get Current User

**GET** `/auth/me`

Get current authenticated user's information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "profile_picture_url": null,
    "bio": null,
    "location": null,
    "mfa_enabled": false,
    "is_verified": false,
    "created_at": "2024-01-01T00:00:00",
    "last_login_at": "2024-01-01T12:00:00"
  }
}
```

---

### Update Profile

**PUT** `/auth/me`

Update current user's profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "bio": "Music lover and concert enthusiast",
  "location": "New York, NY",
  "profile_picture_url": "https://example.com/avatar.jpg"
}
```

**Response:** `200 OK`
```json
{
  "message": "Profile updated successfully",
  "user": { /* updated user object */ }
}
```

---

## Shows

### List Shows

**GET** `/shows`

Get a paginated list of shows.

**Query Parameters:**
- `page` (int, default: 1) - Page number
- `per_page` (int, default: 20, max: 100) - Items per page
- `user_id` (int) - Filter by user ID
- `is_public` (boolean) - Filter by public/private
- `is_past` (boolean) - Filter by past/upcoming
- `artist_id` (int) - Filter by artist
- `venue_id` (int) - Filter by venue

**Response:** `200 OK`
```json
{
  "shows": [
    {
      "id": 1,
      "user_id": 1,
      "venue_id": 1,
      "show_date": "2024-12-31",
      "show_time": "20:00:00",
      "title": "New Year's Eve Concert",
      "notes": "Amazing show!",
      "is_public": true,
      "is_past": false,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00",
      "venue": { /* venue object */ },
      "artists": [ /* artist objects */ ]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### Get Show

**GET** `/shows/{id}`

Get a single show by ID.

**Response:** `200 OK`
```json
{
  "show": {
    "id": 1,
    "user_id": 1,
    "venue_id": 1,
    "show_date": "2024-12-31",
    "show_time": "20:00:00",
    "title": "New Year's Eve Concert",
    "notes": "Amazing show!",
    "is_public": true,
    "is_past": false,
    "user": {
      "id": 1,
      "username": "johndoe",
      "profile_picture_url": null
    },
    "venue": { /* venue object */ },
    "artists": [ /* artist objects */ ]
  }
}
```

---

### Create Show

**POST** `/shows`

Create a new show.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "venue_id": 1,
  "show_date": "2024-12-31",
  "show_time": "20:00:00",
  "title": "New Year's Eve Concert",
  "notes": "Can't wait!",
  "is_public": true,
  "artist_ids": [1, 2, 3]
}
```

**Date/Time Formats:**
- `show_date`: YYYY-MM-DD
- `show_time`: HH:MM:SS (optional)

**Response:** `201 Created`
```json
{
  "message": "Show created successfully",
  "show": { /* show object */ }
}
```

---

### Update Show

**PUT** `/shows/{id}`

Update an existing show. Only the show owner can update.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:** (all fields optional)
```json
{
  "venue_id": 1,
  "show_date": "2024-12-31",
  "show_time": "20:00:00",
  "title": "Updated Title",
  "notes": "Updated notes",
  "is_public": false,
  "artist_ids": [1, 2]
}
```

**Response:** `200 OK`
```json
{
  "message": "Show updated successfully",
  "show": { /* updated show object */ }
}
```

---

### Delete Show

**DELETE** `/shows/{id}`

Delete a show. Only the show owner can delete.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Show deleted successfully"
}
```

---

### Get My Shows

**GET** `/shows/my-shows`

Get current user's shows.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `is_past` (boolean) - Filter by past/upcoming

**Response:** `200 OK`
```json
{
  "shows": [ /* array of show objects */ ],
  "pagination": { /* pagination object */ }
}
```

---

## Artists

### List Artists

**GET** `/artists`

Get a paginated list of artists.

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `search` (string) - Search by name

**Response:** `200 OK`
```json
{
  "artists": [
    {
      "id": 1,
      "name": "Taylor Swift",
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "pagination": { /* pagination object */ }
}
```

---

### Get Artist

**GET** `/artists/{id}`

Get a single artist with their recent shows.

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Taylor Swift",
  "created_at": "2024-01-01T00:00:00",
  "shows": [ /* up to 10 most recent shows */ ],
  "total_shows": 50
}
```

---

### Create Artist

**POST** `/artists`

Create a new artist.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "Taylor Swift"
}
```

**Response:** `201 Created`
```json
{
  "message": "Artist created successfully",
  "artist": {
    "id": 1,
    "name": "Taylor Swift",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

**Note:** If artist already exists, returns `409 Conflict` with the existing artist.

---

### Search Artists

**GET** `/artists/search`

Search artists by name (for autocomplete).

**Query Parameters:**
- `q` (string, required) - Search query
- `limit` (int, default: 10, max: 50) - Maximum results

**Response:** `200 OK`
```json
{
  "artists": [ /* matching artists */ ]
}
```

---

### Bulk Create Artists

**POST** `/artists/bulk`

Create multiple artists at once.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "artists": ["Taylor Swift", "Ed Sheeran", "Adele"]
}
```

**Response:** `201 Created`
```json
{
  "message": "Created 2 artists, 1 already existed",
  "created": [ /* newly created artists */ ],
  "existing": [ /* already existing artists */ ]
}
```

---

## Venues

### List Venues

**GET** `/venues`

Get a paginated list of venues.

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 20, max: 100)
- `search` (string) - Search by name or location
- `city` (string) - Filter by city
- `state` (string) - Filter by state
- `country` (string) - Filter by country

**Response:** `200 OK`
```json
{
  "venues": [
    {
      "id": 1,
      "name": "Madison Square Garden",
      "location": "4 Pennsylvania Plaza, New York, NY 10001",
      "city": "New York",
      "state": "NY",
      "country": "USA",
      "latitude": 40.7505,
      "longitude": -73.9934,
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "pagination": { /* pagination object */ }
}
```

---

### Get Venue

**GET** `/venues/{id}`

Get a single venue with its recent shows.

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Madison Square Garden",
  "location": "4 Pennsylvania Plaza, New York, NY 10001",
  "city": "New York",
  "state": "NY",
  "country": "USA",
  "latitude": 40.7505,
  "longitude": -73.9934,
  "created_at": "2024-01-01T00:00:00",
  "shows": [ /* up to 10 most recent shows */ ],
  "total_shows": 100
}
```

---

### Create Venue

**POST** `/venues`

Create a new venue.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "name": "Madison Square Garden",
  "location": "4 Pennsylvania Plaza, New York, NY 10001",
  "city": "New York",
  "state": "NY",
  "country": "USA",
  "latitude": 40.7505,
  "longitude": -73.9934
}
```

**Required Fields:**
- `name`
- `location`

**Optional Fields:**
- `city`
- `state`
- `country`
- `latitude` (must include longitude)
- `longitude` (must include latitude)

**Coordinate Validation:**
- Latitude: -90 to 90
- Longitude: -180 to 180

**Response:** `201 Created`
```json
{
  "message": "Venue created successfully",
  "venue": { /* venue object */ }
}
```

---

### Search Venues

**GET** `/venues/search`

Search venues by name or location (for autocomplete).

**Query Parameters:**
- `q` (string, required) - Search query
- `limit` (int, default: 10, max: 50) - Maximum results

**Response:** `200 OK`
```json
{
  "venues": [ /* matching venues */ ]
}
```

---

### Get Nearby Venues

**GET** `/venues/nearby`

Get venues near a location (uses Haversine formula).

**Query Parameters:**
- `latitude` (float, required) - Current latitude
- `longitude` (float, required) - Current longitude
- `radius` (float, default: 10, max: 100) - Search radius in kilometers
- `limit` (int, default: 20, max: 100) - Maximum results

**Response:** `200 OK`
```json
{
  "venues": [
    {
      "id": 1,
      "name": "Madison Square Garden",
      "location": "4 Pennsylvania Plaza, New York, NY 10001",
      "distance_km": 2.5,
      /* ... other venue fields */
    }
  ],
  "search_params": {
    "latitude": 40.7505,
    "longitude": -73.9934,
    "radius_km": 10
  }
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Validation Error",
  "message": "Detailed error message"
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "message": "You do not have permission to access this resource"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "The requested resource was not found"
}
```

### 409 Conflict
```json
{
  "error": "Conflict",
  "message": "Resource already exists"
}
```

### 429 Too Many Requests
```json
{
  "error": "Too Many Requests",
  "message": "Too many login attempts. Try again in 900 seconds",
  "retry_after": 900
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

---

## Rate Limiting

The API implements rate limiting on sensitive endpoints:

- **Login attempts**: 5 attempts per 15 minutes per user
- Failed login attempts are tracked and reset on successful login

---

## Future Endpoints (Coming in Phase 2+)

- **Photos**: Upload and manage show photos
- **Audio**: Record and manage audio clips
- **Setlists**: Track setlists for shows
- **Comments**: Comment on shows
- **Friends**: Friend system
- **Messages**: Direct messaging
- **Check-ins**: Real-time location check-ins
- **Notifications**: Push notifications
