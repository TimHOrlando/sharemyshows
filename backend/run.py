"""
ShareMyShows Backend Server
Runs Flask app with SocketIO support
"""
import eventlet
eventlet.monkey_patch()

from app import create_app, socketio

# Create the Flask app
app = create_app()

if __name__ == '__main__':
    # Get configuration
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 5000)
    debug = app.config.get('DEBUG', True)
    
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║              ShareMyShows API Server                       ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    
    🚀 Server starting...
    📍 Address: http://{host}:{port}
    📚 Swagger UI: http://{host}:{port}/api/docs
    🔍 Health: http://{host}:{port}/health
    
    Press Ctrl+C to stop the server
    """)
    
    # Run with SocketIO
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        use_reloader=debug,
        log_output=True
    )
