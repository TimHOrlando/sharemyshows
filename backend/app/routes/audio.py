from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.models import db, AudioRecording, Show
import os
import uuid

audio_bp = Blueprint('audio', __name__, url_prefix='/api/audio')

UPLOAD_FOLDER = 'uploads/audio'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@audio_bp.route('', methods=['POST'])
@jwt_required()
def upload_audio():
    user_id = int(get_jwt_identity())
    
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    if 'show_id' not in request.form:
        return jsonify({'error': 'Missing show_id'}), 400
    
    show_id = int(request.form['show_id'])
    
    show = Show.query.filter_by(id=show_id, user_id=user_id).first()
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    file = request.files['audio']
    
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
    
    audio = AudioRecording(
        user_id=user_id,
        show_id=show_id,
        filename=filename,
        original_filename=original_filename,
        title=request.form.get('title', original_filename),
        duration=request.form.get('duration', type=int)
    )
    
    try:
        db.session.add(audio)
        db.session.commit()
        return jsonify(audio.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': 'Failed to save audio', 'details': str(e)}), 500

@audio_bp.route('/<int:audio_id>', methods=['GET'])
@jwt_required()
def get_audio(audio_id):
    audio = AudioRecording.query.get(audio_id)
    
    if not audio:
        return jsonify({'error': 'Audio not found'}), 404
    
    filepath = os.path.join(UPLOAD_FOLDER, audio.filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Audio file not found'}), 404
    
    return send_file(filepath, mimetype='audio/*')

@audio_bp.route('/<int:audio_id>', methods=['PUT'])
@jwt_required()
def update_audio(audio_id):
    user_id = int(get_jwt_identity())
    audio = AudioRecording.query.filter_by(id=audio_id, user_id=user_id).first()
    
    if not audio:
        return jsonify({'error': 'Audio not found'}), 404
    
    data = request.get_json()
    
    if 'title' in data:
        audio.title = data['title']
    if 'duration' in data:
        audio.duration = data['duration']
    
    try:
        db.session.commit()
        return jsonify(audio.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update audio', 'details': str(e)}), 500

@audio_bp.route('/<int:audio_id>', methods=['DELETE'])
@jwt_required()
def delete_audio(audio_id):
    user_id = int(get_jwt_identity())
    audio = AudioRecording.query.filter_by(id=audio_id, user_id=user_id).first()
    
    if not audio:
        return jsonify({'error': 'Audio not found'}), 404
    
    filepath = os.path.join(UPLOAD_FOLDER, audio.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    try:
        db.session.delete(audio)
        db.session.commit()
        return jsonify({'message': 'Audio deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete audio', 'details': str(e)}), 500

@audio_bp.route('/show/<int:show_id>', methods=['GET'])
@jwt_required()
def get_show_audio(show_id):
    user_id = int(get_jwt_identity())
    
    show = Show.query.filter_by(id=show_id, user_id=user_id).first()
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    audio_recordings = AudioRecording.query.filter_by(show_id=show_id).all()
    return jsonify([audio.to_dict() for audio in audio_recordings]), 200
