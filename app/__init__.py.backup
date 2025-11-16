from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from flask_restx import Api
from config.config import config
from app.models import db
from app.routes.auth_swagger import api as auth_ns


import os

def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # DEBUG: Print JWT config
    print(f"DEBUG: JWT_SECRET_KEY = {app.config.get('JWT_SECRET_KEY')}")
    print(f"DEBUG: JWT_TOKEN_LOCATION = {app.config.get('JWT_TOKEN_LOCATION')}")
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    # Initialize SocketIO
    from app.socket_events import init_socketio
    socketio = init_socketio(app)
    
    # Store socketio in app config for access in run.py
    app.socketio = socketio
    
    # Initialize Flask-RESTX for Swagger documentation
    authorizations = {
        'jwt': {
            'type': 'apiKey',
            'in': 'cookie',
            'name': 'access_token_cookie',
            'description': 'JWT token in HTTP-only cookie. Login via /api/auth/login first.'
        }
    }
    
    api_restx = Api(
        app,
        version='1.0',
        title='ShareMyShows API',
        description='Concert documentation platform with external API integrations',
        doc='/api/docs',
        authorizations=authorizations,
        security='jwt'
    )
    
    # Import and add Flask-RESTX namespace for external APIs
    from app.routes.external_apis_swagger import api as external_ns
    api_restx.add_namespace(external_ns, path='/api/external')
    
    # Register regular Flask blueprints (non-Swagger routes)
    from app.routes.auth_swagger import api as auth_ns
    from app.routes.shows import shows_bp
    from app.routes.photos import photos_bp
    from app.routes.audio import audio_bp
    from app.routes.videos import videos_bp
    from app.routes.comments import comments_bp
    from app.routes.friends import friends_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.chat import chat_bp
    
    api_restx.add_namespace(auth_ns, path='/api/auth')
    app.register_blueprint(shows_bp)
    app.register_blueprint(photos_bp)
    app.register_blueprint(audio_bp)
    app.register_blueprint(videos_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(friends_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chat_bp)
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'message': 'ShareMyShows API is running'}), 200
    
    @app.route('/')
    def index():
        return jsonify({
            'name': 'ShareMyShows API',
            'version': '1.0.0',
            'status': 'running',
            'swagger_ui': 'http://localhost:5000/api/docs'
        }), 200
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print(f"DEBUG: Invalid token error: {error}")
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        print(f"DEBUG: Unauthorized error: {error}")
        return jsonify({'error': 'Missing authorization token'}), 401
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    return app
