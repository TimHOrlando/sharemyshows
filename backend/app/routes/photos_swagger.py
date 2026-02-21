"""
Photos API Routes - Flask-RESTX Implementation
Handles photo uploads, retrieval, thumbnails, updates, and deletion
"""
from flask import request, send_file
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os
from PIL import Image

from app.models import db, Photo, Show, Artist, Venue

# Create namespace
api = Namespace('photos', description='Photo management operations')

# File upload parser
upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='Photo file to upload')
upload_parser.add_argument('show_id', type=int, required=True, help='Show ID')
upload_parser.add_argument('caption', type=str, required=False, help='Photo caption')

# Models
photo_model = api.model('Photo', {
    'id': fields.Integer(description='Photo ID'),
    'show_id': fields.Integer(description='Show ID'),
    'user_id': fields.Integer(description='User ID'),
    'filename': fields.String(description='Original filename'),
    'file_path': fields.String(description='File path'),
    'thumbnail_path': fields.String(description='Thumbnail path'),
    'caption': fields.String(description='Caption'),
    'uploaded_at': fields.DateTime(description='Upload time'),
    'file_size': fields.Integer(description='File size in bytes'),
    'width': fields.Integer(description='Width in pixels'),
    'height': fields.Integer(description='Height in pixels')
})

photo_list_model = api.model('PhotoList', {
    'photos': fields.List(fields.Nested(photo_model)),
    'total': fields.Integer(description='Total photos')
})

caption_update_model = api.model('CaptionUpdate', {
    'caption': fields.String(required=True, description='New caption')
})

message_response = api.model('MessageResponse', {
    'message': fields.String(description='Response message')
})

error_response = api.model('ErrorResponse', {
    'error': fields.String(description='Error message')
})


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


@api.route('')
class PhotoList(Resource):
    @api.doc('list_user_photos', security='jwt')
    @api.response(200, 'Success', photo_list_model)
    @jwt_required()
    def get(self):
        """Get all photos for the current user, with show info"""
        current_user_id = int(get_jwt_identity())
        results = db.session.query(Photo, Show)\
            .join(Show, Photo.show_id == Show.id)\
            .filter(Photo.user_id == current_user_id)\
            .order_by(Show.date.desc(), Photo.created_at.desc()).all()

        photos = []
        for photo, show in results:
            d = photo.to_dict()
            d['artist_name'] = show.artist.name if show.artist else 'Unknown Artist'
            d['venue_name'] = show.venue.name if show.venue else 'Unknown Venue'
            d['show_date'] = show.date.isoformat() if show.date else None
            photos.append(d)

        return {
            'photos': photos,
            'total': len(photos)
        }

    @api.doc('upload_photo', security='jwt')
    @api.expect(upload_parser)
    @api.response(201, 'Photo uploaded', photo_model)
    @api.response(400, 'Bad request', error_response)
    @api.response(404, 'Show not found', error_response)
    @jwt_required()
    def post(self):
        """Upload a new photo"""
        current_user_id = int(get_jwt_identity())
        
        show_id = request.form.get('show_id', type=int)
        caption = request.form.get('caption', '')
        
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
        
        if not allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif', 'webp'}):
            return {'error': 'Invalid file type'}, 400
        
        upload_dir = os.path.join('uploads', 'photos')
        thumbnail_dir = os.path.join('uploads', 'thumbnails')
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(thumbnail_dir, exist_ok=True)
        
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{current_user_id}_{show_id}_{os.urandom(8).hex()}.{extension}"
        
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                thumbnail_filename = f"thumb_{unique_filename}"
                thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
                img.save(thumbnail_path)
        except Exception:
            width = height = None
            thumbnail_path = None
        
        file_size = os.path.getsize(file_path)
        
        photo = Photo(
            show_id=show_id,
            user_id=current_user_id,
            filename=filename,
            file_path=file_path,
            thumbnail_path=thumbnail_path,
            caption=caption,
            file_size=file_size,
            width=width,
            height=height
        )
        
        db.session.add(photo)
        db.session.commit()
        
        return photo.to_dict(), 201


