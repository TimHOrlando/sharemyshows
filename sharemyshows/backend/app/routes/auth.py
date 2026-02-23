"""
Authentication routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from app import db
from app.models.user import User
from app.utils.validators import (
    validate_email_format,
    validate_password_strength,
    validate_username,
    sanitize_input
)
from app.utils.auth import (
    get_current_user,
    check_rate_limit,
    reset_rate_limit,
    revoke_token,
    create_user_session,
    delete_user_session
)
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    
    Request Body:
        {
            "email": "user@example.com",
            "username": "username",
            "password": "SecurePass123!"
        }
    
    Returns:
        201: User created successfully
        400: Validation error
        409: User already exists
    """
    data = request.get_json()
    
    # Validate required fields
    if not all(k in data for k in ('email', 'username', 'password')):
        return jsonify({
            'error': 'Validation Error',
            'message': 'Email, username, and password are required'
        }), 400
    
    # Sanitize inputs
    email = sanitize_input(data['email'], max_length=255)
    username = sanitize_input(data['username'], max_length=100)
    password = data['password']
    
    # Validate email
    is_valid, normalized_email, error = validate_email_format(email)
    if not is_valid:
        return jsonify({
            'error': 'Validation Error',
            'message': f'Invalid email: {error}'
        }), 400
    
    # Validate username
    is_valid, error = validate_username(username)
    if not is_valid:
        return jsonify({
            'error': 'Validation Error',
            'message': error
        }), 400
    
    # Validate password strength
    is_valid, error = validate_password_strength(password)
    if not is_valid:
        return jsonify({
            'error': 'Validation Error',
            'message': error
        }), 400
    
    # Check if user already exists
    if User.query.filter_by(email=normalized_email).first():
        return jsonify({
            'error': 'Conflict',
            'message': 'Email already registered'
        }), 409
    
    if User.query.filter_by(username=username).first():
        return jsonify({
            'error': 'Conflict',
            'message': 'Username already taken'
        }), 409
    
    # Create new user
    user = User(
        email=normalized_email,
        username=username
    )
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict(include_email=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Server Error',
            'message': 'Failed to create user'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user and return JWT tokens
    
    Request Body:
        {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }
    
    Returns:
        200: Login successful with tokens
        401: Invalid credentials
        429: Too many login attempts
    """
    data = request.get_json()
    
    # Validate required fields
    if not all(k in data for k in ('email', 'password')):
        return jsonify({
            'error': 'Validation Error',
            'message': 'Email and password are required'
        }), 400
    
    email = sanitize_input(data['email'])
    password = data['password']
    
    # Find user
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Invalid email or password'
        }), 401
    
    # Check rate limiting
    is_allowed, attempts_left, retry_after = check_rate_limit(
        user.id,
        'login_attempt',
        max_attempts=5,
        window_seconds=900  # 15 minutes
    )
    
    if not is_allowed:
        return jsonify({
            'error': 'Too Many Requests',
            'message': f'Too many login attempts. Try again in {retry_after} seconds',
            'retry_after': retry_after
        }), 429
    
    # Check password
    if not user.check_password(password):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Invalid email or password',
            'attempts_left': attempts_left
        }), 401
    
    # Check if user is active
    if not user.is_active:
        return jsonify({
            'error': 'Forbidden',
            'message': 'Account is deactivated'
        }), 403
    
    # Reset rate limit on successful login
    reset_rate_limit(user.id, 'login_attempt')
    
    # Create tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    # Create session
    create_user_session(user.id, access_token)
    
    # Update last login
    user.update_last_login()
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(include_email=True)
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user by revoking the JWT token
    
    Returns:
        200: Logout successful
    """
    user_id = get_jwt_identity()
    jti = get_jwt()['jti']
    
    # Revoke the token
    revoke_token(jti, timedelta(hours=1))
    
    # Delete user session
    delete_user_session(user_id)
    
    return jsonify({
        'message': 'Logout successful'
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token
    
    Returns:
        200: New access token
    """
    user_id = get_jwt_identity()
    
    # Create new access token
    access_token = create_access_token(identity=user_id)
    
    return jsonify({
        'access_token': access_token
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    """
    Get current user information
    
    Returns:
        200: User information
        404: User not found
    """
    user = get_current_user()
    
    if not user:
        return jsonify({
            'error': 'Not Found',
            'message': 'User not found'
        }), 404
    
    return jsonify({
        'user': user.to_dict(include_email=True)
    }), 200


@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_me():
    """
    Update current user profile
    
    Request Body:
        {
            "bio": "New bio",
            "location": "New location",
            "profile_picture_url": "https://..."
        }
    
    Returns:
        200: User updated successfully
        404: User not found
    """
    user = get_current_user()
    
    if not user:
        return jsonify({
            'error': 'Not Found',
            'message': 'User not found'
        }), 404
    
    data = request.get_json()
    
    # Update allowed fields
    if 'bio' in data:
        user.bio = sanitize_input(data['bio'], max_length=500)
    
    if 'location' in data:
        user.location = sanitize_input(data['location'], max_length=255)
    
    if 'profile_picture_url' in data:
        user.profile_picture_url = sanitize_input(data['profile_picture_url'], max_length=512)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict(include_email=True)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Server Error',
            'message': 'Failed to update profile'
        }), 500
