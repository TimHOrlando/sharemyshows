"""
Enhanced Auth Routes with Email-Based MFA
Fixed DNS timeout issue with eventlet
"""
from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random
import string
import socket
import re

from app.models import db, User, ShowCheckin

api = Namespace('auth', description='Authentication operations with email MFA')

# Models (same as before)
user_model = api.model('User', {
    'id': fields.Integer(description='User ID'),
    'username': fields.String(description='Username'),
    'email': fields.String(description='Email'),
    'mfa_enabled': fields.Boolean(description='MFA enabled status'),
    'appear_offline': fields.Boolean(description='Appear offline to friends'),
    'created_at': fields.DateTime(description='Account creation time')
})

register_model = api.model('Register', {
    'username': fields.String(required=True, description='Username', min_length=3),
    'email': fields.String(required=True, description='Email address'),
    'password': fields.String(required=True, description='Password (12+ chars, upper, lower, special, no underscore)', min_length=12),
    'enable_mfa': fields.Boolean(required=False, default=False, description='Enable MFA during registration')
})

login_model = api.model('Login', {
    'login': fields.String(required=True, description='Username or Email address'),
    'password': fields.String(required=True, description='Password')
})

verify_mfa_model = api.model('VerifyMFA', {
    'email': fields.String(required=True, description='Email address'),
    'code': fields.String(required=True, description='6-digit verification code')
})

enable_mfa_model = api.model('EnableMFA', {
    'enable': fields.Boolean(required=True, description='Enable or disable MFA')
})

request_password_reset_model = api.model('RequestPasswordReset', {
    'email': fields.String(required=True, description='Email address')
})

reset_password_model = api.model('ResetPassword', {
    'token': fields.String(required=True, description='Password reset token'),
    'password': fields.String(required=True, description='New password', min_length=12)
})

change_password_model = api.model('ChangePassword', {
    'current_password': fields.String(required=True, description='Current password'),
    'new_password': fields.String(required=True, description='New password', min_length=12)
})

request_temp_password_model = api.model('RequestTempPassword', {
    'delivery_method': fields.String(required=True, description='Delivery method: email or sms', enum=['email', 'sms']),
    'phone_number': fields.String(required=False, description='Phone number (required if delivery_method is sms)')
})

token_response = api.model('TokenResponse', {
    'access_token': fields.String(description='JWT access token'),
    'refresh_token': fields.String(description='JWT refresh token'),
    'user': fields.Nested(user_model),
    'mfa_required': fields.Boolean(description='Whether MFA verification is required')
})

message_response = api.model('MessageResponse', {
    'message': fields.String(description='Response message')
})

error_response = api.model('ErrorResponse', {
    'error': fields.String(description='Error message')
})


def validate_password(password):
    """Validate password meets all requirements.
    Returns (is_valid, error_message) tuple."""
    if len(password) < 12:
        return False, 'Password must be at least 12 characters'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least 1 uppercase letter'
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least 1 lowercase letter'
    if '_' in password:
        return False, 'Password must not contain underscores'
    if not re.search(r'[^a-zA-Z0-9_]', password):
        return False, 'Password must contain at least 1 special character (not underscore)'
    return True, None


THEME_COLORS = {
    'forest':   {'bg': '#1b211a', 'card': '#232b22', 'card2': '#2d372c', 'text': '#ebd5ab', 'text2': '#8bae66', 'muted': '#628141', 'accent': '#8bae66', 'border': '#2d372c'},
    'sage':     {'bg': '#1e2721', 'card': '#2d3830', 'card2': '#3d4a40', 'text': '#e8efe9', 'text2': '#a3b5a6', 'muted': '#7a8f7d', 'accent': '#9db99a', 'border': '#3d4a40'},
    'dark':     {'bg': '#121212', 'card': '#181818', 'card2': '#282828', 'text': '#ffffff', 'text2': '#b3b3b3', 'muted': '#6a6a6a', 'accent': '#9333ea', 'border': '#282828'},
    'light':    {'bg': '#ffffff', 'card': '#f5f5f5', 'card2': '#e5e5e5', 'text': '#121212', 'text2': '#535353', 'muted': '#9a9a9a', 'accent': '#628141', 'border': '#e5e5e5'},
    'midnight': {'bg': '#0f172a', 'card': '#1e293b', 'card2': '#334155', 'text': '#f8fafc', 'text2': '#94a3b8', 'muted': '#64748b', 'accent': '#6366f1', 'border': '#334155'},
    'concert':  {'bg': '#18181b', 'card': '#27272a', 'card2': '#3f3f46', 'text': '#fafafa', 'text2': '#a1a1aa', 'muted': '#71717a', 'accent': '#dc2626', 'border': '#3f3f46'},
    'purple':   {'bg': '#1a1625', 'card': '#251f33', 'card2': '#352d47', 'text': '#f5f3ff', 'text2': '#c4b5fd', 'muted': '#8b5cf6', 'accent': '#a78bfa', 'border': '#352d47'},
}


