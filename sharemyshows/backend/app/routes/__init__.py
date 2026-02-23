"""
API routes package
"""
from app.routes.auth import auth_bp
from app.routes.shows import shows_bp
from app.routes.artists import artists_bp
from app.routes.venues import venues_bp

__all__ = [
    'auth_bp',
    'shows_bp',
    'artists_bp',
    'venues_bp'
]
