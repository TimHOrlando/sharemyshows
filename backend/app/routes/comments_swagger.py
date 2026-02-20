"""
Comments API Routes - Flask-RESTX Implementation
Handles comment creation, updates, deletion, and retrieval
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.models import db, Comment, Show, Photo, User, get_friend_ids

# Create namespace
api = Namespace('comments', description='Comment management operations')

# Models
user_brief = api.model('UserBrief', {
    'id': fields.Integer(description='User ID'),
    'username': fields.String(description='Username'),
    'email': fields.String(description='Email')
})

comment_model = api.model('Comment', {
    'id': fields.Integer(description='Comment ID'),
    'show_id': fields.Integer(description='Show ID'),
    'user_id': fields.Integer(description='User ID'),
    'user': fields.Nested(user_brief, description='User info'),
    'text': fields.String(description='Comment text'),
    'photo_id': fields.Integer(description='Photo ID (null for show comments)'),
    'created_at': fields.DateTime(description='Creation time'),
    'updated_at': fields.DateTime(description='Last update time')
})

comment_list_model = api.model('CommentList', {
    'comments': fields.List(fields.Nested(comment_model)),
    'total': fields.Integer(description='Total comments')
})

comment_create_model = api.model('CommentCreate', {
    'show_id': fields.Integer(required=False, description='Show ID (required if no photo_id)'),
    'photo_id': fields.Integer(required=False, description='Photo ID (optional, for photo comments)'),
    'text': fields.String(required=True, description='Comment text', min_length=1)
})

comment_update_model = api.model('CommentUpdate', {
    'text': fields.String(required=True, description='New comment text', min_length=1)
})

message_response = api.model('MessageResponse', {
    'message': fields.String(description='Response message')
})

error_response = api.model('ErrorResponse', {
    'error': fields.String(description='Error message')
})


@api.route('')
class CommentCreate(Resource):
    @api.doc('create_comment', security='jwt')
    @api.expect(comment_create_model)
    @api.response(201, 'Comment created', comment_model)
    @api.response(400, 'Bad request', error_response)
    @api.response(404, 'Show not found', error_response)
    @jwt_required()
    def post(self):
        """Create a new comment on a show or photo"""
        current_user_id = int(get_jwt_identity())
        data = request.get_json()

        text = data.get('text', '').strip()
        if not text:
            return {'error': 'text is required'}, 400

        photo_id = data.get('photo_id')
        show_id = data.get('show_id')

        # If photo_id provided, derive show_id from the photo
        if photo_id:
            photo = Photo.query.get(photo_id)
            if not photo:
                return {'error': 'Photo not found'}, 404
            show_id = photo.show_id

        if not show_id:
            return {'error': 'show_id or photo_id is required'}, 400

        show = Show.query.get(show_id)
        if not show:
            return {'error': 'Show not found'}, 404

        # Authorization: must be show owner or friend of owner
        if show.user_id != current_user_id:
            friend_ids = get_friend_ids(show.user_id)
            if current_user_id not in friend_ids:
                return {'error': 'Not authorized to comment on this show'}, 403

        comment = Comment(
            show_id=show_id,
            photo_id=photo_id,
            user_id=current_user_id,
            text=text
        )

        db.session.add(comment)
        db.session.commit()

        return comment.to_dict(), 201


@api.route('/<int:comment_id>')
class CommentDetail(Resource):
    @api.doc('update_comment', security='jwt')
    @api.expect(comment_update_model)
    @api.response(200, 'Comment updated', comment_model)
    @api.response(400, 'Bad request', error_response)
    @api.response(403, 'Forbidden', error_response)
    @api.response(404, 'Not found', error_response)
    @jwt_required()
    def put(self, comment_id):
        """Update a comment"""
        current_user_id = int(get_jwt_identity())
        
        comment = Comment.query.get(comment_id)
        if not comment:
            return {'error': 'Comment not found'}, 404
        
        if comment.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text:
            return {'error': 'text is required'}, 400

        comment.text = text
        comment.updated_at = datetime.utcnow()

        db.session.commit()

        return comment.to_dict()
    
    @api.doc('delete_comment', security='jwt')
    @api.response(200, 'Comment deleted', message_response)
    @api.response(403, 'Forbidden', error_response)
    @api.response(404, 'Not found', error_response)
    @jwt_required()
    def delete(self, comment_id):
        """Delete a comment"""
        current_user_id = int(get_jwt_identity())
        
        comment = Comment.query.get(comment_id)
        if not comment:
            return {'error': 'Comment not found'}, 404
        
        if comment.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        db.session.delete(comment)
        db.session.commit()
        
        return {'message': 'Comment deleted'}


@api.route('/show/<int:show_id>')
class ShowComments(Resource):
    @api.doc('get_show_comments', security='jwt')
    @api.response(200, 'Success', comment_list_model)
    @api.response(404, 'Show not found', error_response)
    @jwt_required()
    def get(self, show_id):
        """Get show-level comments (excludes photo comments)"""
        show = Show.query.get(show_id)
        if not show:
            return {'error': 'Show not found'}, 404

        comments = Comment.query.filter_by(show_id=show_id).filter(
            Comment.photo_id.is_(None)
        ).order_by(Comment.created_at.asc()).all()

        return {
            'comments': [c.to_dict() for c in comments],
            'total': len(comments)
        }


@api.route('/photo/<int:photo_id>')
class PhotoComments(Resource):
    @api.doc('get_photo_comments', security='jwt')
    @api.response(200, 'Success', comment_list_model)
    @api.response(404, 'Photo not found', error_response)
    @jwt_required()
    def get(self, photo_id):
        """Get all comments for a photo"""
        photo = Photo.query.get(photo_id)
        if not photo:
            return {'error': 'Photo not found'}, 404

        comments = Comment.query.filter_by(photo_id=photo_id).order_by(Comment.created_at.asc()).all()

        return {
            'comments': [c.to_dict() for c in comments],
            'total': len(comments)
        }
