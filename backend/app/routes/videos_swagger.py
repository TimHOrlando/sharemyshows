"""
Videos API Routes - Flask-RESTX Implementation
Handles video uploads, streaming, updates, and deletion
"""
from flask import request, send_file
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os

from app.models import db, VideoRecording, Show

# Create namespace
api = Namespace('videos', description='Video recording management operations')

# File upload parser
upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='Video file to upload')
upload_parser.add_argument('show_id', type=int, required=True, help='Show ID')
upload_parser.add_argument('title', type=str, required=False, help='Video title')
upload_parser.add_argument('description', type=str, required=False, help='Video description')

# Models
video_model = api.model('VideoRecording', {
    'id': fields.Integer(description='Video ID'),
    'show_id': fields.Integer(description='Show ID'),
    'user_id': fields.Integer(description='User ID'),
    'filename': fields.String(description='Original filename'),
    'file_path': fields.String(description='File path'),
    'title': fields.String(description='Video title'),
    'description': fields.String(description='Description'),
    'duration': fields.Float(description='Duration in seconds'),
    'file_size': fields.Integer(description='File size in bytes'),
    'uploaded_at': fields.DateTime(description='Upload time')
})

video_list_model = api.model('VideoList', {
    'recordings': fields.List(fields.Nested(video_model)),
    'total': fields.Integer(description='Total recordings')
})

video_update_model = api.model('VideoUpdate', {
    'title': fields.String(required=False, description='New title'),
    'description': fields.String(required=False, description='New description')
})

message_response = api.model('MessageResponse', {
    'message': fields.String(description='Response message')
})

error_response = api.model('ErrorResponse', {
    'error': fields.String(description='Error message')
})


def allowed_video_file(filename):
    """Check if video file extension is allowed"""
    allowed_extensions = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'flv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


@api.route('')
class VideoUpload(Resource):
    @api.doc('upload_video', security='jwt')
    @api.expect(upload_parser)
    @api.response(201, 'Video uploaded', video_model)
    @api.response(400, 'Bad request', error_response)
    @api.response(404, 'Show not found', error_response)
    @jwt_required()
    def post(self):
        """Upload a new video recording"""
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
        
        if not allowed_video_file(file.filename):
            return {'error': 'Invalid file type. Allowed: mp4, mov, avi, mkv, webm, flv'}, 400
        
        upload_dir = os.path.join('uploads', 'videos')
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{current_user_id}_{show_id}_{os.urandom(8).hex()}.{extension}"
        
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        file_size = os.path.getsize(file_path)
        
        # Could add duration calculation here using ffmpeg or similar
        duration = None
        
        video = VideoRecording(
            show_id=show_id,
            user_id=current_user_id,
            filename=filename,
            file_path=file_path,
            title=title or filename,
            description=description,
            duration=duration,
            file_size=file_size
        )
        
        db.session.add(video)
        db.session.commit()
        
        return video.to_dict(), 201


@api.route('/<int:video_id>')
class VideoDetail(Resource):
    @api.doc('stream_video', security='jwt')
    @api.response(200, 'Success - Returns video file')
    @api.response(404, 'Not found', error_response)
    @jwt_required()
    def get(self, video_id):
        """Stream or download video file"""
        video = VideoRecording.query.get(video_id)
        if not video:
            return {'error': 'Video not found'}, 404
        
        if not os.path.exists(video.file_path):
            return {'error': 'File not found'}, 404
        
        # Determine mime type based on extension
        extension = video.filename.rsplit('.', 1)[1].lower() if '.' in video.filename else ''
        mime_types = {
            'mp4': 'video/mp4',
            'mov': 'video/quicktime',
            'avi': 'video/x-msvideo',
            'mkv': 'video/x-matroska',
            'webm': 'video/webm',
            'flv': 'video/x-flv'
        }
        mime_type = mime_types.get(extension, 'video/mp4')
        
        return send_file(video.file_path, mimetype=mime_type)
    
    @api.doc('update_video_metadata', security='jwt')
    @api.expect(video_update_model)
    @api.response(200, 'Metadata updated', video_model)
    @api.response(403, 'Forbidden', error_response)
    @api.response(404, 'Not found', error_response)
    @jwt_required()
    def put(self, video_id):
        """Update video metadata"""
        current_user_id = int(get_jwt_identity())
        
        video = VideoRecording.query.get(video_id)
        if not video:
            return {'error': 'Video not found'}, 404
        
        if video.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        data = request.get_json()
        if 'title' in data:
            video.title = data['title']
        if 'description' in data:
            video.description = data['description']
        
        db.session.commit()
        return video.to_dict()
    
    @api.doc('delete_video', security='jwt')
    @api.response(200, 'Video deleted', message_response)
    @api.response(403, 'Forbidden', error_response)
    @api.response(404, 'Not found', error_response)
    @jwt_required()
    def delete(self, video_id):
        """Delete a video recording"""
        current_user_id = int(get_jwt_identity())
        
        video = VideoRecording.query.get(video_id)
        if not video:
            return {'error': 'Video not found'}, 404
        
        if video.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        try:
            if os.path.exists(video.file_path):
                os.remove(video.file_path)
        except Exception:
            pass
        
        db.session.delete(video)
        db.session.commit()
        
        return {'message': 'Video deleted'}


@api.route('/show/<int:show_id>')
class ShowVideos(Resource):
    @api.doc('get_show_videos', security='jwt')
    @api.response(200, 'Success', video_list_model)
    @api.response(404, 'Show not found', error_response)
    @jwt_required()
    def get(self, show_id):
        """Get all video recordings for a show"""
        show = Show.query.get(show_id)
        if not show:
            return {'error': 'Show not found'}, 404
        
        recordings = VideoRecording.query.filter_by(show_id=show_id).order_by(VideoRecording.uploaded_at.desc()).all()
        
        return {
            'recordings': [video.to_dict() for video in recordings],
            'total': len(recordings)
        }
