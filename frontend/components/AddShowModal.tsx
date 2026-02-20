'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';


interface AddShowModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (showId?: number) => void;
}

interface VenueSearchResult {
  place_id: string;
  name: string;
  formatted_address: string;
  city?: string;
  state?: string;
  country?: string;
}

interface ArtistSearchResult {
  mbid: string;
  name: string;
  sort_name: string;
}

export default function AddShowModal({ isOpen, onClose, onSuccess }: AddShowModalProps) {
  const [step, setStep] = useState<'venue' | 'artist' | 'details'>('venue');

  // Venue search
  const [venueQuery, setVenueQuery] = useState('');
  const [venueResults, setVenueResults] = useState<VenueSearchResult[]>([]);
  const [searchingVenues, setSearchingVenues] = useState(false);
  const [selectedVenue, setSelectedVenue] = useState<VenueSearchResult | null>(null);

  // Artist search
  const [artistQuery, setArtistQuery] = useState('');
  const [artistResults, setArtistResults] = useState<ArtistSearchResult[]>([]);
  const [searchingArtists, setSearchingArtists] = useState(false);
  const [selectedArtist, setSelectedArtist] = useState<ArtistSearchResult | null>(null);

  // Show details
  const [showDate, setShowDate] = useState('');
  const [notes, setNotes] = useState('');
  const [rating, setRating] = useState<number | ''>('');

  // Form state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (venueQuery.length >= 2) {
      const timer = setTimeout(() => searchVenues(), 500);
      return () => clearTimeout(timer);
    } else {
      setVenueResults([]);
    }
  }, [venueQuery]);

  useEffect(() => {
    if (artistQuery.length >= 2) {
      const timer = setTimeout(() => searchArtists(), 500);
      return () => clearTimeout(timer);
    } else {
      setArtistResults([]);
    }
  }, [artistQuery]);

  const searchVenues = async () => {
    try {
      setSearchingVenues(true);
      setError(''); // Clear any previous errors
      const response = await api.get(`/external/venues/search`, {
        params: { query: venueQuery },
      });
      setVenueResults(response.data.venues || []);
    } catch (err) {
      console.error('Venue search failed:', err);
      const errorMsg = (err as { response?: { data?: { message?: string; error?: string } } }).response?.data?.message || (err as { response?: { data?: { message?: string; error?: string } } }).response?.data?.error || 'Failed to search venues. Please try again.';
      setError(errorMsg);
      setVenueResults([]);
    } finally {
      setSearchingVenues(false);
    }
  };

  const searchArtists = async () => {
    try {
      setSearchingArtists(true);
      setError(''); // Clear any previous errors
      const response = await api.get(`/external/artists/search`, {
        params: { query: artistQuery },
      });
      setArtistResults(response.data.artists || []);
    } catch (err) {
      console.error('Artist search failed:', err);
      const errorMsg = (err as { response?: { data?: { message?: string; error?: string } } }).response?.data?.message || (err as { response?: { data?: { message?: string; error?: string } } }).response?.data?.error || 'Failed to search artists. Please try again.';
      setError(errorMsg);
      setArtistResults([]);
    } finally {
      setSearchingArtists(false);
    }
  };

  const handleVenueSelect = async (venue: VenueSearchResult) => {
    try {
      // Fetch venue details to get city, state, country
      const response = await api.get(`/external/venues/details/${venue.place_id}`, {
      });

      const venueDetails = {
        ...venue,
        city: response.data.city || '',
        state: response.data.state || '',
        country: response.data.country || ''
      };

      setSelectedVenue(venueDetails);
      setStep('artist');
    } catch (err) {
      console.error('Failed to fetch venue details:', err);
      // Still allow selection with basic info
      setSelectedVenue(venue);
      setStep('artist');
    }
  };

  const handleArtistSelect = (artist: ArtistSearchResult) => {
    setSelectedArtist(artist);
    setStep('details');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedVenue || !selectedArtist || !showDate) {
      setError('Please complete all required fields');
      return;
    }

    try {
      setSubmitting(true);
      setError('');

      const response = await api.post(`/shows`,
        {
          artist_name: selectedArtist.name,
          artist_mbid: selectedArtist.mbid || undefined,
          venue_name: selectedVenue.name,
          date: showDate,
          city: selectedVenue.city || '',
          state: selectedVenue.state || '',
          country: selectedVenue.country || '',
          notes: notes,
          rating: rating || null
        },
      );

      const showId = response.data.id;

      // Auto-populate setlist for past shows (fire-and-forget)
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const showDateObj = new Date(showDate + 'T00:00:00');
      if (showDateObj < today && selectedArtist.mbid) {
        api.post(`/shows/${showId}/auto-setlist`, {
          mbid: selectedArtist.mbid
        }).catch(() => {
          // Silently ignore - best-effort
        });
      }

      // Reset form
      resetForm();
      onSuccess?.(showId);
      onClose();
    } catch (err) {
      setError((err as { response?: { data?: { error?: string } } }).response?.data?.error || 'Failed to create show');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setStep('venue');
    setVenueQuery('');
    setVenueResults([]);
    setSelectedVenue(null);
    setArtistQuery('');
    setArtistResults([]);
    setSelectedArtist(null);
    setShowDate('');
    setNotes('');
    setRating('');
    setError('');
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-elevated bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
      <div className="relative bg-card rounded-lg shadow-theme-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-card border-b border-theme px-6 py-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-primary">Add Show</h2>
          <button
            onClick={handleClose}
            className="text-muted hover:text-muted"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Progress Steps */}
        <div className="px-6 py-4 bg-secondary border-b border-theme">
          <div className="flex items-center justify-center space-x-2">
            <StepIndicator active={step === 'venue'} completed={selectedVenue !== null} label="1" />
            <div className={`h-0.5 w-16 ${selectedVenue ? 'bg-accent' : 'bg-tertiary'}`} />
            <StepIndicator active={step === 'artist'} completed={selectedArtist !== null} label="2" />
            <div className={`h-0.5 w-16 ${selectedArtist ? 'bg-accent' : 'bg-tertiary'}`} />
            <StepIndicator active={step === 'details'} completed={false} label="3" />
          </div>
          <div className="flex justify-center mt-2 text-sm text-secondary">
            {step === 'venue' && 'Select Venue'}
            {step === 'artist' && 'Select Artist'}
            {step === 'details' && 'Show Details'}
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-6">
          {error && (
            <div className="mb-4 bg-red-500/20 border border-red-500/50 p-4 rounded">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          {/* Step 1: Venue Search */}
          {step === 'venue' && (
            <div>
              <label className="block text-sm font-medium text-secondary mb-2">
                Search for a venue
              </label>
              <input
                type="text"
                value={venueQuery}
                onChange={(e) => setVenueQuery(e.target.value)}
                placeholder="Enter venue name..."
                className="w-full px-4 py-2 border border-theme rounded-md bg-secondary text-primary placeholder:text-muted focus:ring-2 focus:ring-accent focus:border-accent focus:outline-none"
                autoFocus
              />

              {searchingVenues && (
                <p className="mt-2 text-sm text-muted">Searching...</p>
              )}

              <div className="mt-4 space-y-2 max-h-96 overflow-y-auto">
                {venueResults.map((venue) => (
                  <button
                    key={venue.place_id}
                    onClick={() => handleVenueSelect(venue)}
                    className="w-full text-left p-4 border border-theme rounded-lg hover:border-accent hover:bg-hover bg-secondary transition-colors"
                  >
                    <h3 className="font-medium text-primary">{venue.name}</h3>
                    <p className="text-sm text-muted">{venue.formatted_address}</p>
                  </button>
                ))}
              </div>

              {selectedVenue && (
                <div className="mt-4 p-4 bg-tertiary border border-accent rounded-lg">
                  <p className="text-sm text-accent font-medium">Selected:</p>
                  <p className="text-primary font-semibold">{selectedVenue.name}</p>
                  <p className="text-sm text-accent">{selectedVenue.formatted_address}</p>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Artist Search */}
          {step === 'artist' && (
            <div>
              <button
                onClick={() => setStep('venue')}
                className="mb-4 text-sm text-accent hover:text-accent flex items-center"
              >
                <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Change venue
              </button>

              <label className="block text-sm font-medium text-secondary mb-2">
                Search for an artist
              </label>
              <input
                type="text"
                value={artistQuery}
                onChange={(e) => setArtistQuery(e.target.value)}
                placeholder="Enter artist name..."
                className="w-full px-4 py-2 border border-theme rounded-md bg-secondary text-primary placeholder:text-muted focus:ring-2 focus:ring-accent focus:border-accent focus:outline-none"
                autoFocus
              />

              {searchingArtists && (
                <p className="mt-2 text-sm text-muted">Searching...</p>
              )}

              <div className="mt-4 space-y-2 max-h-96 overflow-y-auto">
                {artistResults.map((artist) => (
                  <button
                    key={artist.mbid}
                    onClick={() => handleArtistSelect(artist)}
                    className="w-full text-left p-4 border border-theme rounded-lg hover:border-accent hover:bg-hover bg-secondary transition-colors"
                  >
                    <h3 className="font-medium text-primary">{artist.name}</h3>
                    {artist.sort_name !== artist.name && (
                      <p className="text-sm text-muted">{artist.sort_name}</p>
                    )}
                  </button>
                ))}
              </div>

              {selectedArtist && (
                <div className="mt-4 p-4 bg-tertiary border border-accent rounded-lg">
                  <p className="text-sm text-accent font-medium">Selected:</p>
                  <p className="text-primary font-semibold">{selectedArtist.name}</p>
                </div>
              )}
            </div>
          )}

          {/* Step 3: Show Details */}
          {step === 'details' && (
            <form onSubmit={handleSubmit}>
              <button
                type="button"
                onClick={() => setStep('artist')}
                className="mb-4 text-sm text-accent hover:text-accent flex items-center"
              >
                <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Change artist
              </button>

              <div className="space-y-4">
                {/* Summary */}
                <div className="p-4 bg-secondary rounded-lg">
                  <p className="text-sm text-secondary">Artist:</p>
                  <p className="font-semibold text-primary">{selectedArtist?.name}</p>
                  <p className="text-sm text-secondary mt-2">Venue:</p>
                  <p className="font-semibold text-primary">{selectedVenue?.name}</p>
                </div>

                {/* Show Date */}
                <div>
                  <label className="block text-sm font-medium text-secondary mb-2">
                    Show Date <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={showDate}
                    onChange={(e) => setShowDate(e.target.value)}
                    required
                    className="w-full px-4 py-2 border border-theme rounded-md bg-secondary text-primary placeholder:text-muted focus:ring-2 focus:ring-accent focus:border-accent focus:outline-none"
                  />
                </div>

                {/* Rating */}
                <div>
                  <label className="block text-sm font-medium text-secondary mb-2">
                    Rating (1-5)
                  </label>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setRating(star)}
                        className={`transition-colors ${
                          (rating !== '' && rating >= star) ? 'text-yellow-400' : 'text-gray-300'
                        } hover:text-yellow-400`}
                      >
                        <svg className="w-8 h-8" viewBox="0 0 20 20" fill="currentColor">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      </button>
                    ))}
                    {rating !== '' && (
                      <button
                        type="button"
                        onClick={() => setRating('')}
                        className="ml-2 text-sm text-muted hover:text-secondary"
                      >
                        Clear
                      </button>
                    )}
                  </div>
                </div>

                {/* Notes */}
                <div>
                  <label className="block text-sm font-medium text-secondary mb-2">
                    Notes
                  </label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={4}
                    placeholder="Add notes about the show..."
                    className="w-full px-4 py-2 border border-theme rounded-md bg-secondary text-primary placeholder:text-muted focus:ring-2 focus:ring-accent focus:border-accent focus:outline-none"
                  />
                </div>

                {/* Submit Button */}
                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={handleClose}
                    className="flex-1 px-4 py-2 border border-theme rounded-md text-secondary hover:bg-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting || !showDate}
                    className="flex-1 px-4 py-2 bg-accent text-white rounded-md hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {submitting ? 'Adding Show...' : 'Add Show'}
                  </button>
                </div>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

function StepIndicator({ active, completed, label }: { active: boolean; completed: boolean; label: string }) {
  return (
    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
      completed ? 'bg-accent text-white' :
      active ? 'bg-accent text-white' :
      'bg-tertiary text-secondary'
    }`}>
      {completed ? (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      ) : label}
    </div>
  );
}
