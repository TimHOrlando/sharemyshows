'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import Navbar from '@/components/Navbar';
import SettingsModal from '@/components/SettingsModal';
import { api } from '@/lib/api';

interface Show {
  id: number;
  date: string;
  notes?: string;
  rating?: number;
  owner?: { id: number; username: string };
  artist?: { id: number; name: string };
  venue?: { id: number; name: string; city?: string; state?: string };
  photo_count?: number;
  song_count?: number;
  comment_count?: number;
}

export default function FeedPage() {
  const router = useRouter();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [shows, setShows] = useState<Show[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);

  useEffect(() => {
    fetchFeed();
  }, [page]);

  const fetchFeed = async () => {
    try {
      setLoading(true);
      const response = await api.get('/shows/feed', { params: { page, per_page: 20 } });
      setShows(response.data.shows || []);
      setTotalPages(response.data.pages || 0);
    } catch (error) {
      console.error('Failed to fetch feed:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString + (dateString.length === 10 ? 'T12:00:00' : ''));
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-primary">
        <Navbar onOpenSettings={() => setIsSettingsOpen(true)} />

        <main className="max-w-4xl mx-auto py-6 px-4">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-primary">Friend Activity</h1>
            <p className="text-secondary mt-1">Shows from your friends</p>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-[40vh]">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-accent"></div>
            </div>
          ) : shows.length > 0 ? (
            <div className="space-y-4">
              {shows.map((show) => (
                <div
                  key={show.id}
                  onClick={() => router.push(`/shows/${show.id}`)}
                  className="bg-secondary rounded-xl p-5 hover:bg-tertiary transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-7 h-7 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0">
                          <span className="text-xs font-bold text-accent">
                            {show.owner?.username?.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <span className="text-sm text-accent font-medium">{show.owner?.username}</span>
                      </div>
                      <h3 className="text-lg font-semibold text-primary">
                        {show.artist?.name || 'Unknown Artist'}
                      </h3>
                      <p className="text-secondary">
                        {show.venue?.name || 'Unknown Venue'}
                      </p>
                      {(show.venue?.city || show.venue?.state) && (
                        <p className="text-sm text-muted">
                          {[show.venue?.city, show.venue?.state].filter(Boolean).join(', ')}
                        </p>
                      )}
                      <p className="text-sm text-muted mt-1">{formatDate(show.date)}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1 ml-4">
                      {show.rating && (
                        <div className="flex items-center gap-0.5">
                          {[...Array(5)].map((_, i) => (
                            <svg key={i} className={`w-4 h-4 ${i < show.rating! ? 'text-accent fill-current' : 'text-muted stroke-current fill-none'}`} viewBox="0 0 20 20">
                              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                            </svg>
                          ))}
                        </div>
                      )}
                      <div className="flex items-center gap-3 text-xs text-muted">
                        {(show.song_count ?? 0) > 0 && <span>{show.song_count} songs</span>}
                        {(show.photo_count ?? 0) > 0 && <span>{show.photo_count} photos</span>}
                        {(show.comment_count ?? 0) > 0 && <span>{show.comment_count} comments</span>}
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-4 pt-4">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-4 py-2 bg-tertiary text-secondary rounded-lg hover:text-primary transition-colors disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-muted">Page {page} of {totalPages}</span>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="px-4 py-2 bg-tertiary text-secondary rounded-lg hover:text-primary transition-colors disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-secondary rounded-xl p-12 text-center">
              <svg className="w-16 h-16 text-muted mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <h2 className="text-xl font-semibold text-primary mb-2">No friend activity yet</h2>
              <p className="text-secondary mb-6">Add friends to see their shows in your feed.</p>
              <button
                onClick={() => router.push('/friends')}
                className="px-6 py-3 bg-accent text-white rounded-lg hover:opacity-90 transition-colors"
              >
                Find Friends
              </button>
            </div>
          )}
        </main>

        <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      </div>
    </ProtectedRoute>
  );
}
