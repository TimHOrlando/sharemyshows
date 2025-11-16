#!/usr/bin/env python3
"""
ShareMyShows Backend - Main Entry Point
"""
# Load environment variables FIRST before any other imports
from dotenv import load_dotenv
import os
load_dotenv()

# Now import the app
from app import create_app
from app.models import db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
