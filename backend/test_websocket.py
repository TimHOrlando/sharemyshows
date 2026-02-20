import socketio
import time

# Create a Socket.IO client
sio = socketio.Client()

# Event handlers
@sio.on('connect')
def on_connect():
    print('✅ Connected to WebSocket server')
    # Join show room immediately after connect
    print('Joining show room...')
    sio.emit('join_show', {'show_id': 1})

@sio.on('connected')
def on_connected(data):
    print(f'Server says: {data}')

@sio.on('message_history')
def on_message_history(data):
    print(f'Message history: {data}')

@sio.on('active_users')
def on_active_users(data):
    print(f'Active users: {data}')

@sio.on('new_message')
def on_new_message(data):
    print(f'New message: {data}')

@sio.on('user_joined')
def on_user_joined(data):
    print(f'User joined: {data}')

@sio.on('error')
def on_error(data):
    print(f'❌ Error: {data}')

# Read JWT token from cookies.txt
with open('cookies.txt', 'r') as f:
    cookie_content = f.read()
    # Extract the access_token_cookie value
    for line in cookie_content.split('\n'):
        if 'access_token_cookie' in line:
            token = line.split('\t')[-1].strip()
            break

# Connect with the JWT cookie
print('Connecting to WebSocket server...')
sio.connect('http://localhost:5000', 
            headers={'Cookie': f'access_token_cookie={token}'})

# Wait for connection to fully establish
time.sleep(1)

# Send a test message
print('Sending test message...')
sio.emit('send_message', {
    'show_id': 1,
    'message': 'Test message from Python!'
})

# Wait for response
time.sleep(2)

# Send another message
print('Sending second message...')
sio.emit('send_message', {
    'show_id': 1,
    'message': 'This is working great! 🎸'
})

# Keep connection alive for a bit
time.sleep(2)

# Disconnect
