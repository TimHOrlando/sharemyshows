from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, User, Friendship
from sqlalchemy import or_, and_

friends_bp = Blueprint('friends', __name__, url_prefix='/api/friends')

@friends_bp.route('/search', methods=['GET'])
@jwt_required()
def search_users():
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({'error': 'Search query must be at least 2 characters'}), 400
    
    user_id = int(get_jwt_identity())
    
    users = User.query.filter(
        and_(
            User.id != user_id,
            or_(
                User.username.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%')
            )
        )
    ).limit(20).all()
    
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email
    } for user in users]), 200

@friends_bp.route('/request', methods=['POST'])
@jwt_required()
def send_friend_request():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data or 'friend_id' not in data:
        return jsonify({'error': 'Missing friend_id'}), 400
    
    friend_id = data['friend_id']
    
    friend = User.query.get(friend_id)
    if not friend:
        return jsonify({'error': 'User not found'}), 404
    
    if user_id == friend_id:
        return jsonify({'error': 'Cannot send friend request to yourself'}), 400
    
    existing = Friendship.query.filter(
        or_(
            and_(Friendship.user_id == user_id, Friendship.friend_id == friend_id),
            and_(Friendship.user_id == friend_id, Friendship.friend_id == user_id)
        )
    ).first()
    
    if existing:
        if existing.status == 'accepted':
            return jsonify({'error': 'Already friends'}), 400
        elif existing.status == 'pending':
            return jsonify({'error': 'Friend request already pending'}), 400
    
    friendship = Friendship(
        user_id=user_id,
        friend_id=friend_id,
        status='pending'
    )
    
    try:
        db.session.add(friendship)
        db.session.commit()
        return jsonify(friendship.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to send friend request', 'details': str(e)}), 500

@friends_bp.route('/request/<int:request_id>/accept', methods=['POST'])
@jwt_required()
def accept_friend_request(request_id):
    user_id = int(get_jwt_identity())
    
    friendship = Friendship.query.filter_by(
        id=request_id,
        friend_id=user_id,
        status='pending'
    ).first()
    
    if not friendship:
        return jsonify({'error': 'Friend request not found'}), 404
    
    friendship.status = 'accepted'
    
    try:
        db.session.commit()
        return jsonify(friendship.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to accept friend request', 'details': str(e)}), 500

@friends_bp.route('/request/<int:request_id>/reject', methods=['POST'])
@jwt_required()
def reject_friend_request(request_id):
    user_id = int(get_jwt_identity())
    
    friendship = Friendship.query.filter_by(
        id=request_id,
        friend_id=user_id,
        status='pending'
    ).first()
    
    if not friendship:
        return jsonify({'error': 'Friend request not found'}), 404
    
    try:
        db.session.delete(friendship)
        db.session.commit()
        return jsonify({'message': 'Friend request rejected'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to reject friend request', 'details': str(e)}), 500

@friends_bp.route('', methods=['GET'])
@jwt_required()
def get_friends():
    user_id = int(get_jwt_identity())
    
    friendships = Friendship.query.filter(
        and_(
            or_(
                Friendship.user_id == user_id,
                Friendship.friend_id == user_id
            ),
            Friendship.status == 'accepted'
        )
    ).all()
    
    friends = []
    for friendship in friendships:
        if friendship.user_id == user_id:
            friend = User.query.get(friendship.friend_id)
        else:
            friend = User.query.get(friendship.user_id)
        
        if friend:
            friends.append({
                'id': friend.id,
                'username': friend.username,
                'email': friend.email
            })
    
    return jsonify(friends), 200

@friends_bp.route('/requests', methods=['GET'])
@jwt_required()
def get_friend_requests():
    user_id = int(get_jwt_identity())
    
    requests = Friendship.query.filter_by(
        friend_id=user_id,
        status='pending'
    ).all()
    
    result = []
    for req in requests:
        sender = User.query.get(req.user_id)
        if sender:
            result.append({
                'request_id': req.id,
                'user': {
                    'id': sender.id,
                    'username': sender.username,
                    'email': sender.email
                },
                'created_at': req.created_at.isoformat() if req.created_at else None
            })
    
    return jsonify(result), 200

@friends_bp.route('/<int:friend_id>', methods=['DELETE'])
@jwt_required()
def remove_friend(friend_id):
    user_id = int(get_jwt_identity())
    
    friendship = Friendship.query.filter(
        and_(
            or_(
                and_(Friendship.user_id == user_id, Friendship.friend_id == friend_id),
                and_(Friendship.user_id == friend_id, Friendship.friend_id == user_id)
            ),
            Friendship.status == 'accepted'
        )
    ).first()
    
    if not friendship:
        return jsonify({'error': 'Friendship not found'}), 404
    
    try:
        db.session.delete(friendship)
        db.session.commit()
        return jsonify({'message': 'Friend removed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to remove friend', 'details': str(e)}), 500
