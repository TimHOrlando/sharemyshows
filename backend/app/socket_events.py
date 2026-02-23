"""
WebSocket Integration with Flask-SocketIO
Handles real-time chat and user presence for shows
"""

from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from flask import request
from flask_jwt_extended import decode_token
from app.models import db, ChatMessage, ShowCheckin, User, Show, get_friend_ids
from datetime import datetime
import os

# Initialize SocketIO
socketio = SocketIO(
    cors_allowed_origins=os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(','),
    async_mode='eventlet',
    logger=True,
    engineio_logger=True
)

# Store active users per show
# Format: {show_id: {user_id: {'username': str, 'sid': str}}}
active_users = {}


def get_sibling_show_ids(show_id):
    """Get all show IDs for the same concert (same artist, venue, date)."""
    show = Show.query.get(show_id)
    if not show:
        return [show_id]
    siblings = Show.query.filter_by(
        artist_id=show.artist_id,
        venue_id=show.venue_id,
        date=show.date
    ).with_entities(Show.id).all()
    return [s.id for s in siblings]


def init_socketio(app):
    """Initialize SocketIO with the Flask app"""
    socketio.init_app(app)
    return socketio


def get_user_from_token():
    """Extract user from JWT token in socket connection"""
    try:
        # Get token from cookie or query string
        token = None
        
        # Try to get from cookies
        if 'access_token_cookie' in request.cookies:
            token = request.cookies.get('access_token_cookie')
        
        # Try to get from query string (for WebSocket connections)
        elif 'token' in request.args:
            token = request.args.get('token')
        
        if not token:
            return None
        
        # Decode JWT token
        decoded_token = decode_token(token)
        user_id = int(decoded_token['sub'])
        
        # Get user from database
        user = User.query.get(user_id)
        return user
        
    except Exception as e:
        print(f"Error getting user from token: {e}")
        return None


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    user = get_user_from_token()
    
    if not user:
        print("Unauthorized connection attempt")
        return False  # Reject connection
    
    print(f"Client connected: {user.username} (sid: {request.sid})")
    emit('connected', {'message': 'Connected to ShareMyShows', 'username': user.username})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    user = get_user_from_token()

    if user:
        friend_ids = get_friend_ids(user.id)

        # Remove user from all show rooms
        for show_id in list(active_users.keys()):
            if user.id in active_users[show_id]:
                # Clear location in DB and notify friends before removing
                try:
                    checkin = ShowCheckin.query.filter_by(
                        user_id=user.id,
                        show_id=show_id,
                        is_active=True
                    ).first()
                    if checkin and checkin.latitude is not None:
                        checkin.latitude = None
                        checkin.longitude = None
                        checkin.last_location_update = None
                        db.session.commit()

                        # Notify friends across sibling shows (same concert)
                        sibling_ids = get_sibling_show_ids(show_id)
                        for sid in sibling_ids:
                            if sid in active_users:
                                for friend_id, info in active_users[sid].items():
                                    if friend_id in friend_ids:
                                        emit('location_stopped', {
                                            'user_id': user.id,
                                            'username': user.username
                                        }, to=info['sid'])
                except Exception as e:
                    db.session.rollback()
                    print(f"Error clearing location on disconnect: {e}")

                del active_users[show_id][user.id]

                # Clean up empty show rooms
                if not active_users[show_id]:
                    del active_users[show_id]
                else:
                    # Notify other users in the room
                    emit('user_left', {
                        'user_id': user.id,
                        'username': user.username,
                        'active_users': list(active_users[show_id].values())
                    }, room=f'show_{show_id}')

        print(f"Client disconnected: {user.username} (sid: {request.sid})")


@socketio.on('join_show')
def handle_join_show(data):
    """Handle user joining a show chat room"""
    user = get_user_from_token()
    
    if not user:
        emit('error', {'message': 'Unauthorized'})
        return
    
    show_id = data.get('show_id')
    
    if not show_id:
        emit('error', {'message': 'Missing show_id'})
        return
    
    # Verify show exists
    show = Show.query.get(show_id)
    if not show:
        emit('error', {'message': 'Show not found'})
        return
    
    # Join the room
    room_name = f'show_{show_id}'
    join_room(room_name)
    
    # Add user to active users
    if show_id not in active_users:
        active_users[show_id] = {}
    
    active_users[show_id][user.id] = {
        'user_id': user.id,
        'username': user.username,
        'sid': request.sid
    }
    
    # Check in user to show (optional - tracks presence in database)
    existing_checkin = ShowCheckin.query.filter_by(
        user_id=user.id,
        show_id=show_id,
        is_active=True
    ).first()
    
    if not existing_checkin:
        checkin = ShowCheckin(
            user_id=user.id,
            show_id=show_id
        )
        db.session.add(checkin)
        db.session.commit()
    
    # Get recent chat messages (last 50)
    recent_messages = ChatMessage.query.filter_by(show_id=show_id)\
        .order_by(ChatMessage.created_at.desc())\
        .limit(50)\
        .all()
    
    recent_messages.reverse()  # Show oldest to newest
    
    # Send recent messages to the user
    emit('message_history', {
        'messages': [msg.to_dict() for msg in recent_messages]
    })
    
    # Notify other users in the room
    emit('user_joined', {
        'user_id': user.id,
        'username': user.username,
        'message': f'{user.username} joined the chat',
        'active_users': list(active_users[show_id].values())
    }, room=room_name, include_self=False)
    
    # Send active users list to the joining user
    emit('active_users', {
        'active_users': list(active_users[show_id].values()),
        'count': len(active_users[show_id])
    })
    
    print(f"{user.username} joined show {show_id} chat (Room: {room_name})")


