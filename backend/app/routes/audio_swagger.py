"""
Audio API Routes - Flask-RESTX Implementation
Handles audio recording uploads, streaming, updates, and deletion
"""
from flask import request, send_file, Response
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os

from app.models import db, AudioRecording, Show

# Create namespace
api = Namespace('audio', description='Audio recording management operations')

# File upload parser
upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='Audio file to upload')
upload_parser.add_argument('show_id', type=int, required=True, help='Show ID')
upload_parser.add_argument('title', type=str, required=False, help='Audio title')
upload_parser.add_argument('description', type=str, required=False, help='Audio description')

# Models
audio_model = api.model('AudioRecording', {
    'id': fields.Integer(description='Audio ID'),
    'show_id': fields.Integer(description='Show ID'),
    'user_id': fields.Integer(description='User ID'),
    'filename': fields.String(description='Original filename'),
    'file_path': fields.String(description='File path'),
    'title': fields.String(description='Audio title'),
    'description': fields.String(description='Description'),
    'duration': fields.Float(description='Duration in seconds'),
    'file_size': fields.Integer(description='File size in bytes'),
    'uploaded_at': fields.DateTime(description='Upload time')
})

audio_list_model = api.model('AudioList', {
    'recordings': fields.List(fields.Nested(audio_model)),
    'total': fields.Integer(description='Total recordings')
})

audio_update_model = api.model('AudioUpdate', {
    'title': fields.String(required=False, description='New title'),
    'description': fields.String(required=False, description='New description')
})

message_response = api.model('MessageResponse', {
    'message': fields.String(description='Response message')
})

error_response = api.model('ErrorResponse', {
    'error': fields.String(description='Error message')
})


def allowed_audio_file(filename):
    """Check if audio file extension is allowed"""
    allowed_extensions = {'mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


@api.route('')
class AudioUpload(Resource):
    @api.doc('upload_audio', security='jwt')
    @api.expect(upload_parser)
    @api.response(201, 'Audio uploaded', audio_model)
    @api.response(400, 'Bad request', error_response)
    @api.response(404, 'Show not found', error_response)
    @jwt_required()
    def post(self):
        """Upload a new audio recording"""
        current_user_id = int(get_jwt_identity())
        
        show_id = request.form.get('show_id', type=int)
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        
        if not show_id:
            return {'error': 'show_id is required'}, 400
        
        show = Show.query.get(show_id)
        if not show:
            return {'error': 'Show not found'}, 404
        
        if 'file' not in request.files:
            return {'error': 'No file provided'}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {'error': 'No file selected'}, 400
        
        if not allowed_audio_file(file.filename):
            return {'error': 'Invalid file type. Allowed: mp3, wav, ogg, m4a, flac, aac'}, 400
        
        upload_dir = os.path.join('uploads', 'audio')
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{current_user_id}_{show_id}_{os.urandom(8).hex()}.{extension}"
        
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        file_size = os.path.getsize(file_path)
        
        # Could add duration calculation here using mutagen or similar
        duration = None
        
        audio = AudioRecording(
            show_id=show_id,
            user_id=current_user_id,
            filename=filename,
            file_path=file_path,
            title=title or filename,
            description=description,
            duration=duration,
            file_size=file_size
        )
        
        db.session.add(audio)
        db.session.commit()
        
        return audio.to_dict(), 201


@api.route('/<int:audio_id>')
class AudioDetail(Resource):
    @api.doc('stream_audio', security='jwt')
    @api.response(200, 'Success - Returns audio file')
    @api.response(404, 'Not found', error_response)
    @jwt_required()
    def get(self, audio_id):
        """Stream or download audio file"""
        audio = AudioRecording.query.get(audio_id)
        if not audio:
            return {'error': 'Audio not found'}, 404
        
        if not os.path.exists(audio.file_path):
            return {'error': 'File not found'}, 404
        
        # Determine mime type based on extension
        extension = audio.filename.rsplit('.', 1)[1].lower() if '.' in audio.filename else ''
        mime_types = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            'm4a': 'audio/mp4',
            'flac': 'audio/flac',
            'aac': 'audio/aac'
        }
        mime_type = mime_types.get(extension, 'audio/mpeg')
        
        return send_file(audio.file_path, mimetype=mime_type)
    
    @api.doc('update_audio_metadata', security='jwt')
    @api.expect(audio_update_model)
    @api.response(200, 'Metadata updated', audio_model)
    @api.response(403, 'Forbidden', error_response)
    @api.response(404, 'Not found', error_response)
    @jwt_required()
    def put(self, audio_id):
        """Update audio metadata"""
        current_user_id = int(get_jwt_identity())
        
        audio = AudioRecording.query.get(audio_id)
        if not audio:
            return {'error': 'Audio not found'}, 404
        
        if audio.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        data = request.get_json()
        if 'title' in data:
            audio.title = data['title']
        if 'description' in data:
            audio.description = data['description']
        
        db.session.commit()
        return audio.to_dict()
    
    @api.doc('delete_audio', security='jwt')
    @api.response(200, 'Audio deleted', message_response)
    @api.response(403, 'Forbidden', error_response)
    @api.response(404, 'Not found', error_response)
    @jwt_required()
    def delete(self, audio_id):
        """Delete an audio recording"""
        current_user_id = int(get_jwt_identity())
        
        audio = AudioRecording.query.get(audio_id)
        if not audio:
            return {'error': 'Audio not found'}, 404
        
        if audio.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        try:
            if os.path.exists(audio.file_path):
                os.remove(audio.file_path)
        except Exception:
            pass
        
        db.session.delete(audio)
        db.session.commit()
        
        return {'message': 'Audio deleted'}


@api.route('/show/<int:show_id>')
class ShowAudio(Resource):
    @api.doc('get_show_audio', security='jwt')
    @api.response(200, 'Success', audio_list_model)
    @api.response(404, 'Show not found', error_response)
    @jwt_required()
    def get(self, show_id):
        """Get all audio recordings for a show"""
        show = Show.query.get(show_id)
        if not show:
            return {'error': 'Show not found'}, 404
        
        recordings = AudioRecording.query.filter_by(show_id=show_id).order_by(AudioRecording.uploaded_at.desc()).all()
        
        return {
            'recordings': [audio.to_dict() for audio in recordings],
            'total': len(recordings)
        }
