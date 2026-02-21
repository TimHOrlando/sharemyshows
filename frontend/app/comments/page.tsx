'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import Navbar from '@/components/Navbar';
import SettingsModal from '@/components/SettingsModal';
import { api } from '@/lib/api';

interface Comment {
  id: number;
  show_id: number;
  photo_id?: number | null;
  text: string;
  created_at: string;
  artist_name?: string;
  venue_name?: string;
  show_date?: string;
  photo_caption?: string;
}

interface ShowGroup {
  show_id: number;
  artist_name: string;
  venue_name: string;
  show_date: string;
  comments: Comment[];
}

export default function CommentsPage() {
  const router = useRouter();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [groups, setGroups] = useState<ShowGroup[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchComments();
  }, []);

  const fetchComments = async () => {
    try {
      const response = await api.get('/comments');
      const comments: Comment[] = response.data.comments || response.data || [];
      setTotalCount(comments.length);

      const map = new Map<number, ShowGroup>();
      for (const comment of comments) {
        if (!map.has(comment.show_id)) {
          map.set(comment.show_id, {
            show_id: comment.show_id,
            artist_name: comment.artist_name || 'Unknown Artist',
            venue_name: comment.venue_name || 'Unknown Venue',
            show_date: comment.show_date || '',
            comments: [],
          });
        }
        map.get(comment.show_id)!.comments.push(comment);
      }
      setGroups(Array.from(map.values()));
    } catch (error) {
      console.error('Failed to fetch comments:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '';
    const date = new Date(dateString + 'T12:00:00');
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
  };

  const formatTimestamp = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 30) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-primary">
        <Navbar onOpenSettings={() => setIsSettingsOpen(true)} />

        <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="mb-6">
            <button
              onClick={() => router.back()}
              className="flex items-center gap-2 text-secondary hover:text-primary mb-4 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back
            </button>
            <h1 className="text-3xl font-bold text-primary">My Comments</h1>
            <p className="text-secondary mt-2">{totalCount} comments across {groups.length} shows</p>
          </div>

          {/* Content */}
          {loading ? (
            <div className="space-y-6">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="bg-secondary rounded-xl p-4 animate-pulse">
                  <div className="h-5 bg-tertiary rounded w-1/3 mb-4"></div>
                  <div className="space-y-3">
                    {[...Array(3)].map((_, j) => (
                      <div key={j} className="h-12 bg-tertiary rounded-lg"></div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : groups.length > 0 ? (
            <div className="space-y-6">
              {groups.map((group) => (
                <div key={group.show_id} className="bg-secondary rounded-xl overflow-hidden">
                  {/* Show header */}
                  <button
                    onClick={() => router.push(`/shows/${group.show_id}`)}
                    className="w-full px-5 py-4 border-b border-theme flex items-center justify-between hover:bg-tertiary transition-colors text-left"
                  >
                    <div>
                      <p className="font-semibold text-primary">{group.artist_name} at {group.venue_name}</p>
                      <p className="text-sm text-muted mt-0.5">{formatDate(group.show_date)} &middot; {group.comments.length} comment{group.comments.length !== 1 ? 's' : ''}</p>
                    </div>
                    <svg className="w-5 h-5 text-muted flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>

                  {/* Comments list */}
                  <div className="divide-y divide-theme">
                    {group.comments.map((comment) => (
                      <button
                        key={comment.id}
                        onClick={() => router.push(`/shows/${comment.show_id}`)}
                        className="w-full px-5 py-3 hover:bg-tertiary transition-colors text-left flex items-start gap-3"
                      >
                        {comment.photo_id ? (
                          <svg className="w-5 h-5 text-muted flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        ) : (
                          <svg className="w-5 h-5 text-muted flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                          </svg>
                        )}
                        <div className="flex-1 min-w-0">
                          {comment.photo_id && comment.photo_caption && (
                            <p className="text-muted text-xs mb-1">on photo: {comment.photo_caption}</p>
                          )}
                          <p className="text-primary text-sm whitespace-pre-wrap">{comment.text}</p>
                          <p className="text-muted text-xs mt-1">{formatTimestamp(comment.created_at)}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-secondary rounded-xl p-12 text-center">
              <svg className="w-16 h-16 text-muted mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
              </svg>
              <h3 className="text-xl font-semibold text-primary mb-2">No comments yet</h3>
              <p className="text-secondary mb-4">Start commenting on shows to see them here.</p>
              <button
                onClick={() => router.push('/shows')}
                className="px-6 py-3 rounded-full font-semibold text-white transition-all hover:scale-105"
                style={{ backgroundColor: 'var(--accent-primary)' }}
              >
                Go to My Shows
              </button>
            </div>
          )}
        </main>

        <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      </div>
    </ProtectedRoute>
  );
}
