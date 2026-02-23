"""
Artists routes for managing performing artists
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.artist import Artist
from app.utils.validators import sanitize_input

artists_bp = Blueprint('artists', __name__)


@artists_bp.route('', methods=['GET'])
def get_artists():
    """
    Get list of artists with pagination and search
    
    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20, max: 100)
        search (str): Search artists by name
    
    Returns:
        200: List of artists with pagination metadata
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    search = request.args.get('search', '').strip()
    
    query = Artist.query
    
    # Search by name if provided
    if search:
        query = query.filter(Artist.name.ilike(f'%{search}%'))
    
    # Order alphabetically
    query = query.order_by(Artist.name.asc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'artists': [artist.to_dict() for artist in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@artists_bp.route('/<int:artist_id>', methods=['GET'])
def get_artist(artist_id):
    """
    Get single artist by ID with their shows
    
    Returns:
        200: Artist details
        404: Artist not found
    """
    artist = Artist.query.get_or_404(artist_id)
    
    # Get artist's shows (limited to 10 most recent)
    shows = artist.shows.order_by(db.desc('show_date')).limit(10).all()
    
    response = artist.to_dict()
    response['shows'] = [show.to_dict(include_user=True, include_artists=False) for show in shows]
    response['total_shows'] = artist.shows.count()
    
    return jsonify(response), 200


@artists_bp.route('', methods=['POST'])
@jwt_required()
def create_artist():
    """
    Create a new artist
    
    Request Body:
        {
            "name": "Artist Name"
        }
    
    Returns:
        201: Artist created successfully
        400: Validation error
        409: Artist already exists
    """
    data = request.get_json()
    
    # Validate required fields
    if 'name' not in data or not data['name'].strip():
        return jsonify({
            'error': 'Validation Error',
            'message': 'Artist name is required'
        }), 400
    
    name = sanitize_input(data['name'], max_length=255)
    
    # Check if artist already exists (case-insensitive)
    existing = Artist.query.filter(Artist.name.ilike(name)).first()
    if existing:
        return jsonify({
            'error': 'Conflict',
            'message': 'Artist already exists',
            'artist': existing.to_dict()
        }), 409
    
    # Create artist
    artist = Artist(name=name)
    
    try:
        db.session.add(artist)
        db.session.commit()
        
        return jsonify({
            'message': 'Artist created successfully',
            'artist': artist.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Server Error',
            'message': 'Failed to create artist'
        }), 500


@artists_bp.route('/search', methods=['GET'])
def search_artists():
    """
    Search artists by name (for autocomplete)
    
    Query Parameters:
        q (str): Search query
        limit (int): Maximum results (default: 10, max: 50)
    
    Returns:
        200: List of matching artists
    """
    query = request.args.get('q', '').strip()
    limit = min(request.args.get('limit', 10, type=int), 50)
    
    if not query:
        return jsonify({
            'artists': []
        }), 200
    
    # Search for artists matching the query
    artists = Artist.query.filter(
        Artist.name.ilike(f'%{query}%')
    ).order_by(Artist.name.asc()).limit(limit).all()
    
    return jsonify({
        'artists': [artist.to_dict() for artist in artists]
    }), 200


@artists_bp.route('/bulk', methods=['POST'])
@jwt_required()
def create_artists_bulk():
    """
    Create multiple artists at once
    
    Request Body:
        {
            "artists": ["Artist 1", "Artist 2", "Artist 3"]
        }
    
    Returns:
        201: Artists created
        400: Validation error
    """
    data = request.get_json()
    
    if 'artists' not in data or not isinstance(data['artists'], list):
        return jsonify({
            'error': 'Validation Error',
            'message': 'artists field must be an array'
        }), 400
    
    artist_names = [sanitize_input(name, max_length=255) for name in data['artists'] if name.strip()]
    
    if not artist_names:
        return jsonify({
            'error': 'Validation Error',
            'message': 'At least one artist name is required'
        }), 400
    
    created = []
    existing = []
    
    for name in artist_names:
        # Check if artist exists
        artist = Artist.query.filter(Artist.name.ilike(name)).first()
        
        if artist:
            existing.append(artist.to_dict())
        else:
            # Create new artist
            artist = Artist(name=name)
            db.session.add(artist)
            created.append(artist)
    
    try:
        db.session.commit()
        
        return jsonify({
            'message': f'Created {len(created)} artists, {len(existing)} already existed',
            'created': [artist.to_dict() for artist in created],
            'existing': existing
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Server Error',
            'message': 'Failed to create artists'
        }), 500
