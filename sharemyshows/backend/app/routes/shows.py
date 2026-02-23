"""
Shows routes for concert management
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from app import db
from app.models.show import Show
from app.models.artist import Artist
from app.models.venue import Venue
from app.utils.validators import sanitize_input
from app.utils.auth import get_current_user

shows_bp = Blueprint('shows', __name__)


@shows_bp.route('', methods=['GET'])
def get_shows():
    """
    Get list of shows with pagination and filtering
    
    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20, max: 100)
        user_id (int): Filter by user ID
        is_public (bool): Filter by public/private
        is_past (bool): Filter by past/upcoming shows
        artist_id (int): Filter by artist ID
        venue_id (int): Filter by venue ID
    
    Returns:
        200: List of shows with pagination metadata
    """
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    # Build query
    query = Show.query
    
    # Apply filters
    user_id = request.args.get('user_id', type=int)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    is_public = request.args.get('is_public')
    if is_public is not None:
        is_public = is_public.lower() == 'true'
        query = query.filter_by(is_public=is_public)
    
    is_past = request.args.get('is_past')
    if is_past is not None:
        is_past = is_past.lower() == 'true'
        query = query.filter_by(is_past=is_past)
    
    artist_id = request.args.get('artist_id', type=int)
    if artist_id:
        query = query.join(Show.artists).filter(Artist.id == artist_id)
    
    venue_id = request.args.get('venue_id', type=int)
    if venue_id:
        query = query.filter_by(venue_id=venue_id)
    
    # Order by date (newest first)
    query = query.order_by(Show.show_date.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'shows': [show.to_dict() for show in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@shows_bp.route('/<int:show_id>', methods=['GET'])
def get_show(show_id):
    """
    Get single show by ID
    
    Returns:
        200: Show details
        404: Show not found
        403: Private show, access denied
    """
    show = Show.query.get_or_404(show_id)
    
    # Check if user can view this show
    current_user = get_current_user()
    user_id = current_user.id if current_user else None
    
    if not show.can_be_viewed_by(user_id):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to view this show'
        }), 403
    
    return jsonify({
        'show': show.to_dict(include_user=True)
    }), 200


@shows_bp.route('', methods=['POST'])
@jwt_required()
def create_show():
    """
    Create a new show
    
    Request Body:
        {
            "venue_id": 1,
            "show_date": "2024-12-31",
            "show_time": "20:00:00",  (optional)
            "title": "New Year's Eve Concert",  (optional)
            "notes": "Great show!",  (optional)
            "is_public": true,  (optional, default: true)
            "artist_ids": [1, 2, 3]  (list of artist IDs)
        }
    
    Returns:
        201: Show created successfully
        400: Validation error
        404: Venue or artist not found
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    if not all(k in data for k in ('venue_id', 'show_date', 'artist_ids')):
        return jsonify({
            'error': 'Validation Error',
            'message': 'venue_id, show_date, and artist_ids are required'
        }), 400
    
    # Validate venue exists
    venue = Venue.query.get(data['venue_id'])
    if not venue:
        return jsonify({
            'error': 'Not Found',
            'message': 'Venue not found'
        }), 404
    
    # Validate date format
    try:
        show_date = datetime.strptime(data['show_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Invalid date format. Use YYYY-MM-DD'
        }), 400
    
    # Validate time format if provided
    show_time = None
    if 'show_time' in data and data['show_time']:
        try:
            show_time = datetime.strptime(data['show_time'], '%H:%M:%S').time()
        except ValueError:
            return jsonify({
                'error': 'Validation Error',
                'message': 'Invalid time format. Use HH:MM:SS'
            }), 400
    
    # Validate artists
    artist_ids = data.get('artist_ids', [])
    if not artist_ids:
        return jsonify({
            'error': 'Validation Error',
            'message': 'At least one artist is required'
        }), 400
    
    artists = Artist.query.filter(Artist.id.in_(artist_ids)).all()
    if len(artists) != len(artist_ids):
        return jsonify({
            'error': 'Not Found',
            'message': 'One or more artists not found'
        }), 404
    
    # Create show
    show = Show(
        user_id=user_id,
        venue_id=data['venue_id'],
        show_date=show_date,
        show_time=show_time,
        title=sanitize_input(data.get('title'), max_length=255),
        notes=sanitize_input(data.get('notes')),
        is_public=data.get('is_public', True)
    )
    
    # Add artists
    show.artists = artists
    
    # Check if past
    show.check_if_past()
    
    try:
        db.session.add(show)
        db.session.commit()
        
        return jsonify({
            'message': 'Show created successfully',
            'show': show.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Server Error',
            'message': 'Failed to create show'
        }), 500


