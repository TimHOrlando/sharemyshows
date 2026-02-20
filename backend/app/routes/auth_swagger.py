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

from app.models import db, User

api = Namespace('auth', description='Authentication operations with email MFA')

# Models (same as before)
user_model = api.model('User', {
    'id': fields.Integer(description='User ID'),
    'username': fields.String(description='Username'),
    'email': fields.String(description='Email'),
    'mfa_enabled': fields.Boolean(description='MFA enabled status'),
    'created_at': fields.DateTime(description='Account creation time')
})

register_model = api.model('Register', {
    'username': fields.String(required=True, description='Username', min_length=3),
    'email': fields.String(required=True, description='Email address'),
    'password': fields.String(required=True, description='Password', min_length=8),
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
    'password': fields.String(required=True, description='New password', min_length=8)
})

change_password_model = api.model('ChangePassword', {
    'current_password': fields.String(required=True, description='Current password'),
    'new_password': fields.String(required=True, description='New password', min_length=8)
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


def generate_mfa_code():
    """Generate a 6-digit MFA code"""
    return ''.join(random.choices(string.digits, k=6))


def generate_reset_token():
    """Generate a secure password reset token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=64))


def send_mfa_email(email, code, username, action='login'):
    """Send MFA verification email with increased timeout to avoid DNS issues"""
    from flask_mail import Mail, Message
    
    # Increase socket timeout to avoid DNS lookup timeout with eventlet
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(30)  # 30 seconds instead of default
    
    try:
        base_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        verify_link = f"{base_url}/verify-mfa?email={email}&code={code}"
        
        if action == 'registration':
            subject = f"Welcome {username}! Verify your ShareMyShows account"
            body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .code-box {{ background: white; border: 2px dashed #667eea; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }}
        .code {{ font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #667eea; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎸 Welcome to ShareMyShows!</h1>
        </div>
        <div class="content">
            <h2>Hi {username},</h2>
            <p>Thanks for joining ShareMyShows!</p>
            <div class="code-box">
                <p style="margin: 0; font-size: 14px; color: #666;">Your Verification Code</p>
                <div class="code">{code}</div>
            </div>
            <center>
                <a href="{verify_link}" class="button" target="_self">Verify My Account</a>
            </center>
            <p style="color: #666; font-size: 14px;">This code expires in 10 minutes.</p>
        </div>
    </div>
</body>
</html>
"""
        elif action == 'enable_mfa':
            subject = "Enable Multi-Factor Authentication - ShareMyShows"
            body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .code-box {{ background: white; border: 2px dashed #667eea; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }}
        .code {{ font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #667eea; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Enable MFA</h1>
        </div>
        <div class="content">
            <h2>Hi {username},</h2>
            <div class="code-box">
                <p style="margin: 0; font-size: 14px; color: #666;">Your Verification Code</p>
                <div class="code">{code}</div>
            </div>
            <center>
                <a href="{verify_link}" class="button" target="_self">Complete MFA Setup</a>
            </center>
            <p style="color: #666; font-size: 14px;">This code expires in 10 minutes.</p>
        </div>
    </div>
</body>
</html>
"""
        else:  # login
            subject = "Your ShareMyShows Login Code"
            body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .code-box {{ background: white; border: 2px dashed #667eea; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }}
        .code {{ font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #667eea; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎸 Login to ShareMyShows</h1>
        </div>
        <div class="content">
            <h2>Hi {username},</h2>
            <div class="code-box">
                <p style="margin: 0; font-size: 14px; color: #666;">Your Login Code</p>
                <div class="code">{code}</div>
            </div>
            <center>
                <a href="{verify_link}" class="button" target="_self">Complete Login</a>
            </center>
            <p style="color: #666; font-size: 14px;">This code expires in 10 minutes.</p>
        </div>
    </div>
</body>
</html>
"""
        
        mail = Mail(current_app)
        msg = Message(
            subject=subject,
            recipients=[email],
            html=body_html
        )
        
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
        # Restore original timeout
        socket.setdefaulttimeout(old_timeout)


def send_password_reset_email(email, token, username):
    """Send password reset email"""
    from flask_mail import Mail, Message

    # Increase socket timeout to avoid DNS lookup timeout with eventlet
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(30)

    try:
        base_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        reset_link = f"{base_url}/reset-password?token={token}"

        subject = "Reset Your ShareMyShows Password"
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Reset Your Password</h1>
        </div>
        <div class="content">
            <h2>Hi {username},</h2>
            <p>We received a request to reset your ShareMyShows password. Click the button below to create a new password:</p>
            <center>
                <a href="{reset_link}" class="button" target="_self">Reset Password</a>
            </center>
            <p style="color: #666; font-size: 14px;">This link expires in 1 hour.</p>
            <p style="color: #666; font-size: 14px;">If you didn't request this, you can safely ignore this email.</p>
        </div>
    </div>
</body>
</html>
"""

        mail = Mail(current_app)
        msg = Message(
            subject=subject,
            recipients=[email],
            html=body_html
        )

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
        # Restore original timeout
        socket.setdefaulttimeout(old_timeout)


def send_password_change_email(email, username):
    """Send password change confirmation email"""
    from flask_mail import Mail, Message

    # Increase socket timeout to avoid DNS lookup timeout with eventlet
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(30)

    try:
        base_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        login_link = f"{base_url}/login"

        subject = "Your ShareMyShows Password Has Been Changed"
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Password Changed Successfully</h1>
        </div>
        <div class="content">
            <h2>Hi {username},</h2>
            <p>Your ShareMyShows password has been successfully changed.</p>
            <p>You can now log in with your new password by clicking the button below:</p>
            <center>
                <a href="{login_link}" class="button" target="_self">Log In to ShareMyShows</a>
            </center>
            <p style="color: #666; font-size: 14px;">If you didn't make this change, please contact support immediately.</p>
        </div>
    </div>
</body>
</html>
"""

        mail = Mail(current_app)
        msg = Message(
            subject=subject,
            recipients=[email],
            html=body_html
        )

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
        # Restore original timeout
        socket.setdefaulttimeout(old_timeout)


def send_temp_password_email(email, username, code):
    """Send temporary password email for password change"""
    from flask_mail import Mail, Message

    # Increase socket timeout to avoid DNS lookup timeout with eventlet
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(30)

    try:
        subject = "Your Temporary Password - ShareMyShows"
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .code-box {{ background: white; border: 2px dashed #667eea; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }}
        .code {{ font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #667eea; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔑 Temporary Password</h1>
        </div>
        <div class="content">
            <h2>Hi {username},</h2>
            <p>You requested a temporary password to change your ShareMyShows password.</p>
            <p>Use this code as your current password when changing your password:</p>
            <div class="code-box">
                <p style="margin: 0; font-size: 14px; color: #666;">Your Temporary Password</p>
                <div class="code">{code}</div>
            </div>
            <p style="color: #666; font-size: 14px;">This code expires in 10 minutes.</p>
            <p style="color: #666; font-size: 14px;">If you didn't request this, please ignore this email.</p>
        </div>
    </div>
</body>
</html>
"""

        mail = Mail(current_app)
        msg = Message(
            subject=subject,
            recipients=[email],
            html=body_html
        )

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
        
        if not password or len(password) < 8:
            return {'error': 'Password must be at least 8 characters'}, 400
        
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
            
            send_mfa_email(email, mfa_code, username, action='registration')
            
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

            send_mfa_email(user.email, mfa_code, user.username, action='login')
            
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
        send_mfa_email(user.email, mfa_code, user.username, action=action)

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
        send_password_reset_email(user.email, reset_token, user.username)

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

        if len(password) < 8:
            return {'error': 'Password must be at least 8 characters'}, 400

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

        if len(new_password) < 8:
            return {'error': 'New password must be at least 8 characters'}, 400

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
        send_password_change_email(user.email, user.username)

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
            success = send_temp_password_email(user.email, user.username, temp_code)
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

            send_mfa_email(user.email, mfa_code, user.username, action='enable_mfa')

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
