# WebSocket Real-Time Chat Documentation

This document describes the WebSocket integration using Flask-SocketIO for real-time chat functionality.

## Overview

ShareMyShows uses Socket.IO for real-time bidirectional communication between the server and clients. This enables:
- **Real-time chat** during shows
- **User presence tracking** (who's currently at a show)
- **Typing indicators**
- **Live message delivery** without polling

---

## Architecture

### Backend
- **Flask-SocketIO**: WebSocket server integration with Flask
- **Eventlet**: Async WSGI server for handling WebSocket connections
- **Cookie-based JWT Authentication**: Reuses existing JWT tokens for WebSocket auth

### Frontend
- **socket.io-client**: JavaScript client library for connecting to Socket.IO server
- **React hooks**: For managing WebSocket connections and state

---

## Installation

### Backend Dependencies (Already Added)

```bash
pip install Flask-SocketIO==5.3.5
pip install python-socketio==5.10.0
pip install eventlet==0.33.3
```

### Frontend Dependencies

```bash
npm install socket.io-client
# or
yarn add socket.io-client
```

---

## Server Events

### Connection Events

#### `connect`
Fired when a client connects to the server.

**Server Response:**
```json
{
  "message": "Connected to ShareMyShows",
  "username": "john_doe"
}
```

**Authentication:**
- Server validates JWT token from cookies or query string
- Connection is rejected if unauthorized

---

#### `disconnect`
Fired when a client disconnects.

**Server Actions:**
- Removes user from all active show rooms
- Notifies other users in those rooms
- Updates presence tracking

---

### Show Room Events

#### `join_show`
Join a show's chat room.

**Client Emits:**
```javascript
socket.emit('join_show', {
  show_id: 123
});
```

**Server Responses:**

1. **Message History** (`message_history`):
```json
{
  "messages": [
    {
      "id": 1,
      "show_id": 123,
      "user_id": 5,
      "username": "musiclover87",
      "message": "This opening act is amazing!",
      "created_at": "2024-11-16T20:15:30Z"
    }
  ]
}
```

2. **Active Users** (`active_users`):
```json
{
  "active_users": [
    {
      "user_id": 5,
      "username": "musiclover87",
      "sid": "abc123"
    },
    {
      "user_id": 8,
      "username": "concert_junkie",
      "sid": "def456"
    }
  ],
  "count": 2
}
```

3. **User Joined Broadcast** (`user_joined`) - Sent to other users:
```json
{
  "user_id": 10,
  "username": "you",
  "message": "you joined the chat",
  "active_users": [...]
}
```

**Server Actions:**
- Adds user to show chat room
- Creates ShowCheckin record if not exists
- Sends last 50 messages to joining user
- Broadcasts join event to other users

---

#### `leave_show`
Leave a show's chat room.

**Client Emits:**
```javascript
socket.emit('leave_show', {
  show_id: 123
});
```

**Server Response** (`user_left`) - Broadcast to other users:
```json
{
  "user_id": 10,
  "username": "you",
  "message": "you left the chat",
  "active_users": [...]
}
```

**Server Actions:**
- Removes user from show chat room
- Updates ShowCheckin (checked_out_at)
- Broadcasts leave event to remaining users

---

### Message Events

#### `send_message`
Send a chat message to a show room.

**Client Emits:**
```javascript
socket.emit('send_message', {
  show_id: 123,
  message: "This opening act is incredible!"
});
```

**Server Response** (`new_message`) - Broadcast to all users in room:
```json
{
  "id": 456,
  "show_id": 123,
  "user_id": 10,
  "username": "you",
  "message": "This opening act is incredible!",
  "created_at": "2024-11-16T20:25:45Z"
}
```

**Server Actions:**
- Validates user is in the show room
- Saves message to database (ChatMessage table)
- Broadcasts message to all users in room (including sender)

---

#### `typing`
Send typing indicator.

**Client Emits:**
```javascript
// When user starts typing
socket.emit('typing', {
  show_id: 123,
  is_typing: true
});

// When user stops typing
socket.emit('typing', {
  show_id: 123,
  is_typing: false
});
```

**Server Response** (`user_typing`) - Broadcast to other users (not self):
```json
{
  "user_id": 10,
  "username": "you",
  "is_typing": true
}
```

**Best Practice:** Use debouncing to avoid sending too many typing events.

---

#### `get_active_users`
Request current list of active users in a show.

**Client Emits:**
```javascript
socket.emit('get_active_users', {
  show_id: 123
});
```

**Server Response** (`active_users`):
```json
{
  "show_id": 123,
  "active_users": [
    {
      "user_id": 5,
      "username": "musiclover87",
      "sid": "abc123"
    }
  ],
  "count": 1
}
```

---

### Error Events

#### `error`
Sent when an error occurs.

**Server Response:**
```json
{
  "message": "Error description",
  "details": "Additional error details"
}
```

**Common Errors:**
- "Unauthorized" - Invalid or missing JWT token
- "Show not found" - Invalid show_id
- "Not in show chat room" - Trying to send message without joining
- "Missing show_id or message" - Invalid parameters

---

## Frontend Integration

### 1. Basic Setup (React)

```javascript
import { io } from 'socket.io-client';
import { useEffect, useState, useRef } from 'react';

const SOCKET_URL = 'http://localhost:5000';

function ShowChat({ showId }) {
  const [messages, setMessages] = useState([]);
  const [activeUsers, setActiveUsers] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [typingUsers, setTypingUsers] = useState(new Set());
  const socketRef = useRef(null);

  useEffect(() => {
    // Initialize socket connection
    // Note: Cookies are automatically sent with the connection
    socketRef.current = io(SOCKET_URL, {
      withCredentials: true,
      transports: ['websocket', 'polling']
    });

    const socket = socketRef.current;

    // Connection events
    socket.on('connected', (data) => {
      console.log('Connected:', data);
      // Join the show room
      socket.emit('join_show', { show_id: showId });
    });

    // Message history
    socket.on('message_history', (data) => {
      setMessages(data.messages);
    });

    // New message
    socket.on('new_message', (message) => {
      setMessages(prev => [...prev, message]);
    });

    // Active users
    socket.on('active_users', (data) => {
      setActiveUsers(data.active_users);
    });

    // User joined
    socket.on('user_joined', (data) => {
      setActiveUsers(data.active_users);
      // Optionally show notification
      console.log(`${data.username} joined`);
    });

    // User left
    socket.on('user_left', (data) => {
      setActiveUsers(data.active_users);
      console.log(`${data.username} left`);
    });

    // User typing
    socket.on('user_typing', (data) => {
      if (data.is_typing) {
        setTypingUsers(prev => new Set([...prev, data.username]));
      } else {
        setTypingUsers(prev => {
          const next = new Set(prev);
          next.delete(data.username);
          return next;
        });
      }
    });

    // Error handling
    socket.on('error', (error) => {
      console.error('Socket error:', error);
    });

    // Cleanup on unmount
    return () => {
      if (socket.connected) {
        socket.emit('leave_show', { show_id: showId });
        socket.disconnect();
      }
    };
  }, [showId]);

  const sendMessage = () => {
    if (newMessage.trim() && socketRef.current) {
      socketRef.current.emit('send_message', {
        show_id: showId,
        message: newMessage
      });
      setNewMessage('');
    }
  };

  const handleTyping = (isTyping) => {
    if (socketRef.current) {
      socketRef.current.emit('typing', {
        show_id: showId,
        is_typing: isTyping
      });
    }
  };

  // Render UI...
}
```

---

### 2. Custom React Hook

Create a reusable hook for chat functionality:

```javascript
// hooks/useShowChat.js
import { useEffect, useState, useCallback, useRef } from 'react';
import { io } from 'socket.io-client';

const SOCKET_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export function useShowChat(showId) {
  const [messages, setMessages] = useState([]);
  const [activeUsers, setActiveUsers] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [typingUsers, setTypingUsers] = useState(new Set());
  const socketRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  useEffect(() => {
    if (!showId) return;

    // Initialize socket
    socketRef.current = io(SOCKET_URL, {
      withCredentials: true,
      transports: ['websocket', 'polling']
    });

    const socket = socketRef.current;

    // Connection handlers
    socket.on('connect', () => {
      setIsConnected(true);
      socket.emit('join_show', { show_id: showId });
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
    });

    socket.on('connected', (data) => {
      console.log('WebSocket connected:', data);
    });

    // Message handlers
    socket.on('message_history', (data) => {
      setMessages(data.messages);
    });

    socket.on('new_message', (message) => {
      setMessages(prev => [...prev, message]);
    });

    // User presence handlers
    socket.on('active_users', (data) => {
      setActiveUsers(data.active_users);
    });

    socket.on('user_joined', (data) => {
      setActiveUsers(data.active_users);
    });

    socket.on('user_left', (data) => {
      setActiveUsers(data.active_users);
    });

    // Typing indicator
    socket.on('user_typing', (data) => {
      if (data.is_typing) {
        setTypingUsers(prev => new Set([...prev, data.username]));
      } else {
        setTypingUsers(prev => {
          const next = new Set(prev);
          next.delete(data.username);
          return next;
        });
      }
    });

    // Error handling
    socket.on('error', (error) => {
      console.error('Socket error:', error);
    });

    // Cleanup
    return () => {
      if (socket.connected) {
        socket.emit('leave_show', { show_id: showId });
        socket.disconnect();
      }
    };
  }, [showId]);

  const sendMessage = useCallback((message) => {
    if (socketRef.current && message.trim()) {
      socketRef.current.emit('send_message', {
        show_id: showId,
        message: message.trim()
      });
    }
  }, [showId]);

  const sendTypingIndicator = useCallback((isTyping) => {
    if (socketRef.current) {
      socketRef.current.emit('typing', {
        show_id: showId,
        is_typing: isTyping
      });
    }
  }, [showId]);

  const handleInputChange = useCallback(() => {
    // Send typing indicator
    sendTypingIndicator(true);

    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Set timeout to stop typing indicator
    typingTimeoutRef.current = setTimeout(() => {
      sendTypingIndicator(false);
    }, 2000);
  }, [sendTypingIndicator]);

  return {
    messages,
    activeUsers,
    isConnected,
    typingUsers,
    sendMessage,
    handleInputChange
  };
}
```

---

### 3. Usage Example

```javascript
import { useShowChat } from './hooks/useShowChat';

function ShowChatComponent({ showId }) {
  const {
    messages,
    activeUsers,
    isConnected,
    typingUsers,
    sendMessage,
    handleInputChange
  } = useShowChat(showId);

  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
    setInput('');
  };

  return (
    <div className="chat-container">
      {/* Connection Status */}
      <div className="status">
        {isConnected ? (
          <span className="text-green-500">● Connected</span>
        ) : (
          <span className="text-red-500">● Disconnected</span>
        )}
      </div>

      {/* Active Users */}
      <div className="active-users">
        <h3>Active Users ({activeUsers.length})</h3>
        {activeUsers.map(user => (
          <div key={user.user_id}>{user.username}</div>
        ))}
      </div>

      {/* Messages */}
      <div className="messages">
        {messages.map(msg => (
          <div key={msg.id} className="message">
            <span className="username">{msg.username}:</span>
            <span className="text">{msg.message}</span>
            <span className="time">{new Date(msg.created_at).toLocaleTimeString()}</span>
          </div>
        ))}
      </div>

      {/* Typing Indicator */}
      {typingUsers.size > 0 && (
        <div className="typing-indicator">
          {Array.from(typingUsers).join(', ')} {typingUsers.size > 1 ? 'are' : 'is'} typing...
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            handleInputChange();
          }}
          placeholder="Type a message..."
          disabled={!isConnected}
        />
        <button type="submit" disabled={!isConnected || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
```

---

## Authentication

### Cookie-Based (Recommended)

The WebSocket connection automatically sends cookies, so if the user is authenticated via JWT cookies, they'll be authenticated for WebSocket too.

```javascript
const socket = io('http://localhost:5000', {
  withCredentials: true  // Important: Send cookies
});
```

### Token-Based (Alternative)

If cookies aren't available, pass the JWT token in the query string:

```javascript
const token = localStorage.getItem('access_token');
const socket = io('http://localhost:5000', {
  query: { token }
});
```

---

## Best Practices

### 1. Connection Management
- **Single connection per user**: Reuse the socket connection across components
- **Cleanup on unmount**: Always disconnect and leave rooms when components unmount
- **Reconnection**: Socket.IO handles reconnection automatically

### 2. Message Handling
- **Debounce typing indicators**: Wait 300-500ms before sending typing events
- **Auto-scroll**: Scroll to bottom when new messages arrive
- **Optimistic updates**: Show sent messages immediately, update with server response

### 3. Performance
- **Message limits**: Server sends last 50 messages on join
- **Pagination**: Implement "load more" for message history
- **Throttling**: Limit message send rate to prevent spam

### 4. Error Handling
- **Connection errors**: Show user-friendly error messages
- **Retry logic**: Attempt to rejoin room on disconnect
- **Fallback**: Provide polling-based chat if WebSocket fails

---

## Testing

### 1. Using Browser Console

```javascript
// Connect
const socket = io('http://localhost:5000', { withCredentials: true });

// Join show
socket.emit('join_show', { show_id: 1 });

// Send message
socket.emit('send_message', { show_id: 1, message: 'Test message' });

// Leave show
socket.emit('leave_show', { show_id: 1 });

// Disconnect
socket.disconnect();
```

### 2. Using Python Client

```python
import socketio

# Create client
sio = socketio.Client()

# Event handlers
@sio.on('connected')
def on_connected(data):
    print('Connected:', data)

@sio.on('new_message')
def on_message(data):
    print('New message:', data)

# Connect (with cookie)
sio.connect('http://localhost:5000', headers={'Cookie': 'access_token_cookie=YOUR_JWT'})

# Join show
sio.emit('join_show', {'show_id': 1})

# Send message
sio.emit('send_message', {'show_id': 1, 'message': 'Hello!'})

# Wait
sio.wait()
```

---

## Troubleshooting

### Connection Issues

**Problem:** Socket won't connect
**Solutions:**
- Check CORS settings in backend
- Verify JWT cookie is being sent (`withCredentials: true`)
- Check firewall/proxy settings
- Try polling transport: `transports: ['polling']`

**Problem:** Connection drops frequently
**Solutions:**
- Check network stability
- Increase `pingTimeout` and `pingInterval` in Socket.IO config
- Use polling as fallback

### Message Issues

**Problem:** Messages not appearing
**Solutions:**
- Verify user joined the room (`join_show` event)
- Check server logs for errors
- Ensure JWT token is valid

**Problem:** Duplicate messages
**Solutions:**
- Check for multiple socket connections
- Ensure `useEffect` cleanup is working properly

---

## Production Deployment

### Backend

1. **Use a production WSGI server:**
   ```bash
   pip install gunicorn gevent-websocket
   gunicorn --worker-class eventlet -w 1 run:app
   ```

2. **Configure NGINX:**
   ```nginx
   location /socket.io {
       proxy_pass http://localhost:5000;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_set_header Host $host;
   }
   ```

3. **Enable SSL:**
   - Use wss:// protocol for secure WebSocket
   - Configure SSL certificates

### Frontend

1. **Environment variables:**
   ```env
   REACT_APP_API_URL=https://api.yourdomain.com
   REACT_APP_WS_URL=wss://api.yourdomain.com
   ```

2. **Connection config:**
   ```javascript
   const socket = io(process.env.REACT_APP_WS_URL, {
     secure: true,
     withCredentials: true
   });
   ```

---

## Next Steps

1. Install Socket.IO client in your frontend
2. Create the useShowChat hook
3. Build chat UI components
4. Test with multiple browser windows
5. Add message persistence and history pagination
6. Implement push notifications for messages

For external API integration (Google Places, Setlist.fm), see `EXTERNAL_API_DOCUMENTATION.md`.
