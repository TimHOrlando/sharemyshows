"""
Friends API Routes - Flask-RESTX Implementation
Handles friend searches, requests, accept/reject, and friend list management
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.models import db, User, Friendship, Show

# Create namespace
api = Namespace('friends', description='Friend management operations')

# Query parameters
search_parser = api.parser()
search_parser.add_argument('query', type=str, required=True, location='args', help='Search query for username or email')

# Models
user_model = api.model('User', {
    'id': fields.Integer(description='User ID'),
    'username': fields.String(description='Username'),
    'email': fields.String(description='Email'),
    'created_at': fields.DateTime(description='Account creation time')
})

user_list_model = api.model('UserList', {
    'users': fields.List(fields.Nested(user_model)),
    'total': fields.Integer(description='Total users found')
})

friendship_model = api.model('Friendship', {
    'id': fields.Integer(description='Friendship ID'),
    'user_id': fields.Integer(description='User ID'),
    'friend_id': fields.Integer(description='Friend ID'),
    'status': fields.String(description='Status: pending, accepted'),
    'created_at': fields.DateTime(description='Request time'),
    'friend': fields.Nested(user_model, description='Friend user info')
})

friendship_list_model = api.model('FriendshipList', {
    'friends': fields.List(fields.Nested(friendship_model)),
    'total': fields.Integer(description='Total friends')
})

friend_request_model = api.model('FriendRequest', {
    'friend_id': fields.Integer(required=True, description='ID of user to befriend')
})

message_response = api.model('MessageResponse', {
    'message': fields.String(description='Response message')
})

error_response = api.model('ErrorResponse', {
    'error': fields.String(description='Error message')
})


@api.route('/search')
class FriendSearch(Resource):
    @api.doc('search_users', security='jwt')
    @api.expect(search_parser)
    @api.response(200, 'Success', user_list_model)
    @api.response(400, 'Bad request', error_response)
    @jwt_required()
    def get(self):
        """Search for users by username or email"""
        current_user_id = int(get_jwt_identity())
        
        query = request.args.get('query', '').strip()
        if not query:
            return {'error': 'query parameter is required'}, 400
        
        # Search users by username or email (excluding current user)
        users = User.query.filter(
            db.and_(
                User.id != current_user_id,
                db.or_(
                    User.username.ilike(f'%{query}%'),
                    User.email.ilike(f'%{query}%')
                )
            )
        ).limit(20).all()
        
        return {
            'users': [user.to_dict() for user in users],
            'total': len(users)
        }


@api.route('/request')
class FriendRequestCreate(Resource):
    @api.doc('send_friend_request', security='jwt')
    @api.expect(friend_request_model)
    @api.response(201, 'Friend request sent', friendship_model)
    @api.response(400, 'Bad request', error_response)
    @api.response(404, 'User not found', error_response)
    @jwt_required()
    def post(self):
        """Send a friend request"""
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        friend_id = data.get('friend_id')
        if not friend_id:
            return {'error': 'friend_id is required'}, 400
        
        if friend_id == current_user_id:
            return {'error': 'Cannot befriend yourself'}, 400
        
        friend = User.query.get(friend_id)
        if not friend:
            return {'error': 'User not found'}, 404
        
        # Check if friendship already exists
        existing = Friendship.query.filter(
            db.or_(
                db.and_(Friendship.user_id == current_user_id, Friendship.friend_id == friend_id),
                db.and_(Friendship.user_id == friend_id, Friendship.friend_id == current_user_id)
            )
        ).first()
        
        if existing:
            return {'error': 'Friend request already exists or you are already friends'}, 400
        
        friendship = Friendship(
            user_id=current_user_id,
            friend_id=friend_id,
            status='pending'
        )
        
        db.session.add(friendship)
        db.session.commit()
        
        result = friendship.to_dict()
        result['friend'] = friend.to_dict()
        
        return result, 201


@api.route('/request/<int:request_id>/accept')
class FriendRequestAccept(Resource):
    @api.doc('accept_friend_request', security='jwt')
    @api.response(200, 'Friend request accepted', friendship_model)
    @api.response(403, 'Forbidden', error_response)
    @api.response(404, 'Request not found', error_response)
    @jwt_required()
    def post(self, request_id):
        """Accept a friend request"""
        current_user_id = int(get_jwt_identity())
        
        friendship = Friendship.query.get(request_id)
        if not friendship:
            return {'error': 'Friend request not found'}, 404
        
        # Only the recipient can accept
        if friendship.friend_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        if friendship.status == 'accepted':
            return {'error': 'Already accepted'}, 400
        
        friendship.status = 'accepted'
        db.session.commit()
        
        # Get friend info
        friend = User.query.get(friendship.user_id)
        result = friendship.to_dict()
        result['friend'] = friend.to_dict()
        
        return result


@api.route('/request/<int:request_id>/reject')
class FriendRequestReject(Resource):
    @api.doc('reject_friend_request', security='jwt')
    @api.response(200, 'Friend request rejected', message_response)
    @api.response(403, 'Forbidden', error_response)
    @api.response(404, 'Request not found', error_response)
    @jwt_required()
    def post(self, request_id):
        """Reject a friend request"""
        current_user_id = int(get_jwt_identity())
        
        friendship = Friendship.query.get(request_id)
        if not friendship:
            return {'error': 'Friend request not found'}, 404
        
        # Only the recipient can reject
        if friendship.friend_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        db.session.delete(friendship)
        db.session.commit()
        
        return {'message': 'Friend request rejected'}


@api.route('')
class FriendList(Resource):
    @api.doc('get_friends', security='jwt')
    @api.response(200, 'Success', friendship_list_model)
    @jwt_required()
    def get(self):
        """Get list of accepted friends"""
        current_user_id = int(get_jwt_identity())
        
        # Get friendships where current user is either user_id or friend_id and status is accepted
        friendships = Friendship.query.filter(
            db.and_(
                db.or_(
                    Friendship.user_id == current_user_id,
                    Friendship.friend_id == current_user_id
                ),
                Friendship.status == 'accepted'
            )
        ).all()
        
        results = []
        for friendship in friendships:
            # Determine which user is the friend
            friend_id = friendship.friend_id if friendship.user_id == current_user_id else friendship.user_id
            friend = User.query.get(friend_id)
            
            friend_dict = friendship.to_dict()
            friend_dict['friend'] = friend.to_dict()
            results.append(friend_dict)
        
        return {
            'friends': results,
            'total': len(results)
        }


@api.route('/requests')
class FriendRequestList(Resource):
    @api.doc('get_friend_requests', security='jwt')
    @api.response(200, 'Success', friendship_list_model)
    @jwt_required()
    def get(self):
        """Get pending friend requests (received)"""
        current_user_id = int(get_jwt_identity())
        
        # Get pending requests where current user is the friend_id (recipient)
        friendships = Friendship.query.filter_by(
            friend_id=current_user_id,
            status='pending'
        ).all()
        
        results = []
        for friendship in friendships:
            requester = User.query.get(friendship.user_id)
            friend_dict = friendship.to_dict()
            friend_dict['friend'] = requester.to_dict()
            results.append(friend_dict)
        
        return {
            'friends': results,
            'total': len(results)
        }


@api.route('/<int:friendship_id>')
class FriendshipDelete(Resource):
    @api.doc('remove_friend', security='jwt')
    @api.response(200, 'Friend removed', message_response)
    @api.response(403, 'Forbidden', error_response)
    @api.response(404, 'Friendship not found', error_response)
    @jwt_required()
    def delete(self, friendship_id):
        """Remove a friend"""
        current_user_id = int(get_jwt_identity())
        
        friendship = Friendship.query.get(friendship_id)
        if not friendship:
            return {'error': 'Friendship not found'}, 404
        
        # User can only remove their own friendships
        if friendship.user_id != current_user_id and friendship.friend_id != current_user_id:
            return {'error': 'Not authorized'}, 403
        
        db.session.delete(friendship)
        db.session.commit()

        return {'message': 'Friend removed'}


@api.route('/<int:friend_user_id>/shows')
class FriendShows(Resource):
    @api.doc('get_friend_shows', security='jwt')
    @api.response(200, 'Success')
    @api.response(403, 'Not friends', error_response)
    @api.response(404, 'User not found', error_response)
    @jwt_required()
    def get(self, friend_user_id):
        """Get a friend's shows (must be accepted friends)"""
        current_user_id = int(get_jwt_identity())

        friend = User.query.get(friend_user_id)
        if not friend:
            return {'error': 'User not found'}, 404

        # Verify accepted friendship
        friendship = Friendship.query.filter(
            db.or_(
                db.and_(Friendship.user_id == current_user_id, Friendship.friend_id == friend_user_id),
                db.and_(Friendship.user_id == friend_user_id, Friendship.friend_id == current_user_id)
            ),
            Friendship.status == 'accepted'
        ).first()

        if not friendship:
            return {'error': 'Not friends with this user'}, 403

        shows = Show.query.filter_by(user_id=friend_user_id).order_by(Show.date.desc()).all()

        return {
            'friend': friend.to_dict(),
            'shows': [s.to_dict(viewer_id=current_user_id) for s in shows],
            'total': len(shows)
        }
