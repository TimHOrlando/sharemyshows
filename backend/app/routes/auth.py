from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, unset_jwt_cookies
)
from app.models import db, User
from datetime import datetime, timedelta
import secrets
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def validate_password(password):
    """Validate password strength"""
    errors = []
    
    if len(password) < 15:
        errors.append('Password must be at least 15 characters long')
    
    if len(password) >= 15 and len(password) <= 35:
        if not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter')
        if not re.search(r'\d', password):
            errors.append('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('Password must contain at least one special character')
    
    return errors

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ('email', 'username', 'password', 'confirm_password')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if data['password'] != data['confirm_password']:
        return jsonify({'error': 'Passwords do not match'}), 400
    
    password_errors = validate_password(data['password'])
    if password_errors:
        return jsonify({'error': 'Password validation failed', 'details': password_errors}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 400
    
    user = User(
        email=data['email'],
        username=data['username']
    )
    user.set_password(data['password'])
    user.verification_token = secrets.token_urlsafe(32)
    
    if data.get('enable_mfa'):
        user.mfa_enabled = True
        user.mfa_method = data.get('mfa_method', 'email')
        
        if user.mfa_method == 'totp':
            user.generate_mfa_secret()
        elif user.mfa_method == 'sms':
            user.phone_number = data.get('phone_number')
    
    try:
        db.session.add(user)
        db.session.commit()
        
        response_data = {
            'message': 'Registration successful',
            'user': user.to_dict()
        }
        
        if user.mfa_enabled and user.mfa_method == 'totp':
            response_data['totp_uri'] = user.get_totp_uri()
        
        return jsonify(response_data), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ('username', 'password')):
        return jsonify({'error': 'Missing username or password'}), 400
    
    user = User.query.filter(
        (User.username == data['username']) | (User.email == data['username'])
    ).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if user.mfa_enabled:
        return jsonify({
            'mfa_required': True,
            'mfa_method': user.mfa_method,
            'user_id': user.id
        }), 200
    
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    response = make_response(jsonify({
        'message': 'Login successful',
        'user': user.to_dict()
    }))
    
    response.set_cookie('access_token_cookie', access_token, httponly=True, samesite='Lax')
    response.set_cookie('refresh_token_cookie', refresh_token, httponly=True, samesite='Lax')
    
    return response, 200

@auth_bp.route('/verify-mfa', methods=['POST'])
def verify_mfa():
    """Verify MFA code"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ('user_id', 'code')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    is_valid = False
    
    if user.mfa_method == 'totp':
        is_valid = user.verify_totp(data['code'])
    elif user.mfa_method == 'email':
        is_valid = len(data['code']) == 6 and data['code'].isdigit()
    
    if not is_valid:
        return jsonify({'error': 'Invalid MFA code'}), 401
    
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    response = make_response(jsonify({
        'message': 'MFA verification successful',
        'user': user.to_dict()
    }))
    
    response.set_cookie('access_token_cookie', access_token, httponly=True, samesite='Lax')
    response.set_cookie('refresh_token_cookie', refresh_token, httponly=True, samesite='Lax')
    
    return response, 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout"""
    response = make_response(jsonify({'message': 'Logout successful'}))
    unset_jwt_cookies(response)
    return response, 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify user email with token"""
    data = request.get_json()
    
    if not data or 'token' not in data:
        return jsonify({'error': 'Missing verification token'}), 400
    
    user = User.query.filter_by(verification_token=data['token']).first()
    
    if not user:
        return jsonify({'error': 'Invalid verification token'}), 400
    
    user.email_verified = True
    user.verification_token = None
    
    try:
        db.session.commit()
        return jsonify({'message': 'Email verified successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Verification failed', 'details': str(e)}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset"""
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({'error': 'Missing email'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        return jsonify({'message': 'If the email exists, a reset link has been sent'}), 200
    
    user.reset_token = secrets.token_urlsafe(32)
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'If the email exists, a reset link has been sent',
            'reset_token': user.reset_token
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to process request'}), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ('token', 'password', 'confirm_password')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if data['password'] != data['confirm_password']:
        return jsonify({'error': 'Passwords do not match'}), 400
    
    password_errors = validate_password(data['password'])
    if password_errors:
        return jsonify({'error': 'Password validation failed', 'details': password_errors}), 400
    
    user = User.query.filter_by(reset_token=data['token']).first()
    
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        return jsonify({'error': 'Invalid or expired reset token'}), 400
    
    user.set_password(data['password'])
    user.reset_token = None
    user.reset_token_expires = None
    
    try:
        db.session.commit()
        return jsonify({'message': 'Password reset successful'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Password reset failed', 'details': str(e)}), 500

@auth_bp.route('/update-email', methods=['PUT'])
@jwt_required()
def update_email():
    """Update user email address"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400
    
    new_email = data['email'].lower().strip()
    
    # Validate email format
    if not new_email or '@' not in new_email:
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Check if email is already in use by another user
    existing_user = User.query.filter(User.email == new_email, User.id != user_id).first()
    if existing_user:
        return jsonify({'error': 'Email is already in use'}), 400
    
    # Update email
    user.email = new_email
    
    try:
        db.session.commit()
        return jsonify({'message': 'Email updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update email', 'details': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    user_id = int(get_jwt_identity())
    access_token = create_access_token(identity=user_id)
    
    response = make_response(jsonify({'message': 'Token refreshed'}))
    response.set_cookie('access_token_cookie', access_token, httponly=True, samesite='Lax')
    
    return response, 200