@api.route('/<int:photo_id>')
class PhotoDetail(Resource):
    @api.doc('get_photo')
    @api.response(200, 'Success - Returns image')
    @api.response(404, 'Not found', error_response)
    def get(self, photo_id):
        """Get full-size photo"""
        photo = Photo.query.get(photo_id)
        if not photo:
            return {'error': 'Photo not found'}, 404

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, 'uploads', 'photos', photo.filename)

        if not os.path.exists(file_path):
            return {'error': 'File not found'}, 404

        # Detect mimetype from extension
        ext = photo.filename.rsplit('.', 1)[-1].lower() if '.' in photo.filename else 'jpeg'
        mimetypes = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'gif': 'image/gif', 'webp': 'image/webp'}
        mimetype = mimetypes.get(ext, 'image/jpeg')

        return send_file(file_path, mimetype=mimetype)
    
    @api.doc('update_photo_caption', security='jwt')
    @api.expect(caption_update_model)
    @api.response(200, 'Caption updated', photo_model)
    @api.response(403, 'Forbidden', error_response)
    @api.response(404, 'Not found', error_response)
    @jwt_required()
    def put(self, photo_id):
        """Update photo caption"""
        current_user_id = int(get_jwt_identity())
        
        photo = Photo.query.get(photo_id)
        if not photo:
            return {'error': 'Photo not found'}, 404
        
        if photo.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        data = request.get_json()
        photo.caption = data.get('caption', photo.caption)
        
        db.session.commit()
        return photo.to_dict()
    
    @api.doc('delete_photo', security='jwt')
    @api.response(200, 'Photo deleted', message_response)
    @api.response(403, 'Forbidden', error_response)
    @api.response(404, 'Not found', error_response)
    @jwt_required()
    def delete(self, photo_id):
        """Delete a photo"""
        current_user_id = int(get_jwt_identity())
        
        photo = Photo.query.get(photo_id)
        if not photo:
            return {'error': 'Photo not found'}, 404
        
        if photo.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        try:
            file_path = os.path.join(base_dir, 'uploads', 'photos', photo.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            if photo.thumbnail_filename:
                thumb_path = os.path.join(base_dir, 'uploads', 'thumbnails', photo.thumbnail_filename)
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
        except Exception:
            pass
        
        db.session.delete(photo)
        db.session.commit()
        
        return {'message': 'Photo deleted'}


@api.route('/<int:photo_id>/thumbnail')
class PhotoThumbnail(Resource):
    @api.doc('get_photo_thumbnail')
    @api.response(200, 'Success - Returns thumbnail')
    @api.response(404, 'Not found', error_response)
    def get(self, photo_id):
        """Get photo thumbnail"""
        photo = Photo.query.get(photo_id)
        if not photo:
            return {'error': 'Photo not found'}, 404

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Detect mimetype from extension
        ext = photo.filename.rsplit('.', 1)[-1].lower() if '.' in photo.filename else 'jpeg'
        mimetypes = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'gif': 'image/gif', 'webp': 'image/webp'}
        mimetype = mimetypes.get(ext, 'image/jpeg')

        # Try thumbnail first
        if photo.thumbnail_filename:
            thumb_path = os.path.join(base_dir, 'uploads', 'thumbnails', photo.thumbnail_filename)
            if os.path.exists(thumb_path):
                return send_file(thumb_path, mimetype=mimetype)

        # Fall back to full image
        file_path = os.path.join(base_dir, 'uploads', 'photos', photo.filename)
        if os.path.exists(file_path):
            return send_file(file_path, mimetype=mimetype)

        return {'error': 'File not found'}, 404


@api.route('/show/<int:show_id>')
class ShowPhotos(Resource):
    @api.doc('get_show_photos', security='jwt')
    @api.response(200, 'Success', photo_list_model)
    @api.response(404, 'Show not found', error_response)
    @jwt_required()
    def get(self, show_id):
        """Get all photos for a show"""
        show = Show.query.get(show_id)
        if not show:
            return {'error': 'Show not found'}, 404
        
        photos = Photo.query.filter_by(show_id=show_id).order_by(Photo.uploaded_at.desc()).all()
        
        return {
            'photos': [photo.to_dict() for photo in photos],
            'total': len(photos)
        }
