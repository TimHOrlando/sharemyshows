"""
ShareMyShows - Main application entry point
"""
import os
from app import create_app, db
from app.models import User, Artist, Venue, Show

# Create Flask application
app = create_app()

# Shell context for flask shell command
@app.shell_context_processor
def make_shell_context():
    """Make database models available in flask shell"""
    return {
        'db': db,
        'User': User,
        'Artist': Artist,
        'Venue': Venue,
        'Show': Show
    }


if __name__ == '__main__':
    # Run the application
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
