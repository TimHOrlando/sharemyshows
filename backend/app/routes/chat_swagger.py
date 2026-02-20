"""
Chat API Routes - Flask-RESTX Implementation
Handles chat message history and active users (WebSocket events handled separately)
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.models import db, ChatMessage, Show, User

# Create namespace
api = Namespace('chat', description='Chat message operations')

# Models
user_brief = api.model('UserBrief', {
    'id': fields.Integer(description='User ID'),
    'username': fields.String(description='Username')
})

chat_message_model = api.model('ChatMessage', {
    'id': fields.Integer(description='Message ID'),
    'show_id': fields.Integer(description='Show ID'),
    'user_id': fields.Integer(description='User ID'),
    'user': fields.Nested(user_brief, description='User info'),
    'message': fields.String(description='Message text'),
    'timestamp': fields.DateTime(description='Message timestamp')
})

message_list_model = api.model('MessageList', {
    'messages': fields.List(fields.Nested(chat_message_model)),
    'total': fields.Integer(description='Total messages')
})

message_create_model = api.model('MessageCreate', {
    'message': fields.String(required=True, description='Message text', min_length=1)
})

active_user_model = api.model('ActiveUser', {
    'user_id': fields.Integer(description='User ID'),
    'username': fields.String(description='Username'),
    'joined_at': fields.DateTime(description='When user joined chat')
})

active_users_model = api.model('ActiveUsersList', {
    'users': fields.List(fields.Nested(active_user_model)),
    'total': fields.Integer(description='Total active users')
})

error_response = api.model('ErrorResponse', {
    'error': fields.String(description='Error message')
})


@api.route('/show/<int:show_id>/messages')
class ShowChatMessages(Resource):
    @api.doc('get_chat_messages', security='jwt')
    @api.response(200, 'Success', message_list_model)
    @api.response(404, 'Show not found', error_response)
    @jwt_required()
    def get(self, show_id):
        """Get chat message history for a show"""
        show = Show.query.get(show_id)
        if not show:
            return {'error': 'Show not found'}, 404
        
        # Get messages, ordered by timestamp
        messages = ChatMessage.query.filter_by(show_id=show_id)\
            .order_by(ChatMessage.timestamp.asc())\
            .limit(100)\
            .all()
        
        # Add user info to each message
        results = []
        for message in messages:
            user = User.query.get(message.user_id)
            msg_dict = message.to_dict()
            msg_dict['user'] = {
                'id': user.id,
                'username': user.username
            }
            results.append(msg_dict)
        
        return {
            'messages': results,
            'total': len(results)
        }
    
    @api.doc('post_chat_message', security='jwt')
    @api.expect(message_create_model)
    @api.response(201, 'Message created', chat_message_model)
    @api.response(400, 'Bad request', error_response)
    @api.response(404, 'Show not found', error_response)
    @jwt_required()
    def post(self, show_id):
        """Post a new chat message"""
        current_user_id = int(get_jwt_identity())
        
        show = Show.query.get(show_id)
        if not show:
            return {'error': 'Show not found'}, 404
        
        data = request.get_json()
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return {'error': 'message is required'}, 400
        
        message = ChatMessage(
            show_id=show_id,
            user_id=current_user_id,
            message=message_text,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Get user info for response
        user = User.query.get(current_user_id)
        result = message.to_dict()
        result['user'] = {
            'id': user.id,
            'username': user.username
        }
        
        return result, 201


@api.route('/show/<int:show_id>/active-users')
class ShowActiveUsers(Resource):
    @api.doc('get_active_users', security='jwt')
    @api.response(200, 'Success', active_users_model)
    @api.response(404, 'Show not found', error_response)
    @jwt_required()
    def get(self, show_id):
        """Get list of currently active users in show chat
        
        Note: This returns users who have recently posted messages.
        Real-time active user tracking is handled via WebSocket events.
        """
        show = Show.query.get(show_id)
        if not show:
            return {'error': 'Show not found'}, 404
        
        # Get unique users who have posted in the last hour
        from datetime import timedelta
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        recent_users = db.session.query(User)\
            .join(ChatMessage, ChatMessage.user_id == User.id)\
            .filter(ChatMessage.show_id == show_id)\
            .filter(ChatMessage.timestamp >= one_hour_ago)\
            .distinct()\
            .all()
        
        results = [{
            'user_id': user.id,
            'username': user.username,
            'joined_at': datetime.utcnow().isoformat()  # Placeholder
        } for user in recent_users]
        
        return {
            'users': results,
            'total': len(results)
        }
