from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.models import db, VideoRecording, Show
from PIL import Image
import os
import uuid

videos_bp = Blueprint('videos', __name__, url_prefix='/api/videos')

UPLOAD_FOLDER = 'uploads/videos'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@videos_bp.route('', methods=['POST'])
@jwt_required()
def upload_video():
    user_id = int(get_jwt_identity())
    
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    if 'show_id' not in request.form:
        return jsonify({'error': 'Missing show_id'}), 400
    
    show_id = int(request.form['show_id'])
    
    show = Show.query.filter_by(id=show_id, user_id=user_id).first()
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{extension}"
    
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    video = VideoRecording(
        user_id=user_id,
        show_id=show_id,
        filename=filename,
        original_filename=original_filename,
        title=request.form.get('title', original_filename),
        duration=request.form.get('duration', type=int)
    )
    
    try:
        db.session.add(video)
        db.session.commit()
        return jsonify(video.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': 'Failed to save video', 'details': str(e)}), 500

@videos_bp.route('/<int:video_id>', methods=['GET'])
@jwt_required()
def get_video(video_id):
    video = VideoRecording.query.get(video_id)
    
    if not video:
        return jsonify({'error': 'Video not found'}), 404
    
    filepath = os.path.join(UPLOAD_FOLDER, video.filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Video file not found'}), 404
    
    return send_file(filepath, mimetype='video/*')

@videos_bp.route('/<int:video_id>', methods=['PUT'])
@jwt_required()
def update_video(video_id):
    user_id = int(get_jwt_identity())
    video = VideoRecording.query.filter_by(id=video_id, user_id=user_id).first()
    
    if not video:
        return jsonify({'error': 'Video not found'}), 404
    
    data = request.get_json()
    
    if 'title' in data:
        video.title = data['title']
    if 'duration' in data:
        video.duration = data['duration']
    
    try:
        db.session.commit()
        return jsonify(video.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update video', 'details': str(e)}), 500

@videos_bp.route('/<int:video_id>', methods=['DELETE'])
@jwt_required()
def delete_video(video_id):
    user_id = int(get_jwt_identity())
    video = VideoRecording.query.filter_by(id=video_id, user_id=user_id).first()
    
    if not video:
        return jsonify({'error': 'Video not found'}), 404
    
    filepath = os.path.join(UPLOAD_FOLDER, video.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    try:
        db.session.delete(video)
        db.session.commit()
        return jsonify({'message': 'Video deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete video', 'details': str(e)}), 500

@videos_bp.route('/show/<int:show_id>', methods=['GET'])
@jwt_required()
def get_show_videos(show_id):
    user_id = int(get_jwt_identity())
    
    show = Show.query.filter_by(id=show_id, user_id=user_id).first()
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    videos = VideoRecording.query.filter_by(show_id=show_id).all()
    return jsonify([video.to_dict() for video in videos]), 200
