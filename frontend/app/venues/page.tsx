'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import Navbar from '@/components/Navbar';
import SettingsModal from '@/components/SettingsModal';
import { api } from '@/lib/api';

interface Venue {
  venue_id: number;
  venue_name: string;
  show_count: number;
}

export default function VenuesPage() {
  const router = useRouter();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'shows_desc' | 'shows_asc' | 'name_asc' | 'name_desc'>('shows_desc');

  useEffect(() => {
    fetchVenues();
  }, []);

  const fetchVenues = async () => {
    try {
      const response = await api.get('/dashboard/venues');
      setVenues(response.data.venues || []);
    } catch (error) {
      console.error('Failed to fetch venues:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredVenues = () => {
    let result = venues;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(venue =>
        venue.venue_name.toLowerCase().includes(q)
      );
    }

    result = [...result].sort((a, b) => {
      switch (sortBy) {
        case 'shows_asc':
          return a.show_count - b.show_count;
        case 'name_asc':
          return a.venue_name.localeCompare(b.venue_name);
        case 'name_desc':
          return b.venue_name.localeCompare(a.venue_name);
        case 'shows_desc':
        default:
          return b.show_count - a.show_count;
      }
    });

    return result;
  };

  const filteredVenues = getFilteredVenues();

  const handleVenueClick = (venueId: number) => {
    router.push(`/shows?venue_id=${venueId}`);
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
            <h1 className="text-3xl font-bold text-primary">My Venues</h1>
            <p className="text-secondary mt-2">
              {filteredVenues.length !== venues.length
                ? `${filteredVenues.length} of ${venues.length} venues`
                : `${venues.length} venues visited`}
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
                placeholder="Search venues..."
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

          {/* Venues Grid */}
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-secondary rounded-xl p-6 animate-pulse">
                  <div className="h-6 bg-tertiary rounded w-3/4 mb-2"></div>
                  <div className="h-4 bg-tertiary rounded w-1/2"></div>
                </div>
              ))}
            </div>
          ) : filteredVenues.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredVenues.map((venue) => (
                <button
                  key={venue.venue_id}
                  onClick={() => handleVenueClick(venue.venue_id)}
                  className="bg-secondary rounded-xl p-6 text-left hover:bg-tertiary transition-all hover:scale-[1.02] active:scale-[0.98]"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-tertiary flex items-center justify-center">
                      <svg className="w-6 h-6 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-primary truncate">{venue.venue_name}</h3>
                      <p className="text-sm text-secondary">{venue.show_count} {venue.show_count === 1 ? 'show' : 'shows'}</p>
                    </div>
                    <svg className="w-5 h-5 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="bg-secondary rounded-xl p-12 text-center">
              <svg className="w-16 h-16 text-muted mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {venues.length > 0 ? (
                <>
                  <h3 className="text-xl font-semibold text-primary mb-2">No venues found</h3>
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
                  <h3 className="text-xl font-semibold text-primary mb-2">No venues yet</h3>
                  <p className="text-secondary mb-4">Start adding shows to see your venues here.</p>
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
        </main>

        <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      </div>
    </ProtectedRoute>
  );
}
