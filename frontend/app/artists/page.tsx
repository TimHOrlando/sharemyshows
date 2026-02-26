'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import Navbar from '@/components/Navbar';
import SettingsModal from '@/components/SettingsModal';
import { api } from '@/lib/api';

interface Artist {
  artist_id: number;
  artist_name: string;
  show_count: number;
  description: string;
  image_url: string;
}

interface TooltipState {
  artistId: number | null;
  x: number;
  y: number;
}

export default function ArtistsPage() {
  const router = useRouter();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [artists, setArtists] = useState<Artist[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'shows_desc' | 'shows_asc' | 'name_asc' | 'name_desc'>('shows_desc');
  const [tooltip, setTooltip] = useState<TooltipState>({ artistId: null, x: 0, y: 0 });
  const tooltipTimeout = useRef<NodeJS.Timeout | null>(null);

  const showTooltip = (artistId: number, e: React.MouseEvent) => {
    if (tooltipTimeout.current) clearTimeout(tooltipTimeout.current);
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    setTooltip({ artistId, x: rect.left, y: rect.bottom + 8 });
  };

  const hideTooltip = () => {
    tooltipTimeout.current = setTimeout(() => setTooltip({ artistId: null, x: 0, y: 0 }), 150);
  };

  const keepTooltip = () => {
    if (tooltipTimeout.current) clearTimeout(tooltipTimeout.current);
  };

  useEffect(() => {
    fetchArtists();
  }, []);

  const fetchArtists = async () => {
    try {
      const response = await api.get('/dashboard/artists');
      setArtists(response.data.artists || []);
    } catch (error) {
      console.error('Failed to fetch artists:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredArtists = () => {
    let result = artists;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(artist =>
        artist.artist_name.toLowerCase().includes(q) ||
        artist.description?.toLowerCase().includes(q)
      );
    }

    result = [...result].sort((a, b) => {
      switch (sortBy) {
        case 'shows_asc':
          return a.show_count - b.show_count;
        case 'name_asc':
          return a.artist_name.localeCompare(b.artist_name);
        case 'name_desc':
          return b.artist_name.localeCompare(a.artist_name);
        case 'shows_desc':
        default:
          return b.show_count - a.show_count;
      }
    });

    return result;
  };

  const filteredArtists = getFilteredArtists();

  const handleArtistClick = (artistId: number) => {
    router.push(`/shows?artist_id=${artistId}`);
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
            <h1 className="text-3xl font-bold text-primary">My Artists</h1>
            <p className="text-secondary mt-2">
              {filteredArtists.length !== artists.length
                ? `${filteredArtists.length} of ${artists.length} artists`
                : `${artists.length} artists seen`}
            </p>
          </div>

          {/* Search & Sort */}
          <div className="flex flex-col sm:flex-row gap-3 mb-6">
            <div className="relative flex-1">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search artists..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-secondary text-primary rounded-xl border border-transparent focus:border-accent focus:outline-none placeholder:text-muted"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-primary"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
              className="px-4 py-3 bg-secondary text-primary rounded-xl border border-transparent focus:border-accent focus:outline-none cursor-pointer appearance-none"
              style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='none' viewBox='0 0 24 24' stroke='%239ca3af'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'/%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center', paddingRight: '2.5rem' }}
            >
              <option value="shows_desc">Most Shows</option>
              <option value="shows_asc">Fewest Shows</option>
              <option value="name_asc">Name: A-Z</option>
              <option value="name_desc">Name: Z-A</option>
            </select>
          </div>

          {/* Artists Grid */}
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-secondary rounded-xl p-6 animate-pulse">
                  <div className="h-6 bg-tertiary rounded w-3/4 mb-2"></div>
                  <div className="h-4 bg-tertiary rounded w-1/2"></div>
                </div>
              ))}
            </div>
          ) : filteredArtists.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredArtists.map((artist) => (
                <button
                  key={artist.artist_id}
                  onClick={() => handleArtistClick(artist.artist_id)}
                  className="bg-secondary rounded-xl p-6 text-left hover:bg-tertiary transition-all hover:scale-[1.02] active:scale-[0.98]"
                >
                  <div className="flex items-center gap-4">
                    {artist.image_url ? (
                      <img
                        src={artist.image_url}
                        alt={artist.artist_name}
                        className="w-12 h-12 rounded-full object-cover flex-shrink-0"
                        onError={(e) => {
                          // Fallback to icon on load failure
                          const target = e.currentTarget;
                          target.style.display = 'none';
                          target.nextElementSibling?.classList.remove('hidden');
                        }}
                      />
                    ) : null}
                    <div className={`w-12 h-12 rounded-full bg-tertiary flex items-center justify-center flex-shrink-0${artist.image_url ? ' hidden' : ''}`}>
                      <svg className="w-6 h-6 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-primary truncate">{artist.artist_name}</h3>
                      <p className="text-sm text-secondary">{artist.show_count} {artist.show_count === 1 ? 'show' : 'shows'}</p>
                    </div>
                    <svg className="w-5 h-5 text-muted flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                  {artist.description && (
                    <p
                      className="text-sm text-muted mt-3 line-clamp-2"
                      onMouseEnter={(e) => showTooltip(artist.artist_id, e)}
                      onMouseLeave={hideTooltip}
                    >
                      {artist.description}
                    </p>
                  )}
                </button>
              ))}
            </div>
          ) : (
            <div className="bg-secondary rounded-xl p-12 text-center">
              <svg className="w-16 h-16 text-muted mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
              {artists.length > 0 ? (
                <>
                  <h3 className="text-xl font-semibold text-primary mb-2">No artists found</h3>
                  <p className="text-secondary mb-4">Try a different search term.</p>
                  <button
                    onClick={() => setSearchQuery('')}
                    className="px-6 py-3 rounded-full font-semibold text-white transition-all hover:scale-105"
                    style={{ backgroundColor: 'var(--accent-primary)' }}
                  >
                    Clear Search
                  </button>
                </>
              ) : (
                <>
                  <h3 className="text-xl font-semibold text-primary mb-2">No artists yet</h3>
                  <p className="text-secondary mb-4">Start adding shows to see your artists here.</p>
                  <button
                    onClick={() => router.push('/dashboard')}
                    className="px-6 py-3 rounded-full font-semibold text-white transition-all hover:scale-105"
                    style={{ backgroundColor: 'var(--accent-primary)' }}
                  >
                    Add Your First Show
                  </button>
                </>
              )}
            </div>
          )}
          {/* Themed Tooltip */}
          {tooltip.artistId && (() => {
            const artist = filteredArtists.find(a => a.artist_id === tooltip.artistId);
            if (!artist?.description) return null;
            return (
              <div
                className="fixed z-50 max-w-sm rounded-lg shadow-lg border p-4 text-sm"
                style={{
                  left: tooltip.x,
                  top: tooltip.y,
                  backgroundColor: 'var(--bg-tertiary)',
                  borderColor: 'var(--border-primary)',
                  color: 'var(--text-secondary)',
                  maxHeight: '300px',
                  overflowY: 'auto',
                }}
                onMouseEnter={keepTooltip}
                onMouseLeave={hideTooltip}
              >
                <p className="font-semibold text-primary mb-2">{artist.artist_name}</p>
                <p>{artist.description}</p>
              </div>
            );
          })()}
        </main>

        <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      </div>
    </ProtectedRoute>
  );
}
