from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.models import db, Photo, Show
from PIL import Image
import os
import uuid

photos_bp = Blueprint('photos', __name__, url_prefix='/api/photos')

UPLOAD_FOLDER = 'uploads/photos'
THUMBNAIL_SIZE = (300, 300)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_thumbnail(image_path, thumbnail_path):
    try:
        with Image.open(image_path) as img:
            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            img.save(thumbnail_path)
        return True
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return False

@photos_bp.route('', methods=['POST'])
@jwt_required()
def upload_photo():
    user_id = int(get_jwt_identity())
    
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo file provided'}), 400
    
    if 'show_id' not in request.form:
        return jsonify({'error': 'Missing show_id'}), 400
    
    show_id = int(request.form['show_id'])
    
    show = Show.query.filter_by(id=show_id, user_id=user_id).first()
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    file = request.files['photo']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{extension}"
    thumbnail_filename = f"{uuid.uuid4().hex}_thumb.{extension}"
    
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    thumbnail_path = os.path.join(UPLOAD_FOLDER, thumbnail_filename)
    create_thumbnail(filepath, thumbnail_path)
    
    photo = Photo(
        user_id=user_id,
        show_id=show_id,
        filename=filename,
        original_filename=original_filename,
        thumbnail_filename=thumbnail_filename,
        caption=request.form.get('caption', '')
    )
    
    try:
        db.session.add(photo)
        db.session.commit()
        return jsonify(photo.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        if os.path.exists(filepath):
            os.remove(filepath)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        return jsonify({'error': 'Failed to save photo', 'details': str(e)}), 500

@photos_bp.route('/<int:photo_id>', methods=['GET'])
@jwt_required()
def get_photo(photo_id):
    photo = Photo.query.get(photo_id)
    
    if not photo:
        return jsonify({'error': 'Photo not found'}), 404
    
    filepath = os.path.join(UPLOAD_FOLDER, photo.filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Photo file not found'}), 404
    
    return send_file(filepath, mimetype='image/*')

@photos_bp.route('/<int:photo_id>/thumbnail', methods=['GET'])
@jwt_required()
def get_thumbnail(photo_id):
    photo = Photo.query.get(photo_id)
    
    if not photo or not photo.thumbnail_filename:
        return jsonify({'error': 'Thumbnail not found'}), 404
    
    filepath = os.path.join(UPLOAD_FOLDER, photo.thumbnail_filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Thumbnail file not found'}), 404
    
    return send_file(filepath, mimetype='image/*')

@photos_bp.route('/<int:photo_id>', methods=['PUT'])
@jwt_required()
def update_photo(photo_id):
    user_id = int(get_jwt_identity())
    photo = Photo.query.filter_by(id=photo_id, user_id=user_id).first()
    
    if not photo:
        return jsonify({'error': 'Photo not found'}), 404
    
    data = request.get_json()
    
    if 'caption' in data:
        photo.caption = data['caption']
    
    try:
        db.session.commit()
        return jsonify(photo.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update photo', 'details': str(e)}), 500

@photos_bp.route('/<int:photo_id>', methods=['DELETE'])
@jwt_required()
def delete_photo(photo_id):
    user_id = int(get_jwt_identity())
    photo = Photo.query.filter_by(id=photo_id, user_id=user_id).first()
    
    if not photo:
        return jsonify({'error': 'Photo not found'}), 404
    
    filepath = os.path.join(UPLOAD_FOLDER, photo.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    if photo.thumbnail_filename:
        thumbnail_path = os.path.join(UPLOAD_FOLDER, photo.thumbnail_filename)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
    
    try:
        db.session.delete(photo)
        db.session.commit()
        return jsonify({'message': 'Photo deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete photo', 'details': str(e)}), 500

@photos_bp.route('/show/<int:show_id>', methods=['GET'])
@jwt_required()
def get_show_photos(show_id):
    user_id = int(get_jwt_identity())
    
    show = Show.query.filter_by(id=show_id, user_id=user_id).first()
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    photos = Photo.query.filter_by(show_id=show_id).all()
    return jsonify([photo.to_dict() for photo in photos]), 200
