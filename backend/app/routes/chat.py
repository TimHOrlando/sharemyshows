from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, ChatMessage, Show, ShowCheckin
from datetime import datetime

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('/show/<int:show_id>/messages', methods=['GET'])
@jwt_required()
def get_show_messages(show_id):
    show = Show.query.get(show_id)
    
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    limit = request.args.get('limit', 50, type=int)
    before_id = request.args.get('before', type=int)
    
    query = ChatMessage.query.filter_by(show_id=show_id)
    
    if before_id:
        query = query.filter(ChatMessage.id < before_id)
    
    messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
    
    messages.reverse()
    
    return jsonify([msg.to_dict() for msg in messages]), 200

@chat_bp.route('/show/<int:show_id>/messages', methods=['POST'])
@jwt_required()
def send_message(show_id):
    user_id = int(get_jwt_identity())
    
    show = Show.query.get(show_id)
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Missing message content'}), 400
    
    message = ChatMessage(
        show_id=show_id,
        user_id=user_id,
        message=data['message']
    )
    
    try:
        db.session.add(message)
        db.session.commit()
        return jsonify(message.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to send message', 'details': str(e)}), 500

@chat_bp.route('/show/<int:show_id>/active-users', methods=['GET'])
@jwt_required()
def get_active_chat_users(show_id):
    show = Show.query.get(show_id)
    
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    active_checkins = ShowCheckin.query.filter_by(
        show_id=show_id,
        is_active=True
    ).all()
    
    users = []
    for checkin in active_checkins:
        if checkin.user:
            users.append({
                'id': checkin.user.id,
                'username': checkin.user.username,
                'checked_in_at': checkin.checked_in_at.isoformat() if checkin.checked_in_at else None
            })
    
    return jsonify(users), 200