@socketio.on('leave_show')
def handle_leave_show(data):
    """Handle user leaving a show chat room"""
    user = get_user_from_token()
    
    if not user:
        emit('error', {'message': 'Unauthorized'})
        return
    
    show_id = data.get('show_id')
    
    if not show_id:
        emit('error', {'message': 'Missing show_id'})
        return
    
    room_name = f'show_{show_id}'
    leave_room(room_name)
    
    # Remove user from active users
    if show_id in active_users and user.id in active_users[show_id]:
        del active_users[show_id][user.id]
        
        # Clean up empty show rooms
        if not active_users[show_id]:
            del active_users[show_id]
        else:
            # Notify other users
            emit('user_left', {
                'user_id': user.id,
                'username': user.username,
                'message': f'{user.username} left the chat',
                'active_users': list(active_users[show_id].values())
            }, room=room_name)
    
    # Check out user from show
    checkin = ShowCheckin.query.filter_by(
        user_id=user.id,
        show_id=show_id,
        is_active=True
    ).first()
    
    if checkin:
        checkin.checked_out_at = datetime.utcnow()
        checkin.is_active = False
        db.session.commit()
    
    print(f"{user.username} left show {show_id} chat")


@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a chat message"""
    user = get_user_from_token()
    
    if not user:
        emit('error', {'message': 'Unauthorized'})
        return
    
    show_id = data.get('show_id')
    message_text = data.get('message')
    
    if not show_id or not message_text:
        emit('error', {'message': 'Missing show_id or message'})
        return
    
    # Verify show exists
    show = Show.query.get(show_id)
    if not show:
        emit('error', {'message': 'Show not found'})
        return
    
    # Verify user is in the room
    room_name = f'show_{show_id}'
    if room_name not in rooms():
        emit('error', {'message': 'Not in show chat room'})
        return
    
    # Create chat message in database
    message = ChatMessage(
        show_id=show_id,
        user_id=user.id,
        message=message_text
    )
    
    try:
        db.session.add(message)
        db.session.commit()
        
        # Broadcast message to all users in the room
        emit('new_message', {
            'id': message.id,
            'show_id': show_id,
            'user_id': user.id,
            'username': user.username,
            'message': message_text,
            'created_at': message.created_at.isoformat()
        }, room=room_name)
        
        print(f"Message from {user.username} in show {show_id}: {message_text[:50]}...")
        
    except Exception as e:
        db.session.rollback()
        emit('error', {'message': 'Failed to send message', 'details': str(e)})
        print(f"Error sending message: {e}")


@socketio.on('new_comment')
def handle_new_comment(data):
    """Broadcast a new comment to all users viewing the same show"""
    user = get_user_from_token()

    if not user:
        emit('error', {'message': 'Unauthorized'})
        return

    show_id = data.get('show_id')
    if not show_id:
        emit('error', {'message': 'Missing show_id'})
        return

    room_name = f'show_{show_id}'

    # Broadcast to all users in the show room (including sender for confirmation)
    emit('comment_added', {
        'show_id': show_id,
        'photo_id': data.get('photo_id'),
        'comment': data.get('comment'),
        'user_id': user.id,
        'username': user.username,
    }, room=room_name, include_self=False)


@socketio.on('typing')
def handle_typing(data):
    """Handle user typing indicator"""
    user = get_user_from_token()
    
    if not user:
        return
    
    show_id = data.get('show_id')
    is_typing = data.get('is_typing', False)
    
    if not show_id:
        return
    
    room_name = f'show_{show_id}'
    
    # Broadcast typing indicator to other users in the room
    emit('user_typing', {
        'user_id': user.id,
        'username': user.username,
        'is_typing': is_typing
    }, room=room_name, include_self=False)


@socketio.on('get_active_users')
def handle_get_active_users(data):
    """Get list of active users in a show"""
    user = get_user_from_token()
    
    if not user:
        emit('error', {'message': 'Unauthorized'})
        return
    
    show_id = data.get('show_id')
    
    if not show_id:
        emit('error', {'message': 'Missing show_id'})
        return
    
    users = []
    if show_id in active_users:
        users = list(active_users[show_id].values())
    
    emit('active_users', {
        'show_id': show_id,
        'active_users': users,
        'count': len(users)
    })


@socketio.on('update_location')
def handle_update_location(data):
    """Handle user sharing their live location at a show"""
    user = get_user_from_token()

    if not user:
        emit('error', {'message': 'Unauthorized'})
        return

    show_id = data.get('show_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if not show_id or latitude is None or longitude is None:
        emit('error', {'message': 'Missing show_id, latitude, or longitude'})
        return

    try:
        checkin = ShowCheckin.query.filter_by(
            user_id=user.id,
            show_id=show_id,
            is_active=True
        ).first()

        if not checkin:
            emit('error', {'message': 'Not checked in to this show'})
            return

        checkin.latitude = latitude
        checkin.longitude = longitude
        checkin.last_location_update = datetime.utcnow()
        db.session.commit()

        # Emit location to accepted friends across all sibling shows (same concert)
        friend_ids = get_friend_ids(user.id)
        sibling_ids = get_sibling_show_ids(show_id)
        for sid in sibling_ids:
            if sid in active_users:
                for friend_id, info in active_users[sid].items():
                    if friend_id in friend_ids:
                        emit('location_update', {
                            'user_id': user.id,
                            'username': user.username,
                            'latitude': latitude,
                            'longitude': longitude,
                            'updated_at': checkin.last_location_update.isoformat()
                        }, to=info['sid'])

    except Exception as e:
        db.session.rollback()
        emit('error', {'message': 'Failed to update location', 'details': str(e)})
        print(f"Error updating location: {e}")


@socketio.on('stop_location')
def handle_stop_location(data):
    """Handle user stopping location sharing"""
    user = get_user_from_token()

    if not user:
        emit('error', {'message': 'Unauthorized'})
        return

    show_id = data.get('show_id')

    if not show_id:
        emit('error', {'message': 'Missing show_id'})
        return

    try:
        checkin = ShowCheckin.query.filter_by(
            user_id=user.id,
            show_id=show_id,
            is_active=True
        ).first()

        if checkin:
            checkin.latitude = None
            checkin.longitude = None
            checkin.last_location_update = None
            db.session.commit()

        # Notify friends across all sibling shows (same concert)
        friend_ids = get_friend_ids(user.id)
        sibling_ids = get_sibling_show_ids(show_id)
        for sid in sibling_ids:
            if sid in active_users:
                for friend_id, info in active_users[sid].items():
                    if friend_id in friend_ids:
                        emit('location_stopped', {
                            'user_id': user.id,
                            'username': user.username
                        }, to=info['sid'])

    except Exception as e:
        db.session.rollback()
        emit('error', {'message': 'Failed to stop location', 'details': str(e)})
        print(f"Error stopping location: {e}")


@socketio.on('get_friends_locations')
def handle_get_friends_locations(data):
    """Get locations of friends checked into the same show"""
    user = get_user_from_token()

    if not user:
        emit('error', {'message': 'Unauthorized'})
        return

    show_id = data.get('show_id')

    if not show_id:
        emit('error', {'message': 'Missing show_id'})
        return

    friend_ids = get_friend_ids(user.id)
    sibling_ids = get_sibling_show_ids(show_id)

    # Query active checkins with location data for friends at this concert
    checkins = ShowCheckin.query.filter(
        ShowCheckin.show_id.in_(sibling_ids),
        ShowCheckin.is_active == True,
        ShowCheckin.latitude.isnot(None),
        ShowCheckin.longitude.isnot(None),
        ShowCheckin.user_id.in_(friend_ids)
    ).all()

    friends = []
    for checkin in checkins:
        friend = User.query.get(checkin.user_id)
        if friend:
            friends.append({
                'user_id': friend.id,
                'username': friend.username,
                'latitude': checkin.latitude,
                'longitude': checkin.longitude,
                'updated_at': checkin.last_location_update.isoformat() if checkin.last_location_update else None
            })

    emit('friends_locations', {'friends': friends})


# Error handler
@socketio.on_error_default
def default_error_handler(e):
    """Handle WebSocket errors"""
    print(f"WebSocket error: {e}")
    emit('error', {'message': 'An error occurred', 'details': str(e)})
