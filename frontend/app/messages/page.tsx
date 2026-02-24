'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { io, Socket } from 'socket.io-client';
import ProtectedRoute from '@/components/ProtectedRoute';
import Navbar from '@/components/Navbar';
import SettingsModal from '@/components/SettingsModal';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';

interface UserBrief {
  id: number;
  username: string;
}

interface DirectMessage {
  id: number;
  conversation_id: number;
  sender_id: number;
  sender: UserBrief;
  body: string;
  read_at: string | null;
  created_at: string;
}

interface Conversation {
  id: number;
  other_user: UserBrief;
  last_message: DirectMessage | null;
  unread_count: number;
  created_at: string;
  updated_at: string;
}

export default function MessagesPage() {
  const { user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Conversation state
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<number | null>(null);
  const [messages, setMessages] = useState<DirectMessage[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [loadingConvs, setLoadingConvs] = useState(true);
  const [loadingMsgs, setLoadingMsgs] = useState(false);

  // Input state
  const [draft, setDraft] = useState('');
  const [typingUser, setTypingUser] = useState<string | null>(null);
  const typingTimeout = useRef<NodeJS.Timeout | null>(null);
  const lastTypingEmit = useRef(0);

  // Online presence
  const [onlineFriendIds, setOnlineFriendIds] = useState<Set<number>>(new Set());

  // Mobile state
  const [showThread, setShowThread] = useState(false);

  // Refs
  const socketRef = useRef<Socket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const activeConvIdRef = useRef<number | null>(null);

  // Keep ref in sync with state so socket handlers see the latest value
  useEffect(() => {
    activeConvIdRef.current = activeConvId;
  }, [activeConvId]);

  const activeConv = conversations.find(c => c.id === activeConvId) || null;

  // ── Fetch conversations ──
  const fetchConversations = useCallback(async () => {
    try {
      const res = await api.get('/dm/conversations');
      setConversations(res.data.conversations || []);
    } catch (err) {
      console.error('Failed to fetch conversations:', err);
    } finally {
      setLoadingConvs(false);
    }
  }, []);

  // ── Fetch messages for a conversation ──
  const fetchMessages = useCallback(async (convId: number, before?: number) => {
    setLoadingMsgs(true);
    try {
      const params: Record<string, string | number> = { limit: 50 };
      if (before) params.before = before;
      const res = await api.get(`/dm/conversations/${convId}/messages`, { params });
      const fetched: DirectMessage[] = res.data.messages || [];
      setHasMore(res.data.has_more);
      if (before) {
        setMessages(prev => [...fetched, ...prev]);
      } else {
        setMessages(fetched);
      }
    } catch (err) {
      console.error('Failed to fetch messages:', err);
    } finally {
      setLoadingMsgs(false);
    }
  }, []);

  // ── Mark conversation as read ──
  const markRead = useCallback(async (convId: number) => {
    try {
      await api.post(`/dm/conversations/${convId}/read`);
      // Update local unread count
      setConversations(prev =>
        prev.map(c => c.id === convId ? { ...c, unread_count: 0 } : c)
      );
      // Also tell the other user via socket
      socketRef.current?.emit('dm_read', { conversation_id: convId });
    } catch {
      // ignore
    }
  }, []);

  // ── Select a conversation ──
  const selectConversation = useCallback((convId: number) => {
    setActiveConvId(convId);
    setShowThread(true);
    setMessages([]);
    setTypingUser(null);
    fetchMessages(convId);
    // Mark read if there are unread messages
    const conv = conversations.find(c => c.id === convId);
    if (conv && conv.unread_count > 0) {
      markRead(convId);
    }
  }, [conversations, fetchMessages, markRead]);

  // ── Deep-link: open conversation with friend_id from query ──
  useEffect(() => {
    const friendId = searchParams.get('friend_id');
    if (!friendId || !user) return;

    (async () => {
      try {
        const res = await api.post(`/dm/conversations/${friendId}`);
        const conv: Conversation = res.data;
        // Ensure it's in the list
        setConversations(prev => {
          const exists = prev.find(c => c.id === conv.id);
          if (exists) return prev;
          return [conv, ...prev];
        });
        selectConversation(conv.id);
      } catch (err) {
        console.error('Failed to open conversation:', err);
      }
    })();
    // Clear the query param without navigation
    router.replace('/messages', { scroll: false });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, user]);

  // ── Load conversations on mount ──
  useEffect(() => {
    if (user) fetchConversations();
  }, [user, fetchConversations]);

  // ── Fetch initial online friends ──
  useEffect(() => {
    if (!user) return;
    api.get('/friends/online').then(res => {
      setOnlineFriendIds(new Set(res.data.online_ids || []));
    }).catch(() => {});
  }, [user]);

  // ── Socket connection ──
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token || !user) return;

    const socket = io(
      process.env.NEXT_PUBLIC_API_URL?.replace('/api', '') || 'http://localhost:5000',
      { query: { token }, transports: ['websocket', 'polling'] }
    );
    socketRef.current = socket;

    socket.on('connect', () => {
      socket.emit('join_dm');
    });

    socket.on('new_dm', (msg: DirectMessage) => {
      // This is a message from the OTHER user (our own messages are added via REST response)
      // Append to messages if viewing this conversation
      setMessages(prev => {
        if (prev.some(m => m.id === msg.id)) return prev;
        if (activeConvIdRef.current === msg.conversation_id) {
          return [...prev, msg];
        }
        return prev;
      });

      // Update conversation list with new last_message and bump unread
      setConversations(prev => {
        const exists = prev.some(c => c.id === msg.conversation_id);
        if (!exists) {
          // New conversation we don't have yet — refetch the list
          fetchConversations();
          return prev;
        }
        const updated = prev.map(c => {
          if (c.id !== msg.conversation_id) return c;
          const isViewing = activeConvIdRef.current === msg.conversation_id;
          return {
            ...c,
            last_message: msg,
            updated_at: msg.created_at,
            unread_count: isViewing ? c.unread_count : c.unread_count + 1,
          };
        });
        updated.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
        return updated;
      });

      // Auto-mark read if we're viewing this conversation
      if (activeConvIdRef.current === msg.conversation_id) {
        socketRef.current?.emit('dm_read', { conversation_id: msg.conversation_id });
      }
    });

    socket.on('dm_user_typing', (data: { conversation_id: number; username: string; is_typing: boolean }) => {
      setTypingUser(data.is_typing ? data.username : null);
      // Clear typing after 3s
      if (data.is_typing) {
        if (typingTimeout.current) clearTimeout(typingTimeout.current);
        typingTimeout.current = setTimeout(() => setTypingUser(null), 3000);
      }
    });

    socket.on('friend_online', (data: { user_id: number }) => {
      setOnlineFriendIds(prev => new Set(prev).add(data.user_id));
    });

    socket.on('friend_offline', (data: { user_id: number }) => {
      setOnlineFriendIds(prev => {
        const next = new Set(prev);
        next.delete(data.user_id);
        return next;
      });
    });

    socket.on('dm_messages_read', (data: { conversation_id: number; read_at: string }) => {
      setMessages(prev =>
        prev.map(m =>
          m.conversation_id === data.conversation_id && !m.read_at
            ? { ...m, read_at: data.read_at }
            : m
        )
      );
    });

    return () => {
      socket.emit('leave_dm');
      socket.disconnect();
      socketRef.current = null;
    };
  }, [user]);

  // ── Auto-scroll to bottom on new messages ──
  useEffect(() => {
    if (messages.length > 0) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // ── Mark read when active conversation gets new messages ──
  useEffect(() => {
    if (!activeConvId) return;
    const conv = conversations.find(c => c.id === activeConvId);
    if (conv && conv.unread_count > 0) {
      markRead(activeConvId);
    }
  }, [activeConvId, conversations, markRead]);

  // ── Send message ──
  const handleSend = async () => {
    const body = draft.trim();
    if (!body || !activeConvId) return;
    setDraft('');

    try {
      // Use REST API as primary send path (reliable)
      const res = await api.post(`/dm/conversations/${activeConvId}/messages`, { body });
      const msg: DirectMessage = res.data;

      // Append to local messages immediately
      setMessages(prev => {
        if (prev.some(m => m.id === msg.id)) return prev;
        return [...prev, msg];
      });

      // Update conversation list
      setConversations(prev => {
        const updated = prev.map(c =>
          c.id === activeConvId
            ? { ...c, last_message: msg, updated_at: msg.created_at }
            : c
        );
        updated.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
        return updated;
      });

      // Also emit via socket so the OTHER user gets it in real-time
      socketRef.current?.emit('notify_dm', {
        conversation_id: activeConvId,
        message: msg,
      });
    } catch (err) {
      console.error('Failed to send message:', err);
      setDraft(body); // restore draft on failure
    }

    inputRef.current?.focus();
  };

  // ── Typing indicator ──
  const handleInputChange = (val: string) => {
    setDraft(val);
    if (!activeConvId || !socketRef.current) return;

    const now = Date.now();
    if (now - lastTypingEmit.current > 2000) {
      socketRef.current.emit('dm_typing', { conversation_id: activeConvId, is_typing: true });
      lastTypingEmit.current = now;
    }
  };

  const handleInputBlur = () => {
    if (activeConvId && socketRef.current) {
      socketRef.current.emit('dm_typing', { conversation_id: activeConvId, is_typing: false });
    }
  };

  // ── Load older messages ──
  const loadOlder = () => {
    if (!activeConvId || !hasMore || loadingMsgs) return;
    const oldest = messages[0];
    if (oldest) fetchMessages(activeConvId, oldest.id);
  };

  // ── Helpers ──
  const formatTime = (iso: string) => {
    const d = new Date(iso);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000);
    if (diffDays === 0) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return d.toLocaleDateString([], { weekday: 'short' });
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  const initial = (name: string) => name.charAt(0).toUpperCase();

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-primary flex flex-col">
        <Navbar onOpenSettings={() => setIsSettingsOpen(true)} />

        <div className="flex-1 flex overflow-hidden max-w-7xl w-full mx-auto">
          {/* ── Conversation List ── */}
          <div
            className={`w-full md:w-80 md:min-w-[320px] border-r border-theme flex flex-col bg-secondary ${
              showThread ? 'hidden md:flex' : 'flex'
            }`}
          >
            <div className="p-4 border-b border-theme">
              <h2 className="text-lg font-bold text-primary">Messages</h2>
            </div>

            <div className="flex-1 overflow-y-auto">
              {loadingConvs ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent" />
                </div>
              ) : conversations.length === 0 ? (
                <div className="text-center py-12 px-4">
                  <svg className="mx-auto h-12 w-12 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-primary">No conversations yet</h3>
                  <p className="mt-1 text-sm text-muted">
                    Message a friend from the{' '}
                    <button onClick={() => router.push('/friends')} className="text-accent hover:underline">
                      Friends page
                    </button>
                    .
                  </p>
                </div>
              ) : (
                conversations.map(conv => (
                  <button
                    key={conv.id}
                    onClick={() => selectConversation(conv.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-hover ${
                      activeConvId === conv.id ? 'bg-hover' : ''
                    }`}
                  >
                    {/* Avatar */}
                    <div className="relative shrink-0">
                      <div className="w-10 h-10 rounded-full bg-accent/20 text-accent flex items-center justify-center text-sm font-bold">
                        {initial(conv.other_user.username)}
                      </div>
                      {onlineFriendIds.has(conv.other_user.id) && (
                        <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-secondary" />
                      )}
                    </div>
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-baseline">
                        <span className="text-sm font-medium text-primary truncate">
                          {conv.other_user.username}
                        </span>
                        {conv.last_message && (
                          <span className="text-xs text-muted ml-2 shrink-0">
                            {formatTime(conv.last_message.created_at)}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <p className="text-xs text-muted truncate flex-1">
                          {conv.last_message
                            ? (conv.last_message.sender_id === user?.id ? 'You: ' : '') + conv.last_message.body
                            : 'No messages yet'}
                        </p>
                        {conv.unread_count > 0 && (
                          <span className="bg-accent text-white text-xs rounded-full px-1.5 py-0.5 min-w-[20px] text-center shrink-0">
                            {conv.unread_count}
                          </span>
                        )}
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* ── Message Thread ── */}
          <div
            className={`flex-1 flex flex-col ${
              !showThread ? 'hidden md:flex' : 'flex'
            }`}
          >
            {activeConv ? (
              <>
                {/* Header */}
                <div className="p-4 border-b border-theme flex items-center gap-3 bg-secondary">
                  {/* Back button (mobile) */}
                  <button
                    onClick={() => setShowThread(false)}
                    className="md:hidden p-1 text-secondary hover:text-primary"
                  >
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  <div className="w-9 h-9 rounded-full bg-accent/20 text-accent flex items-center justify-center text-sm font-bold">
                    {initial(activeConv.other_user.username)}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-primary">{activeConv.other_user.username}</p>
                    {typingUser ? (
                      <p className="text-xs text-accent animate-pulse">typing...</p>
                    ) : onlineFriendIds.has(activeConv.other_user.id) ? (
                      <p className="text-xs text-green-400">Online</p>
                    ) : null}
                  </div>
                </div>

                {/* Messages */}
                <div ref={scrollContainerRef} className="flex-1 overflow-y-auto p-4 space-y-2">
                  {hasMore && (
                    <div className="text-center">
                      <button
                        onClick={loadOlder}
                        disabled={loadingMsgs}
                        className="text-xs text-accent hover:underline disabled:opacity-50"
                      >
                        {loadingMsgs ? 'Loading...' : 'Load older messages'}
                      </button>
                    </div>
                  )}

                  {loadingMsgs && messages.length === 0 && (
                    <div className="flex items-center justify-center py-12">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent" />
                    </div>
                  )}

                  {messages.map(msg => {
                    const isMine = msg.sender_id === user?.id;
                    return (
                      <div key={msg.id} className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}>
                        <div
                          className={`max-w-[75%] rounded-2xl px-4 py-2 ${
                            isMine
                              ? 'bg-accent text-white rounded-br-sm'
                              : 'bg-secondary text-primary rounded-bl-sm'
                          }`}
                        >
                          <p className="text-sm whitespace-pre-wrap break-words">{msg.body}</p>
                          <p className={`text-[10px] mt-1 ${isMine ? 'text-white/60' : 'text-muted'}`}>
                            {formatTime(msg.created_at)}
                            {isMine && msg.read_at && ' \u2713\u2713'}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                  <div ref={bottomRef} />
                </div>

                {/* Input */}
                <div className="p-4 border-t border-theme bg-secondary">
                  <div className="flex items-center gap-2">
                    <input
                      ref={inputRef}
                      type="text"
                      value={draft}
                      onChange={e => handleInputChange(e.target.value)}
                      onBlur={handleInputBlur}
                      onKeyDown={e => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSend();
                        }
                      }}
                      placeholder="Type a message..."
                      className="flex-1 px-4 py-3 bg-primary text-primary rounded-xl border border-transparent focus:border-accent focus:outline-none placeholder:text-muted"
                    />
                    <button
                      onClick={handleSend}
                      disabled={!draft.trim()}
                      className="p-3 bg-accent text-white rounded-xl hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                      </svg>
                    </button>
                  </div>
                </div>
              </>
            ) : (
              /* Empty state when no conversation is selected */
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <svg className="mx-auto h-16 w-16 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  <h3 className="mt-3 text-lg font-medium text-primary">Select a conversation</h3>
                  <p className="mt-1 text-sm text-muted">Choose a conversation or message a friend to get started.</p>
                </div>
              </div>
            )}
          </div>
        </div>

        <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      </div>
    </ProtectedRoute>
  );
}
