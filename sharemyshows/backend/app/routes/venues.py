"""
Venues routes for managing concert venues
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.venue import Venue
from app.utils.validators import sanitize_input

venues_bp = Blueprint('venues', __name__)


@venues_bp.route('', methods=['GET'])
def get_venues():
    """
    Get list of venues with pagination and search
    
    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20, max: 100)
        search (str): Search venues by name or location
        city (str): Filter by city
        state (str): Filter by state
        country (str): Filter by country
    
    Returns:
        200: List of venues with pagination metadata
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    search = request.args.get('search', '').strip()
    city = request.args.get('city', '').strip()
    state = request.args.get('state', '').strip()
    country = request.args.get('country', '').strip()
    
    query = Venue.query
    
    # Search by name or location
    if search:
        query = query.filter(
            db.or_(
                Venue.name.ilike(f'%{search}%'),
                Venue.location.ilike(f'%{search}%')
            )
        )
    
    # Filter by city
    if city:
        query = query.filter(Venue.city.ilike(f'%{city}%'))
    
    # Filter by state
    if state:
        query = query.filter(Venue.state.ilike(f'%{state}%'))
    
    # Filter by country
    if country:
        query = query.filter(Venue.country.ilike(f'%{country}%'))
    
    # Order alphabetically by name
    query = query.order_by(Venue.name.asc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'venues': [venue.to_dict() for venue in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@venues_bp.route('/<int:venue_id>', methods=['GET'])
def get_venue(venue_id):
    """
    Get single venue by ID with its shows
    
    Returns:
        200: Venue details
        404: Venue not found
    """
    venue = Venue.query.get_or_404(venue_id)
    
    # Get venue's shows (limited to 10 most recent)
    shows = venue.shows.order_by(db.desc('show_date')).limit(10).all()
    
    response = venue.to_dict()
    response['shows'] = [show.to_dict(include_user=True, include_venue=False) for show in shows]
    response['total_shows'] = venue.shows.count()
    
    return jsonify(response), 200


@venues_bp.route('', methods=['POST'])
@jwt_required()
def create_venue():
    """
    Create a new venue
    
    Request Body:
        {
            "name": "Venue Name",
            "location": "123 Main St, City, State",
            "city": "City",  (optional)
            "state": "State",  (optional)
            "country": "Country",  (optional)
            "latitude": 40.7128,  (optional)
            "longitude": -74.0060  (optional)
        }
    
    Returns:
        201: Venue created successfully
        400: Validation error
    """
    data = request.get_json()
    
    # Validate required fields
    if not all(k in data for k in ('name', 'location')):
        return jsonify({
            'error': 'Validation Error',
            'message': 'name and location are required'
        }), 400
    
    name = sanitize_input(data['name'], max_length=255)
    location = sanitize_input(data['location'], max_length=512)
    
    if not name or not location:
        return jsonify({
            'error': 'Validation Error',
            'message': 'name and location cannot be empty'
        }), 400
    
    # Create venue
    venue = Venue(
        name=name,
        location=location,
        city=sanitize_input(data.get('city'), max_length=100),
        state=sanitize_input(data.get('state'), max_length=100),
        country=sanitize_input(data.get('country'), max_length=100),
        latitude=data.get('latitude'),
        longitude=data.get('longitude')
    )
    
    # Validate coordinates if provided
    if venue.latitude is not None or venue.longitude is not None:
        if venue.latitude is None or venue.longitude is None:
            return jsonify({
                'error': 'Validation Error',
                'message': 'Both latitude and longitude must be provided'
            }), 400
        
        try:
            lat = float(venue.latitude)
            lng = float(venue.longitude)
            
            if not (-90 <= lat <= 90):
                return jsonify({
                    'error': 'Validation Error',
                    'message': 'Latitude must be between -90 and 90'
                }), 400
            
            if not (-180 <= lng <= 180):
                return jsonify({
                    'error': 'Validation Error',
                    'message': 'Longitude must be between -180 and 180'
                }), 400
                
        except (ValueError, TypeError):
            return jsonify({
                'error': 'Validation Error',
                'message': 'Invalid latitude or longitude format'
            }), 400
    
    try:
        db.session.add(venue)
        db.session.commit()
        
        return jsonify({
            'message': 'Venue created successfully',
            'venue': venue.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Server Error',
            'message': 'Failed to create venue'
        }), 500


@venues_bp.route('/search', methods=['GET'])
def search_venues():
    """
    Search venues by name or location (for autocomplete)
    
    Query Parameters:
        q (str): Search query
        limit (int): Maximum results (default: 10, max: 50)
    
    Returns:
        200: List of matching venues
    """
    query = request.args.get('q', '').strip()
    limit = min(request.args.get('limit', 10, type=int), 50)
    
    if not query:
        return jsonify({
            'venues': []
        }), 200
    
    # Search for venues matching the query
    venues = Venue.query.filter(
        db.or_(
            Venue.name.ilike(f'%{query}%'),
            Venue.location.ilike(f'%{query}%'),
            Venue.city.ilike(f'%{query}%')
        )
    ).order_by(Venue.name.asc()).limit(limit).all()
    
    return jsonify({
        'venues': [venue.to_dict() for venue in venues]
    }), 200


@venues_bp.route('/nearby', methods=['GET'])
def get_nearby_venues():
    """
    Get venues near a location (for Phase 5: location-based features)
    
    Query Parameters:
        latitude (float): Current latitude
        longitude (float): Current longitude
        radius (float): Search radius in kilometers (default: 10, max: 100)
        limit (int): Maximum results (default: 20, max: 100)
    
    Returns:
        200: List of nearby venues
        400: Invalid coordinates
    """
    try:
        latitude = float(request.args.get('latitude'))
        longitude = float(request.args.get('longitude'))
    except (TypeError, ValueError):
        return jsonify({
            'error': 'Validation Error',
            'message': 'Valid latitude and longitude are required'
        }), 400
    
    radius = min(float(request.args.get('radius', 10)), 100)
    limit = min(int(request.args.get('limit', 20)), 100)
    
    # Validate coordinates
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        return jsonify({
            'error': 'Validation Error',
            'message': 'Invalid coordinates'
        }), 400
    
    # Get venues with coordinates
    # Note: For production, use PostGIS or a proper geospatial query
    # This is a simplified version using Haversine formula
    venues = Venue.query.filter(
        Venue.latitude.isnot(None),
        Venue.longitude.isnot(None)
    ).all()
    
    # Calculate distances and filter
    from math import radians, cos, sin, asin, sqrt
    
    def haversine(lon1, lat1, lon2, lat2):
        """Calculate distance between two points on Earth"""
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c  # Radius of Earth in kilometers
        return km
    
    nearby = []
    for venue in venues:
        distance = haversine(
            longitude,
            latitude,
            float(venue.longitude),
            float(venue.latitude)
        )
        
        if distance <= radius:
            venue_dict = venue.to_dict()
            venue_dict['distance_km'] = round(distance, 2)
            nearby.append(venue_dict)
    
    # Sort by distance and limit results
    nearby.sort(key=lambda x: x['distance_km'])
    nearby = nearby[:limit]
    
    return jsonify({
        'venues': nearby,
        'search_params': {
            'latitude': latitude,
            'longitude': longitude,
            'radius_km': radius
        }
    }), 200
