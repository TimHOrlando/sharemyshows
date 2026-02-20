from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Show, Artist, Venue, Photo, AudioRecording, VideoRecording, Comment
from sqlalchemy import func, desc

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    user_id = int(get_jwt_identity())
    
    shows_count = Show.query.filter_by(user_id=user_id).count()
    
    artists_count = db.session.query(func.count(func.distinct(Show.artist_id))).\
        filter(Show.user_id == user_id).scalar()
    
    venues_count = db.session.query(func.count(func.distinct(Show.venue_id))).\
        filter(Show.user_id == user_id).scalar()
    
    photos_count = Photo.query.filter_by(user_id=user_id).count()
    
    audio_count = AudioRecording.query.filter_by(user_id=user_id).count()
    
    videos_count = VideoRecording.query.filter_by(user_id=user_id).count()
    
    comments_count = Comment.query.filter_by(user_id=user_id).count()
    
    return jsonify({
        'shows': shows_count,
        'artists': artists_count,
        'venues': venues_count,
        'photos': photos_count,
        'audio': audio_count,
        'videos': videos_count,
        'comments': comments_count
    }), 200

@dashboard_bp.route('/artists', methods=['GET'])
@jwt_required()
def get_artist_stats():
    user_id = int(get_jwt_identity())
    
    artist_stats = db.session.query(
        Artist.id,
        Artist.name,
        func.count(Show.id).label('show_count'),
        func.max(Show.date).label('last_seen')
    ).join(Show).filter(
        Show.user_id == user_id
    ).group_by(
        Artist.id, Artist.name
    ).order_by(
        desc('show_count')
    ).all()
    
    result = []
    for artist in artist_stats:
        result.append({
            'id': artist.id,
            'name': artist.name,
            'show_count': artist.show_count,
            'last_seen': artist.last_seen.isoformat() if artist.last_seen else None
        })
    
    return jsonify(result), 200

@dashboard_bp.route('/venues', methods=['GET'])
@jwt_required()
def get_venue_stats():
    user_id = int(get_jwt_identity())
    
    venue_stats = db.session.query(
        Venue.id,
        Venue.name,
        Venue.location,
        func.count(Show.id).label('show_count'),
        func.max(Show.date).label('last_visit')
    ).join(Show).filter(
        Show.user_id == user_id
    ).group_by(
        Venue.id, Venue.name, Venue.location
    ).order_by(
        desc('show_count')
    ).all()
    
    result = []
    for venue in venue_stats:
        result.append({
            'id': venue.id,
            'name': venue.name,
            'location': venue.location,
            'show_count': venue.show_count,
            'last_visit': venue.last_visit.isoformat() if venue.last_visit else None
        })
    
    return jsonify(result), 200

@dashboard_bp.route('/photos/recent', methods=['GET'])
@jwt_required()
def get_recent_photos():
    user_id = int(get_jwt_identity())
    limit = int(request.args.get('limit', 10))
    
    photos = Photo.query.filter_by(user_id=user_id).\
        order_by(Photo.created_at.desc()).\
        limit(limit).all()
    
    return jsonify([photo.to_dict() for photo in photos]), 200

@dashboard_bp.route('/audio/recent', methods=['GET'])
@jwt_required()
def get_recent_audio():
    user_id = int(get_jwt_identity())
    limit = int(request.args.get('limit', 10))
    
    audio = AudioRecording.query.filter_by(user_id=user_id).\
        order_by(AudioRecording.created_at.desc()).\
        limit(limit).all()
    
    return jsonify([a.to_dict() for a in audio]), 200

@dashboard_bp.route('/videos/recent', methods=['GET'])
@jwt_required()
def get_recent_videos():
    user_id = int(get_jwt_identity())
    limit = int(request.args.get('limit', 10))
    
    videos = VideoRecording.query.filter_by(user_id=user_id).\
        order_by(VideoRecording.created_at.desc()).\
        limit(limit).all()
    
    return jsonify([v.to_dict() for v in videos]), 200

@dashboard_bp.route('/comments/recent', methods=['GET'])
@jwt_required()
def get_recent_comments():
    user_id = int(get_jwt_identity())
    limit = int(request.args.get('limit', 10))
    
    comments = Comment.query.filter_by(user_id=user_id).\
        order_by(Comment.created_at.desc()).\
        limit(limit).all()
    
    return jsonify([comment.to_dict() for comment in comments]), 200
