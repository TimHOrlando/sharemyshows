'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import Navbar from '@/components/Navbar';
import SettingsModal from '@/components/SettingsModal';
import { api } from '@/lib/api';



interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

interface Friendship {
  id: number;
  user_id: number;
  friend_id: number;
  status: string;
  created_at: string;
  friend: User;
}

export default function FriendsPage() {
  const router = useRouter();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'friends' | 'requests' | 'search'>('friends');

  // Friends list
  const [friends, setFriends] = useState<Friendship[]>([]);
  const [loadingFriends, setLoadingFriends] = useState(true);

  // Friend requests
  const [requests, setRequests] = useState<Friendship[]>([]);
  const [loadingRequests, setLoadingRequests] = useState(false);

  // Search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [searching, setSearching] = useState(false);

  // Action states
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetchFriends();
  }, []);

  useEffect(() => {
    if (activeTab === 'requests') {
      fetchRequests();
    }
  }, [activeTab]);

  const fetchFriends = async () => {
    try {
      setLoadingFriends(true);

      const response = await api.get(`/friends`, {
      });
      setFriends(response.data.friends || []);
    } catch (error) {
      console.error('Failed to fetch friends:', error);
    } finally {
      setLoadingFriends(false);
    }
  };

  const fetchRequests = async () => {
    try {
      setLoadingRequests(true);

      const response = await api.get(`/friends/requests`, {
      });
      setRequests(response.data.friends || []);
    } catch (error) {
      console.error('Failed to fetch friend requests:', error);
    } finally {
      setLoadingRequests(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setSearching(true);

      const response = await api.get(`/friends/search`, {
        params: { query: searchQuery },
      });
      setSearchResults(response.data.users || []);
    } catch (error) {
      console.error('Search failed:', error);
      showMessage('error', 'Search failed. Please try again.');
    } finally {
      setSearching(false);
    }
  };

  const sendFriendRequest = async (friendId: number) => {
    try {
      setActionLoading(friendId);

      await api.post(
        `/friends/request`,
        { friend_id: friendId },
      );
      showMessage('success', 'Friend request sent!');
      // Remove from search results
      setSearchResults(searchResults.filter(u => u.id !== friendId));
    } catch (error) {
      const errorMsg = (error as { response?: { data?: { error?: string } } }).response?.data?.error || 'Failed to send friend request';
      showMessage('error', errorMsg);
    } finally {
      setActionLoading(null);
    }
  };

  const acceptFriendRequest = async (requestId: number) => {
    try {
      setActionLoading(requestId);

      await api.post(
        `/friends/request/${requestId}/accept`,
        {},
      );
      showMessage('success', 'Friend request accepted!');
      fetchRequests();
      fetchFriends();
    } catch (error) {
      const errorMsg = (error as { response?: { data?: { error?: string } } }).response?.data?.error || 'Failed to accept friend request';
      showMessage('error', errorMsg);
    } finally {
      setActionLoading(null);
    }
  };

  const rejectFriendRequest = async (requestId: number) => {
    try {
      setActionLoading(requestId);

      await api.post(
        `/friends/request/${requestId}/reject`,
        {},
      );
      showMessage('success', 'Friend request rejected');
      fetchRequests();
    } catch (error) {
      const errorMsg = (error as { response?: { data?: { error?: string } } }).response?.data?.error || 'Failed to reject friend request';
      showMessage('error', errorMsg);
    } finally {
      setActionLoading(null);
    }
  };

  const removeFriend = async (friendshipId: number) => {
    if (!confirm('Are you sure you want to remove this friend?')) return;

    try {
      setActionLoading(friendshipId);

      await api.delete(`/friends/${friendshipId}`, {
      });
      showMessage('success', 'Friend removed');
      fetchFriends();
    } catch (error) {
      const errorMsg = (error as { response?: { data?: { error?: string } } }).response?.data?.error || 'Failed to remove friend';
      showMessage('error', errorMsg);
    } finally {
      setActionLoading(null);
    }
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-primary">
        <Navbar onOpenSettings={() => setIsSettingsOpen(true)} />

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="px-4 py-6 sm:px-0">
            <div className="bg-card rounded-lg shadow-theme-md px-6 py-8">
              <h1 className="text-3xl font-bold text-primary">Friends</h1>
              <p className="mt-2 text-secondary">
                Connect with fellow music lovers and share your concert experiences.
              </p>
            </div>
          </div>

          {/* Message Alert */}
          {message && (
            <div className="px-4 sm:px-0 mb-4">
              <div className={`rounded-md p-4 ${
                message.type === 'success' ? 'bg-green-500/20 border border-green-500/50' : 'bg-red-500/20 border border-red-500/50'
              }`}>
                <p className={`text-sm ${
                  message.type === 'success' ? 'text-green-400' : 'text-red-400'
                }`}>
                  {message.text}
                </p>
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="px-4 sm:px-0">
            <div className="bg-card rounded-lg shadow-theme-md">
              <div className="border-b border-theme">
                <nav className="flex -mb-px">
                  <button
                    onClick={() => setActiveTab('friends')}
                    className={`px-6 py-4 text-sm font-medium border-b-2 ${
                      activeTab === 'friends'
                        ? 'border-accent text-accent'
                        : 'border-transparent text-muted hover:text-secondary hover:border-theme'
                    }`}
                  >
                    My Friends ({friends.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('requests')}
                    className={`px-6 py-4 text-sm font-medium border-b-2 ${
                      activeTab === 'requests'
                        ? 'border-accent text-accent'
                        : 'border-transparent text-muted hover:text-secondary hover:border-theme'
                    }`}
                  >
                    Requests
                    {requests.length > 0 && (
                      <span className="ml-2 bg-red-500 text-white text-xs rounded-full px-2 py-1">
                        {requests.length}
                      </span>
                    )}
                  </button>
                  <button
                    onClick={() => setActiveTab('search')}
                    className={`px-6 py-4 text-sm font-medium border-b-2 ${
                      activeTab === 'search'
                        ? 'border-accent text-accent'
                        : 'border-transparent text-muted hover:text-secondary hover:border-theme'
                    }`}
                  >
                    Find Friends
                  </button>
                </nav>
              </div>

              {/* Tab Content */}
              <div className="p-6">
                {/* Friends List Tab */}
                {activeTab === 'friends' && (
                  <div>
                    {loadingFriends ? (
                      <div className="text-center py-12">
                        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
                        <p className="mt-2 text-sm text-muted">Loading friends...</p>
                      </div>
                    ) : friends.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {friends.map((friendship) => (
                          <div key={friendship.id} className="bg-secondary rounded-xl p-4 hover:bg-tertiary transition-colors">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <h3 className="text-lg font-medium text-primary">
                                  {friendship.friend.username}
                                </h3>
                                <p className="text-sm text-muted">{friendship.friend.email}</p>
                                <p className="text-xs text-muted mt-2">
                                  Friends since {formatDate(friendship.created_at)}
                                </p>
                              </div>
                            </div>
                            <div className="mt-3 flex gap-2">
                              <button
                                onClick={() => router.push(`/shows?friend_id=${friendship.friend.id}`)}
                                className="flex-1 px-3 py-2 text-sm text-accent border border-accent/50 rounded-md hover:bg-accent/10 transition-colors"
                              >
                                View Shows
                              </button>
                              <button
                                onClick={() => removeFriend(friendship.id)}
                                disabled={actionLoading === friendship.id}
                                className="flex-1 px-3 py-2 text-sm text-red-400 border border-red-500/50 rounded-md hover:bg-red-500/10 disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                {actionLoading === friendship.id ? 'Removing...' : 'Remove'}
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <svg className="mx-auto h-12 w-12 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                        </svg>
                        <h3 className="mt-2 text-sm font-medium text-primary">No friends yet</h3>
                        <p className="mt-1 text-sm text-muted">Start by searching for users to connect with.</p>
                        <button
                          onClick={() => setActiveTab('search')}
                          className="mt-4 px-4 py-2 text-sm text-white bg-accent rounded-md hover:opacity-90"
                        >
                          Find Friends
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Friend Requests Tab */}
                {activeTab === 'requests' && (
                  <div>
                    {loadingRequests ? (
                      <div className="text-center py-12">
                        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
                        <p className="mt-2 text-sm text-muted">Loading requests...</p>
                      </div>
                    ) : requests.length > 0 ? (
                      <div className="space-y-4">
                        {requests.map((request) => (
                          <div key={request.id} className="bg-secondary rounded-xl p-4 flex items-center justify-between hover:bg-tertiary transition-colors">
                            <div className="flex-1">
                              <h3 className="text-lg font-medium text-primary">
                                {request.friend.username}
                              </h3>
                              <p className="text-sm text-muted">{request.friend.email}</p>
                              <p className="text-xs text-muted mt-1">
                                Sent {formatDate(request.created_at)}
                              </p>
                            </div>
                            <div className="flex gap-2">
                              <button
                                onClick={() => acceptFriendRequest(request.id)}
                                disabled={actionLoading === request.id}
                                className="px-4 py-2 text-sm text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                {actionLoading === request.id ? 'Processing...' : 'Accept'}
                              </button>
                              <button
                                onClick={() => rejectFriendRequest(request.id)}
                                disabled={actionLoading === request.id}
                                className="px-4 py-2 text-sm text-red-400 border border-red-500/50 rounded-md hover:bg-red-500/10 disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                Reject
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <svg className="mx-auto h-12 w-12 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                        </svg>
                        <h3 className="mt-2 text-sm font-medium text-primary">No pending requests</h3>
                        <p className="mt-1 text-sm text-muted">You don&apos;t have any friend requests at the moment.</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Search Tab */}
                {activeTab === 'search' && (
                  <div>
                    <form onSubmit={handleSearch} className="mb-6">
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          placeholder="Search by username or email..."
                          className="flex-1 px-4 py-2 border border-theme rounded-md bg-secondary text-primary placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent"
                        />
                        <button
                          type="submit"
                          disabled={searching || !searchQuery.trim()}
                          className="px-6 py-2 text-white bg-accent rounded-md hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {searching ? 'Searching...' : 'Search'}
                        </button>
                      </div>
                    </form>

                    {searchResults.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {searchResults.map((user) => (
                          <div key={user.id} className="bg-secondary rounded-xl p-4 hover:bg-tertiary transition-colors">
                            <div className="flex-1 mb-3">
                              <h3 className="text-lg font-medium text-primary">{user.username}</h3>
                              <p className="text-sm text-muted">{user.email}</p>
                              <p className="text-xs text-muted mt-1">
                                Member since {formatDate(user.created_at)}
                              </p>
                            </div>
                            <button
                              onClick={() => sendFriendRequest(user.id)}
                              disabled={actionLoading === user.id}
                              className="w-full px-3 py-2 text-sm text-white bg-accent rounded-md hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {actionLoading === user.id ? 'Sending...' : 'Add Friend'}
                            </button>
                          </div>
                        ))}
                      </div>
                    ) : searchQuery && !searching ? (
                      <div className="text-center py-12">
                        <p className="text-sm text-muted">No users found matching &quot;{searchQuery}&quot;</p>
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <svg className="mx-auto h-12 w-12 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        <h3 className="mt-2 text-sm font-medium text-primary">Search for users</h3>
                        <p className="mt-1 text-sm text-muted">Enter a username or email to find friends.</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>

        {/* Settings Modal */}
        <SettingsModal
          isOpen={isSettingsOpen}
          onClose={() => setIsSettingsOpen(false)}
        />
      </div>
    </ProtectedRoute>
  );
}
