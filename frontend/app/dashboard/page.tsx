'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import Navbar from '@/components/Navbar';
import SettingsModal from '@/components/SettingsModal';
import AddShowModal from '@/components/AddShowModal';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';

interface DashboardStats {
  total_shows: number;
  total_artists: number;
  total_venues: number;
  total_photos: number;
  total_audio: number;
  total_videos: number;
  total_comments: number;
}

interface Show {
  id: number;
  date: string;
  notes?: string;
  rating?: number;
  artist?: { id: number; name: string };
  venue?: { id: number; name: string; city?: string; state?: string };
}

interface ArtistStat {
  artist_id: number;
  artist_name: string;
  show_count: number;
}

interface VenueStat {
  venue_id: number;
  venue_name: string;
  show_count: number;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isAddShowOpen, setIsAddShowOpen] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [topArtists, setTopArtists] = useState<ArtistStat[]>([]);
  const [topVenues, setTopVenues] = useState<VenueStat[]>([]);
  const [upcomingShows, setUpcomingShows] = useState<Show[]>([]);
  const [recentShows, setRecentShows] = useState<Show[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, artistsRes, venuesRes, upcomingRes, recentRes] = await Promise.all([
        api.get('/dashboard/stats'),
        api.get('/dashboard/artists'),
        api.get('/dashboard/venues'),
        api.get('/shows', { params: { filter: 'upcoming', limit: 5 } }),
        api.get('/shows', { params: { filter: 'past', limit: 5 } }),
      ]);

      setStats(statsRes.data);
      setTopArtists(artistsRes.data.artists?.slice(0, 5) || []);
      setTopVenues(venuesRes.data.venues?.slice(0, 5) || []);
      setUpcomingShows(upcomingRes.data || []);
      setRecentShows(recentRes.data || []);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString + (dateString.length === 10 ? 'T12:00:00' : ''));
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const handleShowAdded = () => {
    fetchDashboardData();
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-primary">
        <Navbar onOpenSettings={() => setIsSettingsOpen(true)} />

        <main className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          {/* Welcome + Quick Actions - TOP PRIORITY */}
          <div className="mb-6">
            <h1 className="text-2xl sm:text-3xl font-bold text-primary mb-2">
              Welcome back, {user?.username}!
            </h1>
            <p className="text-secondary mb-6">
              Document and share your concert experiences.
            </p>

            {/* Quick Actions - Large Touch Targets */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                onClick={() => setIsAddShowOpen(true)}
                className="flex items-center justify-center gap-3 px-6 py-4 bg-accent rounded-xl text-white font-semibold text-lg touch-target transition-all hover:scale-[1.02] active:scale-[0.98]"
                style={{ backgroundColor: 'var(--accent-primary)' }}
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Show
              </button>
              
              <button
                onClick={() => router.push('/shows')}
                className="flex items-center justify-center gap-3 px-6 py-4 bg-tertiary rounded-xl text-primary font-semibold text-lg touch-target transition-all hover:bg-hover active:scale-[0.98]"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
                </svg>
                My Shows
              </button>

              <button
                onClick={() => router.push('/friends')}
                className="flex items-center justify-center gap-3 px-6 py-4 bg-tertiary rounded-xl text-primary font-semibold text-lg touch-target transition-all hover:bg-hover active:scale-[0.98]"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                Find Friends
              </button>
            </div>
          </div>

          {/* Stats Bar */}
          {loading ? (
            <div className="bg-secondary rounded-xl p-4 mb-6">
              <div className="grid grid-cols-3 sm:grid-cols-5 gap-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="animate-pulse">
                    <div className="h-4 bg-tertiary rounded w-1/2 mb-2"></div>
                    <div className="h-8 bg-tertiary rounded w-1/3"></div>
                  </div>
                ))}
              </div>
            </div>
          ) : stats ? (
            <div className="bg-secondary rounded-xl p-4 mb-6">
              <div className="grid grid-cols-3 sm:grid-cols-5 gap-4">
                <StatItem type="shows" label="Shows" value={stats.total_shows} onClick={() => router.push('/shows')} />
                <StatItem type="artists" label="Artists" value={stats.total_artists} onClick={() => router.push('/artists')} />
                <StatItem type="venues" label="Venues" value={stats.total_venues} onClick={() => router.push('/venues')} />
                <StatItem type="photos" label="Photos" value={stats.total_photos} onClick={() => router.push('/photos')} />
                <StatItem type="comments" label="Comments" value={stats.total_comments} onClick={() => router.push('/shows')} />
              </div>
            </div>
          ) : null}

          {/* Upcoming & Recent Shows */}
          {!loading && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Upcoming Shows */}
              <div className="bg-secondary rounded-xl overflow-hidden">
                <div className="px-5 py-4 border-b border-theme flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-primary">Upcoming Shows</h2>
                  {upcomingShows.length > 0 && (
                    <button
                      onClick={() => router.push('/shows?filter=upcoming')}
                      className="text-sm text-accent hover:opacity-80 transition-opacity"
                    >
                      View all
                    </button>
                  )}
                </div>
                <div className="p-4">
                  {upcomingShows.length > 0 ? (
                    <ul className="space-y-2">
                      {upcomingShows.map((show) => (
                        <li
                          key={show.id}
                          onClick={() => router.push(`/shows/${show.id}`)}
                          className="flex justify-between items-center p-3 rounded-lg hover:bg-tertiary transition-colors cursor-pointer"
                        >
                          <div className="min-w-0 flex-1">
                            <p className="font-medium text-primary truncate">{show.artist?.name || 'Unknown Artist'}</p>
                            <p className="text-sm text-secondary truncate">{show.venue?.name || 'Unknown Venue'}</p>
                          </div>
                          <div className="flex items-center gap-2 ml-3 flex-shrink-0">
                            <span className="text-sm text-accent font-medium">{formatDate(show.date)}</span>
                            <svg className="w-4 h-4 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-secondary text-center py-6">No upcoming shows. Add one!</p>
                  )}
                </div>
              </div>

              {/* Recent Shows */}
              <div className="bg-secondary rounded-xl overflow-hidden">
                <div className="px-5 py-4 border-b border-theme flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-primary">Recent Shows</h2>
                  {recentShows.length > 0 && (
                    <button
                      onClick={() => router.push('/shows?filter=past')}
                      className="text-sm text-accent hover:opacity-80 transition-opacity"
                    >
                      View all
                    </button>
                  )}
                </div>
                <div className="p-4">
                  {recentShows.length > 0 ? (
                    <ul className="space-y-2">
                      {recentShows.map((show) => (
                        <li
                          key={show.id}
                          onClick={() => router.push(`/shows/${show.id}`)}
                          className="flex justify-between items-center p-3 rounded-lg hover:bg-tertiary transition-colors cursor-pointer"
                        >
                          <div className="min-w-0 flex-1">
                            <p className="font-medium text-primary truncate">{show.artist?.name || 'Unknown Artist'}</p>
                            <p className="text-sm text-secondary truncate">{show.venue?.name || 'Unknown Venue'}</p>
                          </div>
                          <div className="flex items-center gap-2 ml-3 flex-shrink-0">
                            <span className="text-sm text-muted">{formatDate(show.date)}</span>
                            {show.rating && (
                              <div className="flex">
                                {[...Array(5)].map((_, i) => (
                                  <svg key={i} className={`w-3 h-3 ${i < show.rating! ? 'text-accent fill-current' : 'text-muted'}`} viewBox="0 0 20 20">
                                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                  </svg>
                                ))}
                              </div>
                            )}
                            <svg className="w-4 h-4 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-secondary text-center py-6">No past shows yet. Add your first show!</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Two Column Layout for Artists/Venues */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Top Artists */}
            <div className="bg-secondary rounded-xl overflow-hidden">
              <div className="px-5 py-4 border-b border-theme">
                <h2 className="text-lg font-semibold text-primary">Top Artists</h2>
              </div>
              <div className="p-4">
                {topArtists.length > 0 ? (
                  <ul className="space-y-2">
                    {topArtists.map((artist, index) => (
                      <li
                        key={artist.artist_id}
                        onClick={() => router.push(`/shows?artist_id=${artist.artist_id}`)}
                        className="flex justify-between items-center p-3 rounded-lg hover:bg-tertiary transition-colors cursor-pointer"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-medium text-muted w-6">#{index + 1}</span>
                          <span className="font-medium text-primary">{artist.artist_name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-secondary">{artist.show_count} {artist.show_count === 1 ? 'show' : 'shows'}</span>
                          <svg className="w-4 h-4 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-secondary text-center py-6">No artists yet. Add your first show!</p>
                )}
              </div>
            </div>

            {/* Top Venues */}
            <div className="bg-secondary rounded-xl overflow-hidden">
              <div className="px-5 py-4 border-b border-theme">
                <h2 className="text-lg font-semibold text-primary">Top Venues</h2>
              </div>
              <div className="p-4">
                {topVenues.length > 0 ? (
                  <ul className="space-y-2">
                    {topVenues.map((venue, index) => (
                      <li
                        key={venue.venue_id}
                        onClick={() => router.push(`/shows?venue_id=${venue.venue_id}`)}
                        className="flex justify-between items-center p-3 rounded-lg hover:bg-tertiary transition-colors cursor-pointer"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-medium text-muted w-6">#{index + 1}</span>
                          <span className="font-medium text-primary">{venue.venue_name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-secondary">{venue.show_count} {venue.show_count === 1 ? 'show' : 'shows'}</span>
                          <svg className="w-4 h-4 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-secondary text-center py-6">No venues yet. Add your first show!</p>
                )}
              </div>
            </div>
          </div>
        </main>

        {/* Modals */}
        <SettingsModal
          isOpen={isSettingsOpen}
          onClose={() => setIsSettingsOpen(false)}
        />
        <AddShowModal
          isOpen={isAddShowOpen}
          onClose={() => setIsAddShowOpen(false)}
          onSuccess={handleShowAdded}
        />
      </div>
    </ProtectedRoute>
  );
}

function StatItem({ type, label, value, onClick }: { type: 'shows' | 'artists' | 'venues' | 'photos' | 'comments'; label: string; value: number; onClick: () => void }) {
  const icons = {
    shows: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
      </svg>
    ),
    artists: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
    ),
    venues: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
    photos: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
    comments: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
      </svg>
    ),
  };

  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 p-3 rounded-xl hover:bg-tertiary transition-all cursor-pointer text-left w-full group"
    >
      <div className="text-accent group-hover:scale-110 transition-transform">
        {icons[type]}
      </div>
      <div>
        <p className="text-sm text-secondary">{label}</p>
        <p className="text-2xl font-bold text-primary">{value}</p>
      </div>
    </button>
  );
}







