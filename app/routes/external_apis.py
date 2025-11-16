"""
External API Integration Routes
Handles Google Places API and Setlist.fm API integrations
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import googlemaps
import requests
import os

external_api = Blueprint('external_api', __name__, url_prefix='/api/external')

# Initialize Google Maps client
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
SETLISTFM_API_KEY = os.getenv('SETLISTFM_API_KEY')

gmaps = None
if GOOGLE_PLACES_API_KEY:
    try:
        gmaps = googlemaps.Client(key=GOOGLE_PLACES_API_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize Google Maps client: {e}")

# ===== GOOGLE PLACES API ENDPOINTS =====

@external_api.route('/venues/search', methods=['GET'])
@jwt_required()
def search_venues():
    """
    Search for venues using Google Places API autocomplete
    Query params:
      - query: search string (required)
      - location: lat,lng for location bias (optional)
      - radius: search radius in meters (optional, default 50000)
    """
    if not gmaps:
        return jsonify({'error': 'Google Places API not configured'}), 503
    
    query = request.args.get('query')
    if not query or len(query) < 2:
        return jsonify({'error': 'Query must be at least 2 characters'}), 400
    
    try:
        # Use Places API Text Search for concert venues
        results = gmaps.places(
            query=f"{query} concert venue music hall amphitheater",
            type='establishment'
        )
        
        venues = []
        for place in results.get('results', [])[:10]:  # Limit to top 10 results
            venues.append({
                'place_id': place['place_id'],
                'name': place['name'],
                'formatted_address': place.get('formatted_address', ''),
                'location': {
                    'lat': place['geometry']['location']['lat'],
                    'lng': place['geometry']['location']['lng']
                },
                'types': place.get('types', []),
                'rating': place.get('rating'),
                'user_ratings_total': place.get('user_ratings_total')
            })
        
        return jsonify({
            'venues': venues,
            'count': len(venues)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to search venues', 'details': str(e)}), 500


@external_api.route('/venues/autocomplete', methods=['GET'])
@jwt_required()
def autocomplete_venues():
    """
    Get venue autocomplete suggestions as user types
    Query params:
      - input: search string (required)
      - location: lat,lng for location bias (optional)
    """
    if not gmaps:
        return jsonify({'error': 'Google Places API not configured'}), 503
    
    input_text = request.args.get('input')
    if not input_text or len(input_text) < 2:
        return jsonify({'error': 'Input must be at least 2 characters'}), 400
    
    try:
        # Use Autocomplete for faster, more relevant results
        location = request.args.get('location')  # Format: "lat,lng"
        
        autocomplete_params = {
            'input_text': input_text,
            'types': 'establishment'
        }
        
        if location:
            try:
                lat, lng = map(float, location.split(','))
                autocomplete_params['location'] = (lat, lng)
                autocomplete_params['radius'] = 50000  # 50km radius
            except ValueError:
                pass
        
        results = gmaps.places_autocomplete(**autocomplete_params)
        
        suggestions = []
        for prediction in results[:10]:  # Limit to 10 suggestions
            suggestions.append({
                'place_id': prediction['place_id'],
                'description': prediction['description'],
                'main_text': prediction['structured_formatting']['main_text'],
                'secondary_text': prediction['structured_formatting'].get('secondary_text', ''),
                'types': prediction.get('types', [])
            })
        
        return jsonify({
            'suggestions': suggestions,
            'count': len(suggestions)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get autocomplete suggestions', 'details': str(e)}), 500


@external_api.route('/venues/details/<place_id>', methods=['GET'])
@jwt_required()
def get_venue_details(place_id):
    """
    Get detailed information about a venue by place_id
    Returns: name, address, coordinates, photos, phone, website, etc.
    """
    if not gmaps:
        return jsonify({'error': 'Google Places API not configured'}), 503
    
    try:
        # Get place details from Google Places API
        place = gmaps.place(
            place_id=place_id,
            fields=[
                'name', 'formatted_address', 'geometry', 'formatted_phone_number',
                'website', 'rating', 'user_ratings_total', 'photos', 'types',
                'address_components', 'url'
            ]
        )
        
        result = place.get('result', {})
        
        # Extract location info
        location = result.get('geometry', {}).get('location', {})
        
        # Parse address components for city, state, country
        address_components = result.get('address_components', [])
        city = state = country = ''
        
        for component in address_components:
            if 'locality' in component['types']:
                city = component['long_name']
            elif 'administrative_area_level_1' in component['types']:
                state = component['short_name']
            elif 'country' in component['types']:
                country = component['long_name']
        
        # Get photo references (first 5)
        photos = []
        for photo in result.get('photos', [])[:5]:
            photos.append({
                'photo_reference': photo['photo_reference'],
                'width': photo['width'],
                'height': photo['height']
            })
        
        venue_details = {
            'place_id': place_id,
            'name': result.get('name', ''),
            'formatted_address': result.get('formatted_address', ''),
            'location': f"{city}, {state}" if city and state else result.get('formatted_address', ''),
            'latitude': location.get('lat'),
            'longitude': location.get('lng'),
            'phone': result.get('formatted_phone_number'),
            'website': result.get('website'),
            'rating': result.get('rating'),
            'user_ratings_total': result.get('user_ratings_total'),
            'types': result.get('types', []),
            'photos': photos,
            'google_maps_url': result.get('url'),
            'city': city,
            'state': state,
            'country': country
        }
        
        return jsonify(venue_details), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get venue details', 'details': str(e)}), 500


@external_api.route('/venues/photo/<photo_reference>', methods=['GET'])
@jwt_required()
def get_venue_photo(photo_reference):
    """
    Get a venue photo URL by photo_reference
    Query params:
      - max_width: maximum width in pixels (optional, default 400)
    """
    if not gmaps:
        return jsonify({'error': 'Google Places API not configured'}), 503
    
    max_width = request.args.get('max_width', 400, type=int)
    
    try:
        # Note: This returns the raw photo data, you may want to serve it differently
        photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photo_reference={photo_reference}&key={GOOGLE_PLACES_API_KEY}"
        
        return jsonify({'photo_url': photo_url}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get photo', 'details': str(e)}), 500


# ===== SETLIST.FM API ENDPOINTS =====

SETLISTFM_BASE_URL = 'https://api.setlist.fm/rest/1.0'

@external_api.route('/artists/search', methods=['GET'])
@jwt_required()
def search_artists():
    """
    Search for artists on Setlist.fm
    Query params:
      - query: artist name (required)
      - sort: sort method - 'relevance' or 'sortName' (optional)
    """
    if not SETLISTFM_API_KEY:
        return jsonify({'error': 'Setlist.fm API not configured'}), 503
    
    query = request.args.get('query')
    if not query or len(query) < 2:
        return jsonify({'error': 'Query must be at least 2 characters'}), 400
    
    try:
        headers = {
            'Accept': 'application/json',
            'x-api-key': SETLISTFM_API_KEY
        }
        
        params = {
            'artistName': query,
            'sort': request.args.get('sort', 'relevance')
        }
        
        response = requests.get(
            f'{SETLISTFM_BASE_URL}/search/artists',
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to search artists', 'status': response.status_code}), 500
        
        data = response.json()
        artists = []
        
        for artist in data.get('artist', [])[:15]:  # Limit to 15 results
            artists.append({
                'mbid': artist['mbid'],  # MusicBrainz ID
                'name': artist['name'],
                'sort_name': artist.get('sortName', ''),
                'disambiguation': artist.get('disambiguation', ''),
                'url': artist.get('url', '')
            })
        
        return jsonify({
            'artists': artists,
            'count': len(artists),
            'total': data.get('total', 0)
        }), 200
        
    except requests.RequestException as e:
        return jsonify({'error': 'Failed to connect to Setlist.fm', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Failed to search artists', 'details': str(e)}), 500


@external_api.route('/artists/<mbid>', methods=['GET'])
@jwt_required()
def get_artist_details(mbid):
    """
    Get artist details by MusicBrainz ID (mbid)
    Returns: name, disambiguation, url
    """
    if not SETLISTFM_API_KEY:
        return jsonify({'error': 'Setlist.fm API not configured'}), 503
    
    try:
        headers = {
            'Accept': 'application/json',
            'x-api-key': SETLISTFM_API_KEY
        }
        
        response = requests.get(
            f'{SETLISTFM_BASE_URL}/artist/{mbid}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 404:
            return jsonify({'error': 'Artist not found'}), 404
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to get artist details', 'status': response.status_code}), 500
        
        artist = response.json()
        
        artist_details = {
            'mbid': artist['mbid'],
            'name': artist['name'],
            'sort_name': artist.get('sortName', ''),
            'disambiguation': artist.get('disambiguation', ''),
            'url': artist.get('url', '')
        }
        
        return jsonify(artist_details), 200
        
    except requests.RequestException as e:
        return jsonify({'error': 'Failed to connect to Setlist.fm', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Failed to get artist details', 'details': str(e)}), 500


@external_api.route('/artists/<mbid>/setlists', methods=['GET'])
@jwt_required()
def get_artist_setlists(mbid):
    """
    Get setlists for an artist by MusicBrainz ID
    Query params:
      - page: page number (optional, default 1)
    Returns: paginated list of setlists for the artist
    """
    if not SETLISTFM_API_KEY:
        return jsonify({'error': 'Setlist.fm API not configured'}), 503
    
    try:
        headers = {
            'Accept': 'application/json',
            'x-api-key': SETLISTFM_API_KEY
        }
        
        params = {
            'p': request.args.get('page', 1, type=int)
        }
        
        response = requests.get(
            f'{SETLISTFM_BASE_URL}/artist/{mbid}/setlists',
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to get setlists', 'status': response.status_code}), 500
        
        data = response.json()
        setlists = []
        
        for setlist in data.get('setlist', []):
            # Parse setlist data
            venue = setlist.get('venue', {})
            city = venue.get('city', {})
            
            # Extract songs from sets
            songs = []
            for set_item in setlist.get('sets', {}).get('set', []):
                for song in set_item.get('song', []):
                    songs.append({
                        'name': song.get('name', ''),
                        'info': song.get('info', ''),
                        'tape': song.get('tape', False)  # True if from a cover/tape
                    })
            
            setlists.append({
                'id': setlist.get('id'),
                'event_date': setlist.get('eventDate'),  # Format: dd-MM-yyyy
                'artist': setlist.get('artist', {}).get('name', ''),
                'venue': {
                    'name': venue.get('name', ''),
                    'city': city.get('name', ''),
                    'state': city.get('state', ''),
                    'country': city.get('country', {}).get('name', '')
                },
                'tour': setlist.get('tour', {}).get('name', ''),
                'info': setlist.get('info', ''),
                'url': setlist.get('url', ''),
                'songs': songs,
                'song_count': len(songs)
            })
        
        return jsonify({
            'setlists': setlists,
            'count': len(setlists),
            'page': data.get('page', 1),
            'total_pages': data.get('total', 0) // data.get('itemsPerPage', 20) + 1
        }), 200
        
    except requests.RequestException as e:
        return jsonify({'error': 'Failed to connect to Setlist.fm', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Failed to get setlists', 'details': str(e)}), 500


@external_api.route('/setlists/<setlist_id>', methods=['GET'])
@jwt_required()
def get_setlist_details(setlist_id):
    """
    Get detailed setlist information by setlist ID
    Returns: complete setlist with songs, venue, date, etc.
    """
    if not SETLISTFM_API_KEY:
        return jsonify({'error': 'Setlist.fm API not configured'}), 503
    
    try:
        headers = {
            'Accept': 'application/json',
            'x-api-key': SETLISTFM_API_KEY
        }
        
        response = requests.get(
            f'{SETLISTFM_BASE_URL}/setlist/{setlist_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 404:
            return jsonify({'error': 'Setlist not found'}), 404
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to get setlist details', 'status': response.status_code}), 500
        
        setlist = response.json()
        venue = setlist.get('venue', {})
        city = venue.get('city', {})
        
        # Extract all songs from all sets
        songs = []
        set_number = 1
        for set_item in setlist.get('sets', {}).get('set', []):
            # Handle encores and named sets
            set_name = set_item.get('name', f'Set {set_number}')
            
            for song in set_item.get('song', []):
                songs.append({
                    'name': song.get('name', ''),
                    'info': song.get('info', ''),
                    'tape': song.get('tape', False),
                    'set_name': set_name
                })
            set_number += 1
        
        setlist_details = {
            'id': setlist.get('id'),
            'event_date': setlist.get('eventDate'),
            'artist': {
                'mbid': setlist.get('artist', {}).get('mbid'),
                'name': setlist.get('artist', {}).get('name', ''),
                'sort_name': setlist.get('artist', {}).get('sortName', '')
            },
            'venue': {
                'name': venue.get('name', ''),
                'city': city.get('name', ''),
                'state': city.get('state', ''),
                'state_code': city.get('stateCode', ''),
                'country': city.get('country', {}).get('name', ''),
                'country_code': city.get('country', {}).get('code', ''),
                'coordinates': venue.get('city', {}).get('coords', {})
            },
            'tour': setlist.get('tour', {}).get('name', ''),
            'info': setlist.get('info', ''),
            'url': setlist.get('url', ''),
            'songs': songs,
            'song_count': len(songs)
        }
        
        return jsonify(setlist_details), 200
        
    except requests.RequestException as e:
        return jsonify({'error': 'Failed to connect to Setlist.fm', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Failed to get setlist details', 'details': str(e)}), 500


# Health check for external APIs
@external_api.route('/health', methods=['GET'])
def health_check():
    """Check status of external API integrations"""
    return jsonify({
        'google_places': 'configured' if gmaps else 'not configured',
        'setlistfm': 'configured' if SETLISTFM_API_KEY else 'not configured'
    }), 200