@shows_bp.route('/<int:show_id>', methods=['PUT'])
@jwt_required()
def update_show(show_id):
    """
    Update an existing show
    
    Returns:
        200: Show updated successfully
        403: Not authorized to edit this show
        404: Show not found
    """
    user_id = get_jwt_identity()
    show = Show.query.get_or_404(show_id)
    
    # Check if user owns this show
    if not show.can_be_edited_by(user_id):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to edit this show'
        }), 403
    
    data = request.get_json()
    
    # Update venue if provided
    if 'venue_id' in data:
        venue = Venue.query.get(data['venue_id'])
        if not venue:
            return jsonify({
                'error': 'Not Found',
                'message': 'Venue not found'
            }), 404
        show.venue_id = data['venue_id']
    
    # Update date if provided
    if 'show_date' in data:
        try:
            show.show_date = datetime.strptime(data['show_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'error': 'Validation Error',
                'message': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
    
    # Update time if provided
    if 'show_time' in data:
        if data['show_time']:
            try:
                show.show_time = datetime.strptime(data['show_time'], '%H:%M:%S').time()
            except ValueError:
                return jsonify({
                    'error': 'Validation Error',
                    'message': 'Invalid time format. Use HH:MM:SS'
                }), 400
        else:
            show.show_time = None
    
    # Update artists if provided
    if 'artist_ids' in data:
        artist_ids = data['artist_ids']
        artists = Artist.query.filter(Artist.id.in_(artist_ids)).all()
        if len(artists) != len(artist_ids):
            return jsonify({
                'error': 'Not Found',
                'message': 'One or more artists not found'
            }), 404
        show.artists = artists
    
    # Update other fields
    if 'title' in data:
        show.title = sanitize_input(data['title'], max_length=255)
    
    if 'notes' in data:
        show.notes = sanitize_input(data['notes'])
    
    if 'is_public' in data:
        show.is_public = data['is_public']
    
    # Update past status
    show.check_if_past()
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Show updated successfully',
            'show': show.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Server Error',
            'message': 'Failed to update show'
        }), 500


@shows_bp.route('/<int:show_id>', methods=['DELETE'])
@jwt_required()
def delete_show(show_id):
    """
    Delete a show
    
    Returns:
        200: Show deleted successfully
        403: Not authorized to delete this show
        404: Show not found
    """
    user_id = get_jwt_identity()
    show = Show.query.get_or_404(show_id)
    
    # Check if user owns this show
    if not show.can_be_edited_by(user_id):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to delete this show'
        }), 403
    
    try:
        db.session.delete(show)
        db.session.commit()
        
        return jsonify({
            'message': 'Show deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Server Error',
            'message': 'Failed to delete show'
        }), 500


@shows_bp.route('/my-shows', methods=['GET'])
@jwt_required()
def get_my_shows():
    """
    Get current user's shows with pagination
    
    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20)
        is_past (bool): Filter by past/upcoming
    
    Returns:
        200: User's shows with pagination
    """
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    query = Show.query.filter_by(user_id=user_id)
    
    # Filter by past/upcoming if specified
    is_past = request.args.get('is_past')
    if is_past is not None:
        is_past = is_past.lower() == 'true'
        query = query.filter_by(is_past=is_past)
    
    query = query.order_by(Show.show_date.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'shows': [show.to_dict() for show in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200
