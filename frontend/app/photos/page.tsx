'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import Navbar from '@/components/Navbar';
import SettingsModal from '@/components/SettingsModal';
import { api } from '@/lib/api';

interface Photo {
  id: number;
  show_id: number;
  caption?: string;
  filename: string;
  created_at: string;
  artist_name?: string;
  venue_name?: string;
  show_date?: string;
}

interface ShowGroup {
  show_id: number;
  artist_name: string;
  venue_name: string;
  show_date: string;
  photos: Photo[];
}

export default function PhotosPage() {
  const router = useRouter();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [groups, setGroups] = useState<ShowGroup[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'date_desc' | 'date_asc' | 'artist_asc' | 'photos_desc'>('date_desc');

  useEffect(() => {
    fetchPhotos();
  }, []);

  const fetchPhotos = async () => {
    try {
      const response = await api.get('/photos');
      const photos: Photo[] = response.data.photos || response.data || [];
      setTotalCount(photos.length);

      // Group by show_id
      const map = new Map<number, ShowGroup>();
      for (const photo of photos) {
        if (!map.has(photo.show_id)) {
          map.set(photo.show_id, {
            show_id: photo.show_id,
            artist_name: photo.artist_name || 'Unknown Artist',
            venue_name: photo.venue_name || 'Unknown Venue',
            show_date: photo.show_date || '',
            photos: [],
          });
        }
        map.get(photo.show_id)!.photos.push(photo);
      }
      setGroups(Array.from(map.values()));
    } catch (error) {
      console.error('Failed to fetch photos:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '';
    const date = new Date(dateString + 'T12:00:00');
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
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
            <h1 className="text-3xl font-bold text-primary">My Photos</h1>
            <p className="text-secondary mt-2">{totalCount} photos across {groups.length} shows</p>
          </div>

          {/* Content */}
          {loading ? (
            <div className="space-y-6">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="bg-secondary rounded-xl p-4 animate-pulse">
                  <div className="h-5 bg-tertiary rounded w-1/3 mb-4"></div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                    {[...Array(4)].map((_, j) => (
                      <div key={j} className="aspect-square bg-tertiary rounded-lg"></div>
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
                      <p className="text-sm text-muted mt-0.5">{formatDate(group.show_date)} &middot; {group.photos.length} photo{group.photos.length !== 1 ? 's' : ''}</p>
                    </div>
                    <svg className="w-5 h-5 text-muted flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>

                  {/* Photo grid */}
                  <div className="p-4">
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                      {group.photos.map((photo) => (
                        <button
                          key={photo.id}
                          onClick={() => router.push(`/shows/${photo.show_id}`)}
                          className="aspect-square bg-tertiary rounded-lg overflow-hidden hover:opacity-80 transition-all hover:scale-[1.02] active:scale-[0.98] relative group"
                        >
                          <img
                            src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api'}/photos/${photo.id}/thumbnail`}
                            alt={photo.caption || 'Photo'}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              const target = e.target as HTMLImageElement;
                              target.style.display = 'none';
                              target.parentElement!.querySelector('.photo-fallback')?.classList.remove('hidden');
                            }}
                          />
                          <div className="photo-fallback hidden w-full h-full flex items-center justify-center bg-tertiary absolute inset-0">
                            <svg className="w-8 h-8 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                          </div>
                          {photo.caption && (
                            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              <p className="text-white text-xs truncate">{photo.caption}</p>
                            </div>
                          )}
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <h3 className="text-xl font-semibold text-primary mb-2">No photos yet</h3>
              <p className="text-secondary mb-4">Start uploading photos from your shows.</p>
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
