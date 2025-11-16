from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Show, Artist, Venue, SetlistSong, ShowCheckin
from datetime import datetime, time as dt_time

shows_bp = Blueprint('shows', __name__, url_prefix='/api/shows')

@shows_bp.route('', methods=['GET'])
@jwt_required()
def get_shows():
    """Get all shows for the current user"""
    user_id = int(get_jwt_identity())
    
    artist_id = request.args.get('artist_id', type=int)
    venue_id = request.args.get('venue_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Show.query.filter_by(user_id=user_id)
    
    if artist_id:
        query = query.filter_by(artist_id=artist_id)
    if venue_id:
        query = query.filter_by(venue_id=venue_id)
    if start_date:
        query = query.filter(Show.date >= datetime.fromisoformat(start_date).date())
    if end_date:
        query = query.filter(Show.date <= datetime.fromisoformat(end_date).date())
    
    shows = query.order_by(Show.date.desc()).all()
    
    return jsonify([show.to_dict() for show in shows]), 200

@shows_bp.route('/<int:show_id>', methods=['GET'])
@jwt_required()
def get_show(show_id):
    """Get a specific show with full details"""
    user_id = int(get_jwt_identity())
    show = Show.query.filter_by(id=show_id, user_id=user_id).first()
    
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    return jsonify(show.to_dict(include_details=True)), 200

@shows_bp.route('', methods=['POST'])
@jwt_required()
def create_show():
    """Create a new show"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data or not all(k in data for k in ('artist_name', 'venue_name', 'date')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    artist = Artist.query.filter_by(name=data['artist_name']).first()
    if not artist:
        artist = Artist(name=data['artist_name'])
        db.session.add(artist)
        db.session.flush()
    
    venue = Venue.query.filter_by(name=data['venue_name']).first()
    if not venue:
        venue = Venue(
            name=data['venue_name'],
            location=data.get('venue_location', ''),
            place_id=data.get('place_id'),
            address=data.get('address'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude')
        )
        db.session.add(venue)
        db.session.flush()
    
    try:
        show_date = datetime.fromisoformat(data['date']).date()
        show_time = None
        if 'time' in data and data['time']:
            time_parts = data['time'].split(':')
            show_time = dt_time(int(time_parts[0]), int(time_parts[1]))
    except (ValueError, IndexError) as e:
        return jsonify({'error': 'Invalid date or time format'}), 400
    
    show = Show(
        user_id=user_id,
        artist_id=artist.id,
        venue_id=venue.id,
        date=show_date,
        time=show_time,
        notes=data.get('notes', '')
    )
    
    try:
        db.session.add(show)
        db.session.commit()
        return jsonify(show.to_dict(include_details=True)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create show', 'details': str(e)}), 500

@shows_bp.route('/<int:show_id>', methods=['PUT'])
@jwt_required()
def update_show(show_id):
    """Update a show"""
    user_id = int(get_jwt_identity())
    show = Show.query.filter_by(id=show_id, user_id=user_id).first()
    
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    data = request.get_json()
    
    if 'date' in data:
        try:
            show.date = datetime.fromisoformat(data['date']).date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    
    if 'time' in data and data['time']:
        try:
            time_parts = data['time'].split(':')
            show.time = dt_time(int(time_parts[0]), int(time_parts[1]))
        except (ValueError, IndexError):
            return jsonify({'error': 'Invalid time format'}), 400
    
    if 'notes' in data:
        show.notes = data['notes']
    
    try:
        db.session.commit()
        return jsonify(show.to_dict(include_details=True)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update show', 'details': str(e)}), 500

@shows_bp.route('/<int:show_id>', methods=['DELETE'])
@jwt_required()
def delete_show(show_id):
    """Delete a show"""
    user_id = int(get_jwt_identity())
    show = Show.query.filter_by(id=show_id, user_id=user_id).first()
    
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    try:
        db.session.delete(show)
        db.session.commit()
        return jsonify({'message': 'Show deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete show', 'details': str(e)}), 500

@shows_bp.route('/<int:show_id>/setlist', methods=['GET'])
@jwt_required()
def get_setlist(show_id):
    """Get setlist for a show"""
    user_id = int(get_jwt_identity())
    show = Show.query.filter_by(id=show_id, user_id=user_id).first()
    
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    songs = show.setlist_songs.all()
    return jsonify([song.to_dict() for song in songs]), 200

@shows_bp.route('/<int:show_id>/setlist', methods=['POST'])
@jwt_required()
def add_setlist_song(show_id):
    """Add a song to the setlist"""
    user_id = int(get_jwt_identity())
    show = Show.query.filter_by(id=show_id, user_id=user_id).first()
    
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    data = request.get_json()
    
    if not data or 'title' not in data:
        return jsonify({'error': 'Missing song title'}), 400
    
    max_order = db.session.query(db.func.max(SetlistSong.order)).filter_by(show_id=show_id).scalar() or 0
    
    song = SetlistSong(
        show_id=show_id,
        title=data['title'],
        order=data.get('order', max_order + 1),
        notes=data.get('notes', '')
    )
    
    try:
        db.session.add(song)
        db.session.commit()
        return jsonify(song.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add song', 'details': str(e)}), 500

@shows_bp.route('/<int:show_id>/setlist/<int:song_id>', methods=['PUT'])
@jwt_required()
def update_setlist_song(show_id, song_id):
    """Update a setlist song"""
    user_id = int(get_jwt_identity())
    show = Show.query.filter_by(id=show_id, user_id=user_id).first()
    
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    song = SetlistSong.query.filter_by(id=song_id, show_id=show_id).first()
    
    if not song:
        return jsonify({'error': 'Song not found'}), 404
    
    data = request.get_json()
    
    if 'title' in data:
        song.title = data['title']
    if 'order' in data:
        song.order = data['order']
    if 'notes' in data:
        song.notes = data['notes']
    
    try:
        db.session.commit()
        return jsonify(song.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update song', 'details': str(e)}), 500

@shows_bp.route('/<int:show_id>/setlist/<int:song_id>', methods=['DELETE'])
@jwt_required()
def delete_setlist_song(show_id, song_id):
    """Delete a setlist song"""
    user_id = int(get_jwt_identity())
    show = Show.query.filter_by(id=show_id, user_id=user_id).first()
    
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    song = SetlistSong.query.filter_by(id=song_id, show_id=show_id).first()
    
    if not song:
        return jsonify({'error': 'Song not found'}), 404
    
    try:
        db.session.delete(song)
        db.session.commit()
        return jsonify({'message': 'Song deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete song', 'details': str(e)}), 500

@shows_bp.route('/<int:show_id>/checkin', methods=['POST'])
@jwt_required()
def checkin_to_show(show_id):
    """Check in to a show"""
    user_id = int(get_jwt_identity())
    show = Show.query.get(show_id)
    
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    existing_checkin = ShowCheckin.query.filter_by(
        user_id=user_id,
        show_id=show_id,
        is_active=True
    ).first()
    
    if existing_checkin:
        return jsonify({'message': 'Already checked in', 'checkin': existing_checkin.to_dict()}), 200
    
    checkin = ShowCheckin(
        user_id=user_id,
        show_id=show_id
    )
    
    try:
        db.session.add(checkin)
        db.session.commit()
        return jsonify(checkin.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to check in', 'details': str(e)}), 500

@shows_bp.route('/<int:show_id>/checkout', methods=['POST'])
@jwt_required()
def checkout_from_show(show_id):
    """Check out from a show"""
    user_id = int(get_jwt_identity())
    
    checkin = ShowCheckin.query.filter_by(
        user_id=user_id,
        show_id=show_id,
        is_active=True
    ).first()
    
    if not checkin:
        return jsonify({'error': 'Not checked in to this show'}), 404
    
    checkin.checked_out_at = datetime.utcnow()
    checkin.is_active = False
    
    try:
        db.session.commit()
        return jsonify({'message': 'Checked out successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to check out', 'details': str(e)}), 500

@shows_bp.route('/<int:show_id>/active-users', methods=['GET'])
@jwt_required()
def get_active_users(show_id):
    """Get users currently checked in to a show"""
    show = Show.query.get(show_id)
    
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    active_checkins = ShowCheckin.query.filter_by(
        show_id=show_id,
        is_active=True
    ).all()
    
    return jsonify([checkin.to_dict() for checkin in active_checkins]), 200
