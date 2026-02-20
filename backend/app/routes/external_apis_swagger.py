"""
External API Integration Routes with Swagger Documentation
Handles Google Places API and Setlist.fm API integrations
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
import googlemaps
import requests
import os

# Create API namespace
api = Namespace('external', description='External API integrations (Google Places, Setlist.fm)')

# Initialize clients
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
SETLISTFM_API_KEY = os.getenv('SETLISTFM_API_KEY')
SETLISTFM_BASE_URL = 'https://api.setlist.fm/rest/1.0'

gmaps = None
if GOOGLE_PLACES_API_KEY:
    try:
        gmaps = googlemaps.Client(key=GOOGLE_PLACES_API_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize Google Maps client: {e}")

# ===== API MODELS (for Swagger documentation) =====

# Google Places Models
venue_location = api.model('VenueLocation', {
    'lat': fields.Float(description='Latitude'),
    'lng': fields.Float(description='Longitude')
})

venue_search_result = api.model('VenueSearchResult', {
    'place_id': fields.String(description='Google Place ID'),
    'name': fields.String(description='Venue name'),
    'formatted_address': fields.String(description='Full address'),
    'location': fields.Nested(venue_location),
    'types': fields.List(fields.String, description='Place types'),
    'rating': fields.Float(description='Google rating'),
    'user_ratings_total': fields.Integer(description='Number of ratings')
})

venue_autocomplete_result = api.model('VenueAutocompleteResult', {
    'place_id': fields.String(description='Google Place ID'),
    'description': fields.String(description='Full description'),
    'main_text': fields.String(description='Main text (venue name)'),
    'secondary_text': fields.String(description='Secondary text (location)'),
    'types': fields.List(fields.String, description='Place types')
})

venue_photo = api.model('VenuePhoto', {
    'photo_reference': fields.String(description='Photo reference ID'),
    'width': fields.Integer(description='Photo width'),
    'height': fields.Integer(description='Photo height')
})

venue_details = api.model('VenueDetails', {
    'place_id': fields.String(description='Google Place ID'),
    'name': fields.String(description='Venue name'),
    'formatted_address': fields.String(description='Full address'),
    'location': fields.String(description='City, State'),
    'latitude': fields.Float(description='Latitude'),
    'longitude': fields.Float(description='Longitude'),
    'phone': fields.String(description='Phone number'),
    'website': fields.String(description='Website URL'),
    'rating': fields.Float(description='Google rating'),
    'user_ratings_total': fields.Integer(description='Number of ratings'),
    'types': fields.List(fields.String, description='Place types'),
    'photos': fields.List(fields.Nested(venue_photo)),
    'google_maps_url': fields.String(description='Google Maps URL'),
    'city': fields.String(description='City'),
    'state': fields.String(description='State'),
    'country': fields.String(description='Country')
})

# Setlist.fm Models
artist_result = api.model('ArtistResult', {
    'mbid': fields.String(description='MusicBrainz ID'),
    'name': fields.String(description='Artist name'),
    'sort_name': fields.String(description='Sort name'),
    'disambiguation': fields.String(description='Disambiguation'),
    'url': fields.String(description='Setlist.fm URL')
})

setlist_song = api.model('SetlistSong', {
    'name': fields.String(description='Song name'),
    'info': fields.String(description='Additional info'),
    'tape': fields.Boolean(description='Is from tape/cover'),
    'set_name': fields.String(description='Set name (Set 1, Encore, etc.)')
})

setlist_venue = api.model('SetlistVenue', {
    'name': fields.String(description='Venue name'),
    'city': fields.String(description='City'),
    'state': fields.String(description='State'),
    'country': fields.String(description='Country')
})

setlist_result = api.model('SetlistResult', {
    'id': fields.String(description='Setlist ID'),
    'event_date': fields.String(description='Event date (dd-MM-yyyy)'),
    'artist': fields.String(description='Artist name'),
    'venue': fields.Nested(setlist_venue),
    'tour': fields.String(description='Tour name'),
    'info': fields.String(description='Additional info'),
    'url': fields.String(description='Setlist.fm URL'),
    'songs': fields.List(fields.Nested(setlist_song)),
    'song_count': fields.Integer(description='Number of songs')
})

# ===== GOOGLE PLACES API ENDPOINTS =====

@api.route('/venues/search')
class VenueSearch(Resource):
    @api.doc('search_venues',
             security='jwt',
             params={
                 'query': 'Search query (minimum 2 characters)',
                 'location': 'Location bias (lat,lng) - optional',
                 'radius': 'Search radius in meters - optional'
             })
    @api.marshal_list_with(venue_search_result, envelope='venues')
    @jwt_required()
    def get(self):
        """Search for concert venues using Google Places API"""
        print(f"DEBUG: Venue search called, gmaps={gmaps is not None}")
        if not gmaps:
            api.abort(503, 'Google Places API not configured')

        query = request.args.get('query')
        print(f"DEBUG: Query={query}")
        if not query or len(query) < 2:
            api.abort(400, 'Query must be at least 2 characters')

        try:
            results = gmaps.places(
                query=f"{query} concert venue music hall amphitheater",
                type='establishment'
            )
            print(f"DEBUG: Got {len(results.get('results', []))} results from Google")

            venues = []
            for place in results.get('results', [])[:10]:
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

            print(f"DEBUG: Returning {len(venues)} venues")
            # Return just the list - the envelope decorator will wrap it
            return venues

        except Exception as e:
            print(f"DEBUG ERROR: {type(e).__name__}: {str(e)}")
            api.abort(500, f'Failed to search venues: {str(e)}')


@api.route('/venues/autocomplete')
class VenueAutocomplete(Resource):
    @api.doc('autocomplete_venues',
             security='jwt',
             params={
                 'input': 'Search input (minimum 2 characters)',
                 'location': 'Location bias (lat,lng) - optional'
             })
    @api.marshal_list_with(venue_autocomplete_result, envelope='suggestions')
    @jwt_required()
    def get(self):
        """Get venue autocomplete suggestions as user types"""
        if not gmaps:
            api.abort(503, 'Google Places API not configured')

        input_text = request.args.get('input')
        if not input_text or len(input_text) < 2:
            api.abort(400, 'Input must be at least 2 characters')

        try:
            location = request.args.get('location')
            autocomplete_params = {
                'input_text': input_text,
                'types': 'establishment'
            }

            if location:
                try:
                    lat, lng = map(float, location.split(','))
                    autocomplete_params['location'] = (lat, lng)
                    autocomplete_params['radius'] = 50000
                except ValueError:
                    pass

            results = gmaps.places_autocomplete(**autocomplete_params)

            suggestions = []
            for prediction in results[:10]:
                suggestions.append({
                    'place_id': prediction['place_id'],
                    'description': prediction['description'],
                    'main_text': prediction['structured_formatting']['main_text'],
                    'secondary_text': prediction['structured_formatting'].get('secondary_text', ''),
                    'types': prediction.get('types', [])
                })

            # Return just the list - the envelope decorator will wrap it
            return suggestions

        except Exception as e:
            api.abort(500, f'Failed to get autocomplete suggestions: {str(e)}')


@api.route('/venues/details/<string:place_id>')
class VenueDetails(Resource):
    @api.doc('get_venue_details',
             security='jwt',
             params={'place_id': 'Google Place ID'})
    @api.marshal_with(venue_details)
    @jwt_required()
    def get(self, place_id):
        """Get detailed information about a venue by place_id"""
        if not gmaps:
            api.abort(503, 'Google Places API not configured')
        
        try:
            place = gmaps.place(
                place_id=place_id,
                fields=[
                    'name', 'formatted_address', 'geometry', 'formatted_phone_number',
                    'website', 'rating', 'user_ratings_total', 'photo', 'type',
                    'address_component', 'url'
                ]
            )
            
            result = place.get('result', {})
            location = result.get('geometry', {}).get('location', {})
            address_components = result.get('address_components', result.get('address_component', []))

            city = state = country = ''
            for component in address_components:
                comp_types = component.get('types', component.get('type', []))
                if 'locality' in comp_types:
                    city = component['long_name']
                elif 'administrative_area_level_1' in comp_types:
                    state = component['short_name']
                elif 'country' in comp_types:
                    country = component['long_name']

            photos = []
            raw_photos = result.get('photos', result.get('photo', []))
            for photo in (raw_photos or [])[:5]:
                photos.append({
                    'photo_reference': photo.get('photo_reference', ''),
                    'width': photo.get('width', 0),
                    'height': photo.get('height', 0)
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
                'types': result.get('types', result.get('type', [])),
                'photos': photos,
                'google_maps_url': result.get('url'),
                'city': city,
                'state': state,
                'country': country
            }
            
            return venue_details
            
        except Exception as e:
            api.abort(500, f'Failed to get venue details: {str(e)}')


@api.route('/venues/photo/<string:photo_reference>')
class VenuePhoto(Resource):
    @api.doc('get_venue_photo',
             security='jwt',
             params={
                 'photo_reference': 'Google photo reference ID',
                 'max_width': 'Maximum width in pixels (default 400)'
             })
    @jwt_required()
    def get(self, photo_reference):
        """Get a venue photo URL by photo_reference"""
        if not gmaps:
            api.abort(503, 'Google Places API not configured')
        
        max_width = request.args.get('max_width', 400, type=int)
        
        try:
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photo_reference={photo_reference}&key={GOOGLE_PLACES_API_KEY}"
            return {'photo_url': photo_url}
        except Exception as e:
            api.abort(500, f'Failed to get photo: {str(e)}')


# ===== SETLIST.FM API ENDPOINTS =====

@api.route('/artists/search')
class ArtistSearch(Resource):
    @api.doc('search_artists',
             security='jwt',
             params={
                 'query': 'Artist name (minimum 2 characters)',
                 'sort': 'Sort method: relevance or sortName'
             })
    @api.marshal_list_with(artist_result, envelope='artists')
    @jwt_required()
    def get(self):
        """Search for artists on Setlist.fm"""
        if not SETLISTFM_API_KEY:
            api.abort(503, 'Setlist.fm API not configured')

        query = request.args.get('query')
        if not query or len(query) < 2:
            api.abort(400, 'Query must be at least 2 characters')

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
                return []

            data = response.json()
            artists = []

            for artist in data.get('artist', [])[:15]:
                artists.append({
                    'mbid': artist['mbid'],
                    'name': artist['name'],
                    'sort_name': artist.get('sortName', ''),
                    'disambiguation': artist.get('disambiguation', ''),
                    'url': artist.get('url', '')
                })

            return artists

        except requests.RequestException:
            return []
        except Exception:
            return []


@api.route('/artists/<string:mbid>')
class ArtistDetails(Resource):
    @api.doc('get_artist_details',
             security='jwt',
             params={'mbid': 'MusicBrainz ID'})
    @api.marshal_with(artist_result)
    @jwt_required()
    def get(self, mbid):
        """Get artist details by MusicBrainz ID"""
        if not SETLISTFM_API_KEY:
            api.abort(503, 'Setlist.fm API not configured')
        
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
                api.abort(404, 'Artist not found')
            
            if response.status_code != 200:
                api.abort(500, 'Failed to get artist details')
            
            artist = response.json()
            
            return {
                'mbid': artist['mbid'],
                'name': artist['name'],
                'sort_name': artist.get('sortName', ''),
                'disambiguation': artist.get('disambiguation', ''),
                'url': artist.get('url', '')
            }
            
        except requests.RequestException as e:
            api.abort(500, f'Failed to connect to Setlist.fm: {str(e)}')
        except Exception as e:
            api.abort(500, f'Failed to get artist details: {str(e)}')


@api.route('/artists/<string:mbid>/setlists')
class ArtistSetlists(Resource):
    @api.doc('get_artist_setlists',
             security='jwt',
             params={
                 'mbid': 'MusicBrainz ID',
                 'page': 'Page number (default 1)'
             })
    @api.marshal_list_with(setlist_result, envelope='setlists')
    @jwt_required()
    def get(self, mbid):
        """Get setlists for an artist (paginated, 20 per page)"""
        if not SETLISTFM_API_KEY:
            api.abort(503, 'Setlist.fm API not configured')
        
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
                api.abort(500, 'Failed to get setlists')
            
            data = response.json()
            setlists = []
            
            for setlist in data.get('setlist', []):
                venue = setlist.get('venue', {})
                city = venue.get('city', {})
                
                songs = []
                for set_item in setlist.get('sets', {}).get('set', []):
                    for song in set_item.get('song', []):
                        songs.append({
                            'name': song.get('name', ''),
                            'info': song.get('info', ''),
                            'tape': song.get('tape', False)
                        })
                
                setlists.append({
                    'id': setlist.get('id'),
                    'event_date': setlist.get('eventDate'),
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
            
            return {
                'setlists': setlists,
                'count': len(setlists),
                'page': data.get('page', 1),
                'total_pages': data.get('total', 0) // data.get('itemsPerPage', 20) + 1
            }
            
        except requests.RequestException as e:
            api.abort(500, f'Failed to connect to Setlist.fm: {str(e)}')
        except Exception as e:
            api.abort(500, f'Failed to get setlists: {str(e)}')


@api.route('/setlists/<string:setlist_id>')
class SetlistDetails(Resource):
    @api.doc('get_setlist_details',
             security='jwt',
             params={'setlist_id': 'Setlist ID'})
    @api.marshal_with(setlist_result)
    @jwt_required()
    def get(self, setlist_id):
        """Get detailed setlist information by setlist ID"""
        if not SETLISTFM_API_KEY:
            api.abort(503, 'Setlist.fm API not configured')
        
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
                api.abort(404, 'Setlist not found')
            
            if response.status_code != 200:
                api.abort(500, 'Failed to get setlist details')
            
            setlist = response.json()
            venue = setlist.get('venue', {})
            city = venue.get('city', {})
            
            songs = []
            set_number = 1
            for set_item in setlist.get('sets', {}).get('set', []):
                set_name = set_item.get('name', f'Set {set_number}')
                
                for song in set_item.get('song', []):
                    songs.append({
                        'name': song.get('name', ''),
                        'info': song.get('info', ''),
                        'tape': song.get('tape', False),
                        'set_name': set_name
                    })
                set_number += 1
            
            return {
                'id': setlist.get('id'),
                'event_date': setlist.get('eventDate'),
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
            }
            
        except requests.RequestException as e:
            api.abort(500, f'Failed to connect to Setlist.fm: {str(e)}')
        except Exception as e:
            api.abort(500, f'Failed to get setlist details: {str(e)}')


@api.route('/health')
class HealthCheck(Resource):
    @api.doc('health_check')
    def get(self):
        """Check status of external API integrations"""
        return {
            'google_places': 'configured' if gmaps else 'not configured',
            'setlistfm': 'configured' if SETLISTFM_API_KEY else 'not configured'
        }
