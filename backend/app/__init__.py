"""
Flask Application Factory with Flask-RESTX API Documentation
Updated to handle existing file structure
"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_restx import Api

from config.config import config
from app.models import db

# Initialize extensions
jwt = JWTManager()
migrate = Migrate()
socketio = SocketIO()

# Export socketio for use in run.py
__all__ = ['create_app', 'socketio', 'db']

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Configure CORS
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Initialize SocketIO
    socketio.init_app(app, 
                     cors_allowed_origins=app.config['CORS_ORIGINS'],
                     async_mode='threading')
    
    # Initialize Flask-RESTX API
    api = Api(
        app,
        version='1.0',
        title='ShareMyShows API',
        description='Concert documentation and sharing platform API',
        doc='/api/docs',
        prefix='/api',
        authorizations={
            'jwt': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization',
                'description': 'JWT token in format: Bearer <token>'
            }
        },
        security='jwt'
    )
    
    # Import swagger namespaces (only ones that exist)
    from app.routes.auth_swagger import api as auth_ns
    from app.routes.external_apis_swagger import api as external_ns
    
    # Add core namespaces
    api.add_namespace(auth_ns, path='/auth')
    api.add_namespace(external_ns, path='/external')
    
    # Try to import shows_swagger, fall back to regular shows blueprint if not exists
    try:
        from app.routes.shows_swagger import api as shows_ns
        api.add_namespace(shows_ns, path='/shows')
    except ImportError:
        # If shows_swagger doesn't exist, register the blueprint version
        from app.routes import shows
        app.register_blueprint(shows.bp)
    
    # Try to import new swagger files (if they exist)
    try:
        from app.routes.photos_swagger import api as photos_ns
        api.add_namespace(photos_ns, path='/photos')
    except ImportError:
        # Register original blueprint if swagger version doesn't exist
        try:
            from app.routes import photos
            app.register_blueprint(photos.bp)
        except ImportError:
            pass
    
    try:
        from app.routes.audio_swagger import api as audio_ns
        api.add_namespace(audio_ns, path='/audio')
    except ImportError:
        try:
            from app.routes import audio
            app.register_blueprint(audio.bp)
        except ImportError:
            pass
    
    try:
        from app.routes.videos_swagger import api as videos_ns
        api.add_namespace(videos_ns, path='/videos')
    except ImportError:
        try:
            from app.routes import videos
            app.register_blueprint(videos.bp)
        except ImportError:
            pass
    
    try:
        from app.routes.comments_swagger import api as comments_ns
        api.add_namespace(comments_ns, path='/comments')
    except ImportError:
        try:
            from app.routes import comments
            app.register_blueprint(comments.bp)
        except ImportError:
            pass
    
    try:
        from app.routes.friends_swagger import api as friends_ns
        api.add_namespace(friends_ns, path='/friends')
    except ImportError:
        try:
            from app.routes import friends
            app.register_blueprint(friends.bp)
        except ImportError:
            pass
    
    try:
        from app.routes.dashboard_swagger import api as dashboard_ns
        api.add_namespace(dashboard_ns, path='/dashboard')
    except ImportError:
        try:
            from app.routes import dashboard
            app.register_blueprint(dashboard.bp)
        except ImportError:
            pass
    
    try:
        from app.routes.chat_swagger import api as chat_ns
        api.add_namespace(chat_ns, path='/chat')
    except ImportError:
        try:
            from app.routes import chat
            app.register_blueprint(chat.bp)
        except ImportError:
            pass
    
    # Import WebSocket events
    from app import socket_events
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200
    
    @app.route('/')
    def index():
        return {
            'message': 'ShareMyShows API',
            'version': '1.0',
            'documentation': '/api/docs'
        }
    
    return app
