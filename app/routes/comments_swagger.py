"""
Comments API Routes - Flask-RESTX Implementation
Handles comment creation, updates, deletion, and retrieval
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.models import db, Comment, Show, User

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
    'content': fields.String(description='Comment text'),
    'created_at': fields.DateTime(description='Creation time'),
    'updated_at': fields.DateTime(description='Last update time')
})

comment_list_model = api.model('CommentList', {
    'comments': fields.List(fields.Nested(comment_model)),
    'total': fields.Integer(description='Total comments')
})

comment_create_model = api.model('CommentCreate', {
    'show_id': fields.Integer(required=True, description='Show ID'),
    'content': fields.String(required=True, description='Comment text', min_length=1)
})

comment_update_model = api.model('CommentUpdate', {
    'content': fields.String(required=True, description='New comment text', min_length=1)
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
        """Create a new comment"""
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        show_id = data.get('show_id')
        content = data.get('content', '').strip()
        
        if not show_id:
            return {'error': 'show_id is required'}, 400
        
        if not content:
            return {'error': 'content is required'}, 400
        
        show = Show.query.get(show_id)
        if not show:
            return {'error': 'Show not found'}, 404
        
        comment = Comment(
            show_id=show_id,
            user_id=current_user_id,
            content=content
        )
        
        db.session.add(comment)
        db.session.commit()
        
        # Get user info for response
        user = User.query.get(current_user_id)
        result = comment.to_dict()
        result['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
        
        return result, 201


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
        current_user_id = get_jwt_identity()
        
        comment = Comment.query.get(comment_id)
        if not comment:
            return {'error': 'Comment not found'}, 404
        
        if comment.user_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return {'error': 'content is required'}, 400
        
        comment.content = content
        comment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Get user info for response
        user = User.query.get(current_user_id)
        result = comment.to_dict()
        result['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
        
        return result
    
    @api.doc('delete_comment', security='jwt')
    @api.response(200, 'Comment deleted', message_response)
    @api.response(403, 'Forbidden', error_response)
    @api.response(404, 'Not found', error_response)
    @jwt_required()
    def delete(self, comment_id):
        """Delete a comment"""
        current_user_id = get_jwt_identity()
        
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
        """Get all comments for a show"""
        show = Show.query.get(show_id)
        if not show:
            return {'error': 'Show not found'}, 404
        
        comments = Comment.query.filter_by(show_id=show_id).order_by(Comment.created_at.desc()).all()
        
        # Add user info to each comment
        results = []
        for comment in comments:
            user = User.query.get(comment.user_id)
            comment_dict = comment.to_dict()
            comment_dict['user'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
            results.append(comment_dict)
        
        return {
            'comments': results,
            'total': len(results)
        }
