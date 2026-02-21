'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import Navbar from '@/components/Navbar';
import SettingsModal from '@/components/SettingsModal';
import { api } from '@/lib/api';

interface Video {
  id: number;
  show_id: number;
  title?: string;
  original_filename?: string;
  duration?: number;
  file_size?: number;
  created_at: string;
  url: string;
  artist_name?: string;
  venue_name?: string;
  show_date?: string;
}

interface ShowGroup {
  show_id: number;
  artist_name: string;
  venue_name: string;
  show_date: string;
  videos: Video[];
}

export default function VideosPage() {
  const router = useRouter();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [groups, setGroups] = useState<ShowGroup[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      const response = await api.get('/videos');
      const videos: Video[] = response.data.recordings || response.data || [];
      setTotalCount(videos.length);

      const map = new Map<number, ShowGroup>();
      for (const video of videos) {
        if (!map.has(video.show_id)) {
          map.set(video.show_id, {
            show_id: video.show_id,
            artist_name: video.artist_name || 'Unknown Artist',
            venue_name: video.venue_name || 'Unknown Venue',
            show_date: video.show_date || '',
            videos: [],
          });
        }
        map.get(video.show_id)!.videos.push(video);
      }
      setGroups(Array.from(map.values()));
    } catch (error) {
      console.error('Failed to fetch videos:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '';
    const date = new Date(dateString + 'T12:00:00');
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
  };

  const formatDuration = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
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
            <h1 className="text-3xl font-bold text-primary">My Videos</h1>
            <p className="text-secondary mt-2">{totalCount} videos across {groups.length} shows</p>
          </div>

          {/* Content */}
          {loading ? (
            <div className="space-y-6">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="bg-secondary rounded-xl p-4 animate-pulse">
                  <div className="h-5 bg-tertiary rounded w-1/3 mb-4"></div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {[...Array(2)].map((_, j) => (
                      <div key={j} className="aspect-video bg-tertiary rounded-lg"></div>
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
                      <p className="text-sm text-muted mt-0.5">{formatDate(group.show_date)} &middot; {group.videos.length} video{group.videos.length !== 1 ? 's' : ''}</p>
                    </div>
                    <svg className="w-5 h-5 text-muted flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>

                  {/* Video grid */}
                  <div className="p-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {group.videos.map((video) => (
                        <button
                          key={video.id}
                          onClick={() => router.push(`/shows/${video.show_id}`)}
                          className="bg-tertiary rounded-lg overflow-hidden hover:ring-2 hover:ring-accent/50 transition-all text-left group"
                        >
                          <div className="aspect-video bg-black relative flex items-center justify-center">
                            <svg className="w-14 h-14 text-white/40 group-hover:text-white/70 transition-colors" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M8 5v14l11-7z" />
                            </svg>
                            {video.duration && (
                              <span className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-0.5 rounded">
                                {formatDuration(video.duration)}
                              </span>
                            )}
                          </div>
                          <div className="p-3">
                            <p className="text-primary font-medium text-sm truncate">
                              {video.title || video.original_filename || 'Untitled'}
                            </p>
                            {video.file_size && (
                              <p className="text-muted text-xs mt-0.5">{(video.file_size / (1024 * 1024)).toFixed(1)} MB</p>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-secondary rounded-xl p-12 text-center">
              <svg className="w-16 h-16 text-muted mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <h3 className="text-xl font-semibold text-primary mb-2">No videos yet</h3>
              <p className="text-secondary mb-4">Record or upload videos from your shows.</p>
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
