"""
Direct Messaging API Routes - Flask-RESTX Implementation
Handles 1-on-1 conversations between friends
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.models import db, User, Conversation, DirectMessage, get_friend_ids

# Create namespace
api = Namespace('dm', description='Direct messaging operations')

# --- Swagger models ---

user_brief = api.model('DMUserBrief', {
    'id': fields.Integer(description='User ID'),
    'username': fields.String(description='Username'),
})

dm_model = api.model('DirectMessage', {
    'id': fields.Integer(description='Message ID'),
    'conversation_id': fields.Integer(description='Conversation ID'),
    'sender_id': fields.Integer(description='Sender user ID'),
    'sender': fields.Nested(user_brief, description='Sender info'),
    'body': fields.String(description='Message body'),
    'read_at': fields.String(description='Read timestamp (null if unread)'),
    'created_at': fields.String(description='Created timestamp'),
})

conversation_model = api.model('Conversation', {
    'id': fields.Integer(description='Conversation ID'),
    'other_user': fields.Nested(user_brief, description='Other participant'),
    'last_message': fields.Nested(dm_model, description='Most recent message', allow_null=True),
    'unread_count': fields.Integer(description='Unread messages from other user'),
    'created_at': fields.String(description='Created timestamp'),
    'updated_at': fields.String(description='Last activity timestamp'),
})

conversation_list_model = api.model('ConversationList', {
    'conversations': fields.List(fields.Nested(conversation_model)),
})

message_list_model = api.model('DMMessageList', {
    'messages': fields.List(fields.Nested(dm_model)),
    'has_more': fields.Boolean(description='Whether older messages exist'),
})

message_create_model = api.model('DMMessageCreate', {
    'body': fields.String(required=True, description='Message text', min_length=1),
})

unread_count_model = api.model('UnreadCount', {
    'unread_count': fields.Integer(description='Total unread DM count'),
})

error_model = api.model('DMError', {
    'error': fields.String(description='Error message'),
})


def _get_or_create_conversation(user_id, friend_id):
    """Get existing conversation or create a new one. Always stores min id as user1."""
    u1, u2 = (min(user_id, friend_id), max(user_id, friend_id))
    conv = Conversation.query.filter_by(user1_id=u1, user2_id=u2).first()
    if not conv:
        conv = Conversation(user1_id=u1, user2_id=u2)
        db.session.add(conv)
        db.session.commit()
    return conv


def _conversation_to_dict(conv, current_user_id):
    """Serialize a conversation with last_message and unread_count."""
    data = conv.to_dict(current_user_id=current_user_id)
    last_msg = conv.messages.order_by(DirectMessage.created_at.desc()).first()
    data['last_message'] = last_msg.to_dict() if last_msg else None
    data['unread_count'] = conv.messages.filter(
        DirectMessage.sender_id != current_user_id,
        DirectMessage.read_at.is_(None),
    ).count()
    return data


@api.route('/conversations')
class ConversationList(Resource):
    @api.doc('list_conversations', security='jwt')
    @api.response(200, 'Success', conversation_list_model)
    @jwt_required()
    def get(self):
        """List all conversations for the current user, ordered by most recent activity"""
        current_user_id = int(get_jwt_identity())

        convs = Conversation.query.filter(
            db.or_(
                Conversation.user1_id == current_user_id,
                Conversation.user2_id == current_user_id,
            )
        ).order_by(Conversation.updated_at.desc()).all()

        return {
            'conversations': [_conversation_to_dict(c, current_user_id) for c in convs],
        }


@api.route('/conversations/<int:friend_user_id>')
class ConversationGetOrCreate(Resource):
    @api.doc('get_or_create_conversation', security='jwt')
    @api.response(200, 'Success', conversation_model)
    @api.response(403, 'Not friends', error_model)
    @api.response(404, 'User not found', error_model)
    @jwt_required()
    def post(self, friend_user_id):
        """Get or create a conversation with a friend"""
        current_user_id = int(get_jwt_identity())

        if friend_user_id == current_user_id:
            return {'error': 'Cannot message yourself'}, 400

        friend = User.query.get(friend_user_id)
        if not friend:
            return {'error': 'User not found'}, 404

        friend_ids = get_friend_ids(current_user_id)
        if friend_user_id not in friend_ids:
            return {'error': 'You can only message accepted friends'}, 403

        conv = _get_or_create_conversation(current_user_id, friend_user_id)
        return _conversation_to_dict(conv, current_user_id)


@api.route('/conversations/<int:conversation_id>/messages')
class ConversationMessages(Resource):
    @api.doc('get_messages', security='jwt', params={
        'before': 'Message ID cursor — return messages older than this ID',
        'limit': 'Max messages to return (default 50, max 100)',
    })
    @api.response(200, 'Success', message_list_model)
    @api.response(403, 'Forbidden', error_model)
    @api.response(404, 'Not found', error_model)
    @jwt_required()
    def get(self, conversation_id):
        """Get messages in a conversation (paginated, newest first)"""
        current_user_id = int(get_jwt_identity())

        conv = Conversation.query.get(conversation_id)
        if not conv:
            return {'error': 'Conversation not found'}, 404

        if current_user_id not in (conv.user1_id, conv.user2_id):
            return {'error': 'Forbidden'}, 403

        before = request.args.get('before', type=int)
        limit = min(request.args.get('limit', 50, type=int), 100)

        query = DirectMessage.query.filter_by(conversation_id=conversation_id)
        if before:
            query = query.filter(DirectMessage.id < before)
        messages = query.order_by(DirectMessage.created_at.desc()).limit(limit + 1).all()

        has_more = len(messages) > limit
        messages = messages[:limit]
        messages.reverse()  # return oldest-first within the page

        return {
            'messages': [m.to_dict() for m in messages],
            'has_more': has_more,
        }

    @api.doc('send_message', security='jwt')
    @api.expect(message_create_model)
    @api.response(201, 'Message sent', dm_model)
    @api.response(400, 'Bad request', error_model)
    @api.response(403, 'Forbidden', error_model)
    @api.response(404, 'Not found', error_model)
    @jwt_required()
    def post(self, conversation_id):
        """Send a message in a conversation (REST fallback)"""
        current_user_id = int(get_jwt_identity())

        conv = Conversation.query.get(conversation_id)
        if not conv:
            return {'error': 'Conversation not found'}, 404

        if current_user_id not in (conv.user1_id, conv.user2_id):
            return {'error': 'Forbidden'}, 403

        data = request.get_json()
        body = (data.get('body') or '').strip()
        if not body:
            return {'error': 'body is required'}, 400

        msg = DirectMessage(
            conversation_id=conversation_id,
            sender_id=current_user_id,
            body=body,
        )
        db.session.add(msg)
        conv.updated_at = datetime.utcnow()
        db.session.commit()

        return msg.to_dict(), 201


@api.route('/conversations/<int:conversation_id>/read')
class ConversationMarkRead(Resource):
    @api.doc('mark_read', security='jwt')
    @api.response(200, 'Success')
    @api.response(403, 'Forbidden', error_model)
    @api.response(404, 'Not found', error_model)
    @jwt_required()
    def post(self, conversation_id):
        """Mark all unread messages in this conversation as read"""
        current_user_id = int(get_jwt_identity())

        conv = Conversation.query.get(conversation_id)
        if not conv:
            return {'error': 'Conversation not found'}, 404

        if current_user_id not in (conv.user1_id, conv.user2_id):
            return {'error': 'Forbidden'}, 403

        now = datetime.utcnow()
        updated = DirectMessage.query.filter(
            DirectMessage.conversation_id == conversation_id,
            DirectMessage.sender_id != current_user_id,
            DirectMessage.read_at.is_(None),
        ).update({'read_at': now}, synchronize_session='fetch')

        db.session.commit()

        return {'marked_read': updated}


@api.route('/unread-count')
class UnreadCount(Resource):
    @api.doc('unread_count', security='jwt')
    @api.response(200, 'Success', unread_count_model)
    @jwt_required()
    def get(self):
        """Get total unread DM count across all conversations"""
        current_user_id = int(get_jwt_identity())

        count = DirectMessage.query.join(Conversation).filter(
            db.or_(
                Conversation.user1_id == current_user_id,
                Conversation.user2_id == current_user_id,
            ),
            DirectMessage.sender_id != current_user_id,
            DirectMessage.read_at.is_(None),
        ).count()

        return {'unread_count': count}
