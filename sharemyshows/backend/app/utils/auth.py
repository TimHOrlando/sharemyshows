"""
Authentication utilities
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app import redis_client
from app.models.user import User
from datetime import datetime, timedelta


def get_current_user():
    """
    Get the current authenticated user from JWT
    
    Returns:
        User: Current user object or None
    """
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        return User.query.get(user_id)
    except Exception:
        return None


def admin_required(fn):
    """
    Decorator to require admin privileges
    
    Usage:
        @admin_required
        def admin_only_route():
            pass
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not getattr(user, 'is_admin', False):
            return jsonify({
                'error': 'Forbidden',
                'message': 'Admin privileges required'
            }), 403
        
        return fn(*args, **kwargs)
    
    return wrapper


def check_rate_limit(user_id, action, max_attempts=5, window_seconds=900):
    """
    Check if user has exceeded rate limit for an action
    
    Args:
        user_id: User ID
        action: Action name (e.g., 'login_attempt', 'password_reset')
        max_attempts: Maximum attempts allowed
        window_seconds: Time window in seconds
        
    Returns:
        tuple: (is_allowed, attempts_left, retry_after_seconds)
    """
    key = f'rate_limit:{action}:{user_id}'
    
    try:
        # Get current attempt count
        attempts = redis_client.get(key)
        attempts = int(attempts) if attempts else 0
        
        # Check if limit exceeded
        if attempts >= max_attempts:
            ttl = redis_client.ttl(key)
            return False, 0, ttl if ttl > 0 else window_seconds
        
        # Increment attempt count
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        pipe.execute()
        
        attempts_left = max_attempts - (attempts + 1)
        return True, attempts_left, 0
        
    except Exception as e:
        # If Redis fails, allow the request (fail open)
        print(f'Rate limit check failed: {e}')
        return True, max_attempts, 0


def reset_rate_limit(user_id, action):
    """
    Reset rate limit for a user action
    
    Args:
        user_id: User ID
        action: Action name
    """
    key = f'rate_limit:{action}:{user_id}'
    try:
        redis_client.delete(key)
    except Exception as e:
        print(f'Rate limit reset failed: {e}')


def revoke_token(jti, expires_delta):
    """
    Revoke a JWT token by adding it to the blacklist
    
    Args:
        jti: JWT ID (unique token identifier)
        expires_delta: Token expiration time delta
    """
    try:
        redis_client.setex(
            f'revoked_token:{jti}',
            expires_delta,
            'true'
        )
    except Exception as e:
        print(f'Token revocation failed: {e}')


def is_token_revoked(jti):
    """
    Check if a token has been revoked
    
    Args:
        jti: JWT ID
        
    Returns:
        bool: True if revoked, False otherwise
    """
    try:
        return redis_client.get(f'revoked_token:{jti}') is not None
    except Exception as e:
        print(f'Token revocation check failed: {e}')
        return False


def create_user_session(user_id, token):
    """
    Create a user session in Redis
    
    Args:
        user_id: User ID
        token: JWT token
    """
    try:
        session_key = f'user_session:{user_id}'
        session_data = {
            'token': token,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat()
        }
        redis_client.setex(
            session_key,
            timedelta(days=7),  # Match refresh token expiry
            str(session_data)
        )
    except Exception as e:
        print(f'Session creation failed: {e}')


def update_user_activity(user_id):
    """
    Update user's last activity timestamp
    
    Args:
        user_id: User ID
    """
    try:
        session_key = f'user_session:{user_id}'
        if redis_client.exists(session_key):
            # Extend session TTL
            redis_client.expire(session_key, timedelta(days=7))
    except Exception as e:
        print(f'Activity update failed: {e}')


def delete_user_session(user_id):
    """
    Delete user session from Redis
    
    Args:
        user_id: User ID
    """
    try:
        session_key = f'user_session:{user_id}'
        redis_client.delete(session_key)
    except Exception as e:
        print(f'Session deletion failed: {e}')
