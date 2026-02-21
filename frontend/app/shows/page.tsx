'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import Navbar from '@/components/Navbar';
import SettingsModal from '@/components/SettingsModal';
import AddShowModal from '@/components/AddShowModal';
import { api } from '@/lib/api';

interface Artist {
  id: number;
  name: string;
}

interface Venue {
  id: number;
  name: string;
  city?: string;
  state?: string;
}

interface Show {
  id: number;
  date: string;
  notes?: string;
  rating?: number;
  created_at: string;
  artist: Artist;
  venue: Venue;
}

export default function ShowsPage() {
  return (
    <Suspense fallback={
      <ProtectedRoute>
        <div className="min-h-screen bg-primary">
          <Navbar onOpenSettings={() => {}} />
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-accent border-t-transparent"></div>
          </div>
        </div>
      </ProtectedRoute>
    }>
      <ShowsContent />
    </Suspense>
  );
}

function ShowsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isAddShowOpen, setIsAddShowOpen] = useState(false);
  const [shows, setShows] = useState<Show[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'upcoming' | 'past'>('all');
  const [filterLabel, setFilterLabel] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'date_desc' | 'date_asc' | 'artist_asc' | 'venue_asc'>('date_desc');

  const artistId = searchParams.get('artist_id');
  const venueId = searchParams.get('venue_id');
  const artistName = searchParams.get('artist');
  const venueName = searchParams.get('venue');
  const filterParam = searchParams.get('filter');

  // Set initial filter from URL query param
  useEffect(() => {
    if (filterParam === 'upcoming' || filterParam === 'past') {
      setFilter(filterParam);
    }
  }, [filterParam]);

  useEffect(() => {
    fetchShows();
  }, [artistId, venueId, artistName, venueName]);

  const fetchShows = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (artistId) params.set('artist_id', artistId);
      if (venueId) params.set('venue_id', venueId);
      if (artistName) params.set('artist', artistName);
      if (venueName) params.set('venue', venueName);
      const query = params.toString();
      const response = await api.get(`/shows${query ? `?${query}` : ''}`);
      setShows(response.data || []);

      // Build filter label from response data
      if (artistId && response.data?.length > 0) {
        setFilterLabel(response.data[0].artist?.name || null);
      } else if (venueId && response.data?.length > 0) {
        setFilterLabel(response.data[0].venue?.name || null);
      } else if (artistName) {
        setFilterLabel(artistName);
      } else if (venueName) {
        setFilterLabel(venueName);
      } else {
        setFilterLabel(null);
      }
    } catch (error) {
      console.error('Failed to fetch shows:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleShowAdded = (showId?: number) => {
    if (showId) {
      router.push(`/shows/${showId}?autoSetlist=1`);
    } else {
      fetchShows();
    }
  };

  const handleShowClick = (showId: number) => {
    router.push(`/shows/${showId}`);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString + (dateString.length === 10 ? 'T12:00:00' : ''));
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getFilteredShows = () => {
    const now = new Date();
    now.setHours(0, 0, 0, 0);

    let result = shows;

    // Time filter
    if (filter === 'upcoming') {
      result = result.filter(show => new Date(show.date + 'T12:00:00') >= now);
    } else if (filter === 'past') {
      result = result.filter(show => new Date(show.date + 'T12:00:00') < now);
    }

    // Search filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(show =>
        show.artist?.name?.toLowerCase().includes(q) ||
        show.venue?.name?.toLowerCase().includes(q) ||
        show.venue?.city?.toLowerCase().includes(q) ||
        show.venue?.state?.toLowerCase().includes(q)
      );
    }

    // Sort
    result = [...result].sort((a, b) => {
      switch (sortBy) {
        case 'date_asc':
          return a.date.localeCompare(b.date);
        case 'artist_asc':
          return (a.artist?.name || '').localeCompare(b.artist?.name || '');
        case 'venue_asc':
          return (a.venue?.name || '').localeCompare(b.venue?.name || '');
        case 'date_desc':
        default:
          return b.date.localeCompare(a.date);
      }
    });

    return result;
  };

  const filteredShows = getFilteredShows();

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-primary">
        <Navbar onOpenSettings={() => setIsSettingsOpen(true)} />

        <main className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          {/* Header with Add Show CTA */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-primary">
                {filterLabel ? `Shows: ${filterLabel}` : 'My Shows'}
              </h1>
              <p className="text-secondary">
                {filteredShows.length !== shows.length
                  ? `${filteredShows.length} of ${shows.length} shows`
                  : `${shows.length} ${shows.length === 1 ? 'show' : 'shows'} ${filterLabel ? 'found' : 'documented'}`}
              </p>
              {filterLabel && (
                <button
                  onClick={() => router.push('/shows')}
                  className="mt-1 text-sm text-accent hover:underline"
                >
                  Clear filter
                </button>
              )}
            </div>
            <button
              onClick={() => setIsAddShowOpen(true)}
              className="flex items-center justify-center gap-2 px-6 py-3 bg-accent rounded-xl text-white font-semibold touch-target transition-all hover:scale-[1.02] active:scale-[0.98]"
              style={{ backgroundColor: 'var(--accent-primary)' }}
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Show
            </button>
          </div>

          {/* Filter Tabs */}
          <div className="bg-secondary rounded-xl mb-6 overflow-hidden">
            <div className="flex">
              {[
                { key: 'all', label: `All (${shows.length})` },
                { key: 'past', label: 'Past Shows' },
                { key: 'upcoming', label: 'Upcoming' },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setFilter(tab.key as 'all' | 'past' | 'upcoming')}
                  className={`flex-1 px-4 py-4 text-sm font-medium transition-colors ${
                    filter === tab.key
                      ? 'bg-accent text-white'
                      : 'text-secondary hover:text-primary hover:bg-tertiary'
                  }`}
                  style={filter === tab.key ? { backgroundColor: 'var(--accent-primary)' } : {}}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Search & Sort */}
          <div className="flex flex-col sm:flex-row gap-3 mb-6">
            <div className="relative flex-1">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search artist, venue, or city..."
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
              <option value="date_desc">Date: Newest First</option>
              <option value="date_asc">Date: Oldest First</option>
              <option value="artist_asc">Artist: A-Z</option>
              <option value="venue_asc">Venue: A-Z</option>
            </select>
          </div>

          {/* Shows Grid */}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-accent border-t-transparent"></div>
            </div>
          ) : filteredShows.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredShows.map((show) => (
                <div
                  key={show.id}
                  onClick={() => handleShowClick(show.id)}
                  className="bg-secondary rounded-xl overflow-hidden cursor-pointer transition-all hover:scale-[1.02] hover:bg-tertiary active:scale-[0.98]"
                >
                  {/* Gradient Header */}
                  <div className="px-5 py-3" style={{ background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-muted))' }}>
                    <p className="text-white/90 text-sm font-medium">
                      {formatDate(show.date)}
                    </p>
                  </div>

                  {/* Card Body */}
                  <div className="p-5">
                    <h3 className="text-xl font-bold text-primary mb-2">
                      {show.artist?.name || 'Unknown Artist'}
                    </h3>
                    
                    <div className="flex items-start gap-2 text-secondary mb-3">
                      <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      <div>
                        <p className="font-medium">{show.venue?.name || 'Unknown Venue'}</p>
                        {(show.venue?.city || show.venue?.state) && (
                          <p className="text-sm text-muted">
                            {[show.venue.city, show.venue.state].filter(Boolean).join(', ')}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Rating */}
                    {show.rating && (
                      <div className="flex items-center gap-1 mb-3">
                        {[...Array(5)].map((_, i) => (
                          <svg
                            key={i}
                            className={`w-5 h-5 ${i < show.rating! ? 'text-yellow-400' : 'text-muted'}`}
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                        ))}
                      </div>
                    )}

                    {show.notes && (
                      <p className="text-sm text-muted line-clamp-2">{show.notes}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-secondary rounded-xl p-12 text-center">
              <div className="text-5xl mb-4">??</div>
              <h3 className="text-lg font-semibold text-primary mb-2">No shows found</h3>
              <p className="text-secondary mb-6">
                {filter === 'all'
                  ? 'Start documenting your concert experiences!'
                  : filter === 'upcoming'
                  ? 'No upcoming shows scheduled.'
                  : 'No past shows documented yet.'}
              </p>
              <button
                onClick={() => setIsAddShowOpen(true)}
                className="inline-flex items-center gap-2 px-6 py-3 bg-accent rounded-xl text-white font-semibold touch-target"
                style={{ backgroundColor: 'var(--accent-primary)' }}
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Your First Show
              </button>
            </div>
          )}
        </main>

        <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
        <AddShowModal isOpen={isAddShowOpen} onClose={() => setIsAddShowOpen(false)} onSuccess={handleShowAdded} />
      </div>
    </ProtectedRoute>
  );
}



