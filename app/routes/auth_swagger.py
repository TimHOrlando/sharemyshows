"""
Authentication Routes with Swagger Documentation
"""

from flask import request, make_response
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, unset_jwt_cookies
)
from app.models import db, User
from datetime import datetime, timedelta
import secrets
import re

# Create API namespace
api = Namespace('auth', description='Authentication operations')

# API Models for Swagger
register_model = api.model('Register', {
    'email': fields.String(required=True, description='Email address', example='user@example.com'),
    'username': fields.String(required=True, description='Username', example='john_doe'),
    'password': fields.String(required=True, description='Password (15+ characters)', example='SecurePassword123!'),
    'confirm_password': fields.String(required=True, description='Confirm password'),
    'enable_mfa': fields.Boolean(description='Enable multi-factor authentication', default=False),
    'mfa_method': fields.String(description='MFA method: totp, email, or sms', enum=['totp', 'email', 'sms']),
    'phone_number': fields.String(description='Phone number (for SMS MFA)')
})

login_model = api.model('Login', {
    'username': fields.String(required=True, description='Username or email', example='john_doe'),
    'password': fields.String(required=True, description='Password', example='SecurePassword123!')
})

mfa_verify_model = api.model('MFAVerify', {
    'user_id': fields.Integer(required=True, description='User ID'),
    'code': fields.String(required=True, description='MFA verification code', example='123456')
})

user_response_model = api.model('UserResponse', {
    'id': fields.Integer(description='User ID'),
    'username': fields.String(description='Username'),
    'email': fields.String(description='Email'),
    'email_verified': fields.Boolean(description='Email verified status'),
    'mfa_enabled': fields.Boolean(description='MFA enabled status'),
    'mfa_method': fields.String(description='MFA method'),
    'created_at': fields.DateTime(description='Account creation date')
})

email_verify_model = api.model('EmailVerify', {
    'token': fields.String(required=True, description='Email verification token')
})

forgot_password_model = api.model('ForgotPassword', {
    'email': fields.String(required=True, description='Email address', example='user@example.com')
})

reset_password_model = api.model('ResetPassword', {
    'token': fields.String(required=True, description='Password reset token'),
    'password': fields.String(required=True, description='New password'),
    'confirm_password': fields.String(required=True, description='Confirm new password')
})

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


@api.route('/register')
class Register(Resource):
    @api.doc('register_user')
    @api.expect(register_model)
    @api.marshal_with(user_response_model, code=201)
    def post(self):
        """Register a new user"""
        data = api.payload
        
        if not data or not all(k in data for k in ('email', 'username', 'password', 'confirm_password')):
            api.abort(400, 'Missing required fields')
        
        if data['password'] != data['confirm_password']:
            api.abort(400, 'Passwords do not match')
        
        password_errors = validate_password(data['password'])
        if password_errors:
            api.abort(400, f"Password validation failed: {', '.join(password_errors)}")
        
        if User.query.filter_by(email=data['email']).first():
            api.abort(400, 'Email already registered')
        
        if User.query.filter_by(username=data['username']).first():
            api.abort(400, 'Username already taken')
        
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
            
            return response_data, 201
        
        except Exception as e:
            db.session.rollback()
            api.abort(500, f'Registration failed: {str(e)}')


@api.route('/login')
class Login(Resource):
    @api.doc('user_login')
    @api.expect(login_model)
    def post(self):
        """User login - returns JWT tokens in HTTP-only cookies"""
        data = api.payload
        
        if not data or not all(k in data for k in ('username', 'password')):
            api.abort(400, 'Missing username or password')
        
        user = User.query.filter(
            (User.username == data['username']) | (User.email == data['username'])
        ).first()
        
        if not user or not user.check_password(data['password']):
            api.abort(401, 'Invalid credentials')
        
        if user.mfa_enabled:
            return {
                'mfa_required': True,
                'mfa_method': user.mfa_method,
                'user_id': user.id
            }, 200
        
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        response = make_response({
            'message': 'Login successful',
            'user': user.to_dict()
        })
        
        response.set_cookie('access_token_cookie', access_token, httponly=True, samesite='Lax')
        response.set_cookie('refresh_token_cookie', refresh_token, httponly=True, samesite='Lax')
        
        return response