def get_email_colors(user_id):
    """Get theme colors for a user's email styling"""
    try:
        user = User.query.get(user_id)
        theme = user.theme_preference if user and user.theme_preference else 'forest'
    except Exception:
        theme = 'forest'
    return THEME_COLORS.get(theme, THEME_COLORS['forest'])


def themed_email_html(colors, header_text, body_content):
    """Generate a themed email HTML template"""
    return f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; background-color: {colors['bg']}; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {colors['accent']}; color: {colors['bg']}; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .content {{ background: {colors['card']}; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid {colors['border']}; border-top: none; }}
        .content h2 {{ color: {colors['text']}; margin-top: 0; }}
        .content p {{ color: {colors['text2']}; }}
        .code-box {{ background: {colors['card2']}; border: 2px dashed {colors['accent']}; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }}
        .code {{ font-size: 32px; font-weight: bold; letter-spacing: 8px; color: {colors['accent']}; }}
        .code-label {{ margin: 0; font-size: 14px; color: {colors['muted']}; }}
        .button {{ display: inline-block; background: {colors['accent']}; color: {colors['bg']}; padding: 15px 40px; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
        .muted {{ color: {colors['muted']}; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{header_text}</h1>
        </div>
        <div class="content">
            {body_content}
        </div>
    </div>
</body>
</html>"""


def generate_mfa_code():
    """Generate a 6-digit MFA code"""
    return ''.join(random.choices(string.digits, k=6))


def generate_reset_token():
    """Generate a secure password reset token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=64))


def send_mfa_email(email, code, username, action='login', user_id=None):
    """Send MFA verification email with increased timeout to avoid DNS issues"""
    from flask_mail import Mail, Message

    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(30)

    try:
        colors = get_email_colors(user_id) if user_id else THEME_COLORS['forest']
        base_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        verify_link = f"{base_url}/verify-mfa?email={email}&code={code}"

        code_block = f"""
            <div class="code-box">
                <p class="code-label">Your Verification Code</p>
                <div class="code">{code}</div>
            </div>
            <center><a href="{verify_link}" class="button" target="_self">{{button_text}}</a></center>
            <p class="muted">This code expires in 10 minutes.</p>"""

        if action == 'registration':
            subject = f"Welcome {username}! Verify your ShareMyShows account"
            body = f"""<h2>Hi {username},</h2>
            <p>Thanks for joining ShareMyShows!</p>
            {code_block.format(button_text='Verify My Account')}"""
            header = "Welcome to ShareMyShows!"
        elif action == 'enable_mfa':
            subject = "Enable Multi-Factor Authentication - ShareMyShows"
            body = f"""<h2>Hi {username},</h2>
            {code_block.format(button_text='Complete MFA Setup')}"""
            header = "Enable MFA"
        else:
            subject = "Your ShareMyShows Login Code"
            body = f"""<h2>Hi {username},</h2>
            {code_block.format(button_text='Complete Login')}"""
            header = "Login to ShareMyShows"

        body_html = themed_email_html(colors, header, body)

        mail = Mail(current_app)
        msg = Message(subject=subject, recipients=[email], html=body_html)

        print(f"Sending MFA email to {email}...")
        mail.send(msg)
        print(f"✅ Email sent successfully to {email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        socket.setdefaulttimeout(old_timeout)


def send_password_reset_email(email, token, username, user_id=None):
    """Send password reset email"""
    from flask_mail import Mail, Message

    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(30)

    try:
        colors = get_email_colors(user_id) if user_id else THEME_COLORS['forest']
        base_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        reset_link = f"{base_url}/reset-password?token={token}"

        body = f"""<h2>Hi {username},</h2>
            <p>We received a request to reset your ShareMyShows password. Click the button below to create a new password:</p>
            <center><a href="{reset_link}" class="button" target="_self">Reset Password</a></center>
            <p class="muted">This link expires in 1 hour.</p>
            <p class="muted">If you didn't request this, you can safely ignore this email.</p>"""

        body_html = themed_email_html(colors, "Reset Your Password", body)

        mail = Mail(current_app)
        msg = Message(subject="Reset Your ShareMyShows Password", recipients=[email], html=body_html)

        print(f"Sending password reset email to {email}...")
        mail.send(msg)
        print(f"✅ Email sent successfully to {email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        socket.setdefaulttimeout(old_timeout)


def send_password_change_email(email, username, user_id=None):
    """Send password change confirmation email"""
    from flask_mail import Mail, Message

    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(30)

    try:
        colors = get_email_colors(user_id) if user_id else THEME_COLORS['forest']
        base_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        login_link = f"{base_url}/login"

        body = f"""<h2>Hi {username},</h2>
            <p>Your ShareMyShows password has been successfully changed.</p>
            <p>You can now log in with your new password by clicking the button below:</p>
            <center><a href="{login_link}" class="button" target="_self">Log In to ShareMyShows</a></center>
            <p class="muted">If you didn't make this change, please contact support immediately.</p>"""

        body_html = themed_email_html(colors, "Password Changed Successfully", body)

        mail = Mail(current_app)
        msg = Message(subject="Your ShareMyShows Password Has Been Changed", recipients=[email], html=body_html)

        print(f"Sending password change confirmation email to {email}...")
        mail.send(msg)
        print(f"✅ Email sent successfully to {email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        socket.setdefaulttimeout(old_timeout)


def send_temp_password_email(email, username, code, user_id=None):
    """Send temporary password email for password change"""
    from flask_mail import Mail, Message

    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(30)

    try:
        colors = get_email_colors(user_id) if user_id else THEME_COLORS['forest']

        body = f"""<h2>Hi {username},</h2>
            <p>You requested a temporary password to change your ShareMyShows password.</p>
            <p>Use this code as your current password when changing your password:</p>
            <div class="code-box">
                <p class="code-label">Your Temporary Password</p>
                <div class="code">{code}</div>
            </div>
            <p class="muted">This code expires in 10 minutes.</p>
            <p class="muted">If you didn't request this, please ignore this email.</p>"""

        body_html = themed_email_html(colors, "Temporary Password", body)

        mail = Mail(current_app)
        msg = Message(subject="Your Temporary Password - ShareMyShows", recipients=[email], html=body_html)

        print(f"Sending temporary password email to {email}...")
        mail.send(msg)
        print(f"✅ Temporary password sent successfully to {email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original timeout
        socket.setdefaulttimeout(old_timeout)


def send_temp_password_sms(phone_number, code):
    """Send temporary password via SMS (Twilio integration required)"""
    # TODO: Implement Twilio SMS sending
    # For now, just return False since Twilio is not configured
    print(f"SMS sending not yet implemented for {phone_number}")
    return False


@api.route('/register')
class Register(Resource):
    @api.doc('register_user')
    @api.expect(register_model)
    @api.response(201, 'User registered successfully', token_response)
    @api.response(400, 'Validation error', error_response)
    def post(self):
        """Register a new user with optional MFA"""
        data = request.get_json()
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        enable_mfa = data.get('enable_mfa', False)
        
        if not username or len(username) < 3:
            return {'error': 'Username must be at least 3 characters'}, 400
        
        if not email or '@' not in email:
            return {'error': 'Valid email is required'}, 400
        
        if not password:
            return {'error': 'Password is required'}, 400
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return {'error': error_msg}, 400
        
        if User.query.filter_by(username=username).first():
            return {'error': 'Username already exists'}, 400
        
        if User.query.filter_by(email=email).first():
            return {'error': 'Email already registered'}, 400
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            mfa_enabled=enable_mfa,
            email_verified=False
        )
        
        db.session.add(user)
        db.session.commit()
        
        if enable_mfa:
            mfa_code = generate_mfa_code()
            user.mfa_code = mfa_code
            user.mfa_code_expires = datetime.utcnow() + timedelta(minutes=10)
            db.session.commit()
            
            send_mfa_email(email, mfa_code, username, action='registration', user_id=user.id)
            
            return {
                'message': 'Registration successful! Check your email for verification code.',
                'mfa_required': True,
                'user': user.to_dict()
            }, 201
        else:
            user.email_verified = True
            db.session.commit()
            
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict(),
                'mfa_required': False
            }, 201


@api.route('/login')
class Login(Resource):
    @api.doc('login_user')
    @api.expect(login_model)
    @api.response(200, 'Login successful', token_response)
    @api.response(401, 'Invalid credentials', error_response)
    def post(self):
        """Login user with username or email and optional MFA"""
        data = request.get_json()

        login_input = data.get('login', '').strip()
        password = data.get('password', '')

        if not login_input or not password:
            return {'error': 'Username/Email and password required'}, 400

        # Try to find user by email first, then by username
        user = User.query.filter_by(email=login_input.lower()).first()
        if not user:
            user = User.query.filter_by(username=login_input).first()

        if not user or not check_password_hash(user.password_hash, password):
            return {'error': 'Invalid username/email or password'}, 401
        
        if user.mfa_enabled:
            mfa_code = generate_mfa_code()
            user.mfa_code = mfa_code
            user.mfa_code_expires = datetime.utcnow() + timedelta(minutes=10)
            db.session.commit()

            send_mfa_email(user.email, mfa_code, user.username, action='login', user_id=user.id)
            
            return {
                'message': 'MFA code sent to your email',
                'mfa_required': True,
                'user': user.to_dict()
            }, 200
        else:
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict(),
                'mfa_required': False
            }, 200


@api.route('/verify-mfa')
class VerifyMFA(Resource):
    @api.doc('verify_mfa_code')
    @api.expect(verify_mfa_model, validate=False)
    @api.response(200, 'Verification successful', token_response)
    @api.response(400, 'Invalid or expired code', error_response)
    def post(self):
        """Verify MFA code and complete login/registration"""
        data = request.get_json()

        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()

        if not email or not code:
            return {'error': 'Email and code required'}, 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return {'error': 'User not found'}, 404

        if not user.mfa_code:
            return {'error': 'No verification code found. Please request a new code.'}, 400

        if user.mfa_code != code:
            return {'error': 'Invalid verification code'}, 400

        if not user.mfa_code_expires or user.mfa_code_expires < datetime.utcnow():
            return {'error': 'Verification code has expired'}, 400

        user.mfa_code = None
        user.mfa_code_expires = None
        user.email_verified = True
        db.session.commit()

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(),
            'message': 'Verification successful!'
        }, 200


@api.route('/resend-mfa')
class ResendMFA(Resource):
    @api.doc('resend_mfa_code')
    @api.expect(request_password_reset_model)
    @api.response(200, 'Code resent', message_response)
    @api.response(404, 'User not found', error_response)
    def post(self):
        """Resend MFA verification code"""
        data = request.get_json()

        email = data.get('email', '').strip().lower()

        if not email:
            return {'error': 'Email is required'}, 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return {'error': 'User not found'}, 404

        # Generate new MFA code
        mfa_code = generate_mfa_code()
        user.mfa_code = mfa_code
        user.mfa_code_expires = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()

        # Determine action type
        action = 'registration' if not user.email_verified else 'login'

        # Send email
        send_mfa_email(user.email, mfa_code, user.username, action=action, user_id=user.id)

        return {'message': 'Verification code has been resent to your email'}, 200


@api.route('/logout')
class Logout(Resource):
    @api.doc('logout_user', security='jwt')
    @api.response(200, 'Logout successful', message_response)
    @jwt_required()
    def post(self):
        """Logout user"""
        return {'message': 'Logged out successfully'}, 200


@api.route('/me')
class CurrentUser(Resource):
    @api.doc('get_current_user', security='jwt')
    @api.marshal_with(user_model)
    @jwt_required()
    def get(self):
        """Get current user info"""
        current_user_id = int(get_jwt_identity())
        user = User.query.get(int(current_user_id))

        if not user:
            return {'error': 'User not found'}, 404

        return user.to_dict()


@api.route('/request-password-reset')
class RequestPasswordReset(Resource):
    @api.doc('request_password_reset')
    @api.expect(request_password_reset_model)
    @api.response(200, 'Reset email sent', message_response)
    @api.response(404, 'User not found', error_response)
    def post(self):
        """Request a password reset email"""
        data = request.get_json()

        email = data.get('email', '').strip().lower()

        if not email:
            return {'error': 'Email is required'}, 400

        user = User.query.filter_by(email=email).first()

        # Always return success to avoid email enumeration
        if not user:
            return {'message': 'If that email exists, a password reset link has been sent'}, 200

        # Generate reset token
        reset_token = generate_reset_token()
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        # Send reset email
        send_password_reset_email(user.email, reset_token, user.username, user_id=user.id)

        return {'message': 'If that email exists, a password reset link has been sent'}, 200


@api.route('/reset-password')
class ResetPassword(Resource):
    @api.doc('reset_password')
    @api.expect(reset_password_model)
    @api.response(200, 'Password reset successful', message_response)
    @api.response(400, 'Invalid or expired token', error_response)
    def post(self):
        """Reset password using reset token"""
        data = request.get_json()

        token = data.get('token', '').strip()
        password = data.get('password', '')

        if not token or not password:
            return {'error': 'Token and password are required'}, 400

        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return {'error': error_msg}, 400

        user = User.query.filter_by(reset_token=token).first()

        if not user:
            return {'error': 'Invalid or expired reset token'}, 400

        if user.reset_token_expires < datetime.utcnow():
            return {'error': 'Reset token has expired'}, 400

        # Reset password
        user.password_hash = generate_password_hash(password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()

        return {'message': 'Password reset successful! You can now log in with your new password.'}, 200


@api.route('/change-password')
class ChangePassword(Resource):
    @api.doc('change_password', security='jwt')
    @api.expect(change_password_model)
    @api.response(200, 'Password changed successfully', message_response)
    @api.response(400, 'Invalid current password', error_response)
    @api.response(401, 'Unauthorized', error_response)
    @jwt_required()
    def post(self):
        """Change password for logged-in user"""
        current_user_id = int(get_jwt_identity())
        user = User.query.get(int(current_user_id))

        if not user:
            return {'error': 'User not found'}, 404

        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')

        if not current_password or not new_password:
            return {'error': 'Current password and new password are required'}, 400

        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            return {'error': error_msg}, 400

        # Verify current password or temporary code
        is_temp_code = False
        if not check_password_hash(user.password_hash, current_password):
            # Check if it's a valid temporary code
            if user.mfa_code and user.mfa_code == current_password:
                # Check if code has expired
                if user.mfa_code_expires and user.mfa_code_expires > datetime.utcnow():
                    is_temp_code = True
                else:
                    return {'error': 'Temporary code has expired'}, 400
            else:
                return {'error': 'Current password is incorrect'}, 400

        # Change password
        user.password_hash = generate_password_hash(new_password)

        # Clear temporary code if it was used
        if is_temp_code:
            user.mfa_code = None
            user.mfa_code_expires = None

        db.session.commit()

        # Send confirmation email
        send_password_change_email(user.email, user.username, user_id=user.id)

        return {'message': 'Password changed successfully! Please log in with your new password.'}, 200


@api.route('/request-temp-password')
class RequestTempPassword(Resource):
    @api.doc('request_temp_password', security='jwt')
    @api.expect(request_temp_password_model)
    @api.response(200, 'Temporary password sent successfully', message_response)
    @api.response(400, 'Invalid request', error_response)
    @api.response(401, 'Unauthorized', error_response)
    @jwt_required()
    def post(self):
        """Request a temporary password for password change"""
        current_user_id = int(get_jwt_identity())
        user = User.query.get(int(current_user_id))

        if not user:
            return {'error': 'User not found'}, 404

        data = request.get_json()
        delivery_method = data.get('delivery_method', '')
        phone_number = data.get('phone_number', '')

        if not delivery_method or delivery_method not in ['email', 'sms']:
            return {'error': 'Delivery method must be email or sms'}, 400

        if delivery_method == 'sms' and not phone_number:
            return {'error': 'Phone number is required for SMS delivery'}, 400

        # Generate temporary code
        temp_code = generate_mfa_code()

        # Store code with 10-minute expiration
        user.mfa_code = temp_code
        user.mfa_code_expires = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()

        # Send code via selected method
        if delivery_method == 'email':
            success = send_temp_password_email(user.email, user.username, temp_code, user_id=user.id)
            if success:
                return {'message': 'Temporary password sent to your email. Please check your inbox.'}, 200
            else:
                return {'error': 'Failed to send email. Please try again.'}, 500
        else:  # sms
            success = send_temp_password_sms(phone_number, temp_code)
            if success:
                return {'message': f'Temporary password sent via SMS to {phone_number}.'}, 200
            else:
                return {'error': 'SMS sending is not yet implemented. Please use email instead.'}, 501


@api.route('/profile/mfa')
class ProfileMFA(Resource):
    @api.doc('toggle_mfa', security='jwt')
    @api.expect(enable_mfa_model)
    @api.response(200, 'MFA status updated', message_response)
    @api.response(401, 'Unauthorized', error_response)
    @jwt_required()
    def post(self):
        """Enable or disable MFA for the current user"""
        current_user_id = int(get_jwt_identity())
        user = User.query.get(int(current_user_id))

        if not user:
            return {'error': 'User not found'}, 404

        data = request.get_json()
        enable = data.get('enable', False)

        if enable and not user.mfa_enabled:
            # Enabling MFA - send verification code
            mfa_code = generate_mfa_code()
            user.mfa_code = mfa_code
            user.mfa_code_expires = datetime.utcnow() + timedelta(minutes=10)
            db.session.commit()

            send_mfa_email(user.email, mfa_code, user.username, action='enable_mfa', user_id=user.id)

            return {
                'message': 'MFA verification code sent to your email. Please verify to enable MFA.',
                'mfa_required': True
            }, 200

        elif not enable and user.mfa_enabled:
            # Disabling MFA
            user.mfa_enabled = False
            user.mfa_code = None
            user.mfa_code_expires = None
            db.session.commit()

            return {'message': 'MFA has been disabled for your account'}, 200

        elif enable and user.mfa_enabled:
            return {'message': 'MFA is already enabled for your account'}, 200

        else:
            return {'message': 'MFA is already disabled for your account'}, 200


@api.route('/profile/verify-mfa')
class ProfileVerifyMFA(Resource):
    @api.doc('verify_mfa_enable', security='jwt')
    @api.expect(verify_mfa_model)
    @api.response(200, 'MFA enabled successfully', message_response)
    @api.response(400, 'Invalid code', error_response)
    @jwt_required()
    def post(self):
        """Verify MFA code when enabling from profile"""
        current_user_id = int(get_jwt_identity())
        user = User.query.get(int(current_user_id))

        if not user:
            return {'error': 'User not found'}, 404

        data = request.get_json()
        code = data.get('code', '').strip()

        if not code:
            return {'error': 'Verification code is required'}, 400

        if user.mfa_code != code:
            return {'error': 'Invalid verification code'}, 400

        if user.mfa_code_expires < datetime.utcnow():
            return {'error': 'Verification code has expired'}, 400

        # Enable MFA
        user.mfa_enabled = True
        user.mfa_code = None
        user.mfa_code_expires = None
        db.session.commit()

        return {'message': 'MFA has been enabled successfully for your account!'}, 200


@api.route('/profile/appear-offline')
class AppearOffline(Resource):
    @api.doc('update_appear_offline', security='jwt')
    @api.response(200, 'Status updated', message_response)
    @jwt_required()
    def put(self):
        """Update user's appear-offline preference"""
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        if not user:
            return {'error': 'User not found'}, 404

        data = request.get_json()
        appear_offline = bool(data.get('appear_offline', False))
        user.appear_offline = appear_offline
        db.session.commit()

        if appear_offline:
            # Clear active location sharing so user disappears from "Friends Here"
            active_checkins = ShowCheckin.query.filter_by(
                user_id=user.id,
                is_active=True
            ).filter(ShowCheckin.latitude.isnot(None)).all()
            for checkin in active_checkins:
                checkin.latitude = None
                checkin.longitude = None
                checkin.last_location_update = None
                checkin.share_with = None
            db.session.commit()

            # Notify friends via WebSocket that location stopped and user went offline
            from app import socketio
            from app.socket_events import online_users, active_users, get_sibling_show_ids, user_sids
            from app.models import get_friend_ids

            friend_ids = get_friend_ids(user.id)

            # Tell the user's own sessions to stop location tracking
            sids_before = set(online_users.get(user.id, set()))
            online_users.pop(user.id, None)
            for sid in sids_before:
                socketio.emit('appear_offline_updated', {'appear_offline': True}, to=sid)

            # Tell friends we went offline and hide from show lists
            for fid in friend_ids:
                if fid in online_users:
                    for sid in online_users[fid]:
                        socketio.emit('friend_offline', {
                            'user_id': user.id,
                            'username': user.username
                        }, to=sid)
                # Send hide event to ALL connected sids (not just online_users)
                for sid in user_sids.get(fid, set()):
                    socketio.emit('friend_hide_from_show', {
                        'user_id': user.id,
                        'username': user.username
                    }, to=sid)

            # Broadcast location_stopped to friends in active show rooms
            for checkin in active_checkins:
                sibling_ids = get_sibling_show_ids(checkin.show_id)
                for sid in sibling_ids:
                    if sid in active_users:
                        for friend_id, info in active_users[sid].items():
                            if friend_id in friend_ids:
                                socketio.emit('location_stopped', {
                                    'user_id': user.id,
                                    'username': user.username
                                }, to=info['sid'])

        else:
            # Going back online — restore presence from connected sockets
            from app import socketio
            from app.socket_events import online_users, user_sids
            from app.models import get_friend_ids

            sids = user_sids.get(user.id, set())
            if sids:
                was_empty = not online_users.get(user.id)
                online_users[user.id] = set(sids)

                # Notify own sockets
                for sid in sids:
                    socketio.emit('appear_offline_updated', {'appear_offline': False}, to=sid)

                # Notify friends we came back online and re-show on show lists
                if was_empty:
                    friend_ids = get_friend_ids(user.id)
                    for fid in friend_ids:
                        if fid in online_users:
                            for sid in online_users[fid]:
                                socketio.emit('friend_online', {
                                    'user_id': user.id,
                                    'username': user.username
                                }, to=sid)
                        # Send show_at_show event to ALL connected sids
                        for sid in user_sids.get(fid, set()):
                            socketio.emit('friend_show_at_show', {
                                'user_id': user.id,
                                'username': user.username
                            }, to=sid)

        return {'message': 'Appear offline status updated', 'appear_offline': user.appear_offline}


@api.route('/profile/theme')
class UserTheme(Resource):
    @api.doc('update_theme', security='jwt')
    @api.response(200, 'Theme updated', message_response)
    @jwt_required()
    def put(self):
        """Update user's theme preference"""
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        if not user:
            return {'error': 'User not found'}, 404

        data = request.get_json()
        theme = data.get('theme', 'forest')
        valid_themes = ['forest', 'sage', 'dark', 'light', 'midnight', 'concert', 'purple', 'custom']
        if theme not in valid_themes:
            theme = 'forest'

        user.theme_preference = theme
        db.session.commit()
        return {'message': 'Theme updated'}
