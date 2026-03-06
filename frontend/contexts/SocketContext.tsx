'use client';

import React, { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuth } from './AuthContext';

interface SocketContextType {
  socket: Socket | null;
  onlineFriendIds: Set<number>;
}

const SocketContext = createContext<SocketContextType>({
  socket: null,
  onlineFriendIds: new Set(),
});

export function SocketProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [socket, setSocket] = useState<Socket | null>(null);
  const [onlineFriendIds, setOnlineFriendIds] = useState<Set<number>>(new Set());
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token || !user) {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
        setSocket(null);
      }
      setOnlineFriendIds(new Set());
      return;
    }

    // Already connected
    if (socketRef.current?.connected) return;

    const s = io(
      process.env.NEXT_PUBLIC_API_URL?.replace('/api', '') || 'http://localhost:5000',
      { query: { token }, transports: ['websocket', 'polling'] }
    );

    s.on('friend_online', (data: { user_id: number }) => {
      setOnlineFriendIds(prev => new Set(prev).add(data.user_id));
    });

    s.on('friend_offline', (data: { user_id: number }) => {
      setOnlineFriendIds(prev => {
        const next = new Set(prev);
        next.delete(data.user_id);
        return next;
      });
    });

    s.on('connect', () => {
      import('@/lib/api').then(({ api }) => {
        api.get('/friends/online').then(res => {
          setOnlineFriendIds(new Set(res.data.online_ids || []));
        }).catch(() => {});
      });
    });

    socketRef.current = s;
    setSocket(s);

    return () => {
      s.disconnect();
      socketRef.current = null;
      setSocket(null);
    };
  }, [user?.id]);

  return (
    <SocketContext.Provider value={{ socket, onlineFriendIds }}>
      {children}
    </SocketContext.Provider>
  );
}

export function useSocket() {
  return useContext(SocketContext);
}