@api.route('/verify-mfa')
class VerifyMFA(Resource):
    @api.doc('verify_mfa')
    @api.expect(mfa_verify_model)
    def post(self):
        """Verify MFA code and complete login"""
        data = api.payload
        
        if not data or not all(k in data for k in ('user_id', 'code')):
            api.abort(400, 'Missing required fields')
        
        user = User.query.get(data['user_id'])
        if not user:
            api.abort(404, 'User not found')
        
        is_valid = False
        
        if user.mfa_method == 'totp':
            is_valid = user.verify_totp(data['code'])
        elif user.mfa_method == 'email':
            is_valid = len(data['code']) == 6 and data['code'].isdigit()
        
        if not is_valid:
            api.abort(401, 'Invalid MFA code')
        
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        response = make_response({
            'message': 'MFA verification successful',
            'user': user.to_dict()
        })
        
        response.set_cookie('access_token_cookie', access_token, httponly=True, samesite='Lax')
        response.set_cookie('refresh_token_cookie', refresh_token, httponly=True, samesite='Lax')
        
        return response


@api.route('/logout')
class Logout(Resource):
    @api.doc('user_logout', security='jwt')
    @jwt_required()
    def post(self):
        """User logout - clears JWT cookies"""
        response = make_response({'message': 'Logout successful'})
        unset_jwt_cookies(response)
        return response


@api.route('/me')
class CurrentUser(Resource):
    @api.doc('get_current_user', security='jwt')
    @api.marshal_with(user_response_model)
    @jwt_required()
    def get(self):
        """Get current authenticated user"""
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            api.abort(404, 'User not found')
        
        return user.to_dict()


@api.route('/verify-email')
class VerifyEmail(Resource):
    @api.doc('verify_email')
    @api.expect(email_verify_model)
    def post(self):
        """Verify user email with token"""
        data = api.payload
        
        if not data or 'token' not in data:
            api.abort(400, 'Missing verification token')
        
        user = User.query.filter_by(verification_token=data['token']).first()
        
        if not user:
            api.abort(400, 'Invalid verification token')
        
        user.email_verified = True
        user.verification_token = None
        
        try:
            db.session.commit()
            return {'message': 'Email verified successfully'}, 200
        except Exception as e:
            db.session.rollback()
            api.abort(500, f'Verification failed: {str(e)}')


@api.route('/forgot-password')
class ForgotPassword(Resource):
    @api.doc('forgot_password')
    @api.expect(forgot_password_model)
    def post(self):
        """Request password reset - sends reset link to email"""
        data = api.payload
        
        if not data or 'email' not in data:
            api.abort(400, 'Missing email')
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            return {'message': 'If the email exists, a reset link has been sent'}, 200
        
        user.reset_token = secrets.token_urlsafe(32)
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        
        try:
            db.session.commit()
            return {
                'message': 'If the email exists, a reset link has been sent',
                'reset_token': user.reset_token
            }, 200
        
        except Exception as e:
            db.session.rollback()
            api.abort(500, 'Failed to process request')


@api.route('/reset-password')
class ResetPassword(Resource):
    @api.doc('reset_password')
    @api.expect(reset_password_model)
    def post(self):
        """Reset password with token"""
        data = api.payload
        
        if not data or not all(k in data for k in ('token', 'password', 'confirm_password')):
            api.abort(400, 'Missing required fields')
        
        if data['password'] != data['confirm_password']:
            api.abort(400, 'Passwords do not match')
        
        password_errors = validate_password(data['password'])
        if password_errors:
            api.abort(400, f"Password validation failed: {', '.join(password_errors)}")
        
        user = User.query.filter_by(reset_token=data['token']).first()
        
        if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
            api.abort(400, 'Invalid or expired reset token')
        
        user.set_password(data['password'])
        user.reset_token = None
        user.reset_token_expires = None
        
        try:
            db.session.commit()
            return {'message': 'Password reset successful'}, 200
        except Exception as e:
            db.session.rollback()
            api.abort(500, f'Password reset failed: {str(e)}')


@api.route('/refresh')
class RefreshToken(Resource):
    @api.doc('refresh_token', security='jwt')
    @jwt_required(refresh=True)
    def post(self):
        """Refresh access token using refresh token"""
        user_id = int(get_jwt_identity())
        access_token = create_access_token(identity=str(user_id))
        
        response = make_response({'message': 'Token refreshed'})
        response.set_cookie('access_token_cookie', access_token, httponly=True, samesite='Lax')
        
        return response
