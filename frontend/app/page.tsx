'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Redirect authenticated users to dashboard
    if (!loading && user) {
      router.push('/dashboard');
    }
  }, [user, loading, router]);

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-primary">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto"></div>
          <p className="mt-4 text-secondary">Loading...</p>
        </div>
      </div>
    );
  }

  // Show landing page for non-authenticated users
  return (
    <div className="min-h-screen bg-primary">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <div className="text-6xl mb-6">🎸</div>
          <h1 className="text-5xl md:text-6xl font-extrabold text-primary mb-6">
            ShareMyShows
          </h1>
          <p className="text-xl md:text-2xl text-accent mb-4">
            Document Your Concert Experiences
          </p>
          <p className="text-lg text-secondary mb-12 max-w-2xl mx-auto">
            Like Last.fm meets Instagram for live music. Share shows, upload media,
            connect with friends, and discover concerts together.
          </p>

          {/* CTA Buttons - Large Touch Targets */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              href="/register"
              className="w-full sm:w-auto px-10 py-4 rounded-full font-bold text-lg text-white transition-all hover:scale-105 active:scale-95 touch-target"
              style={{ backgroundColor: 'var(--accent-primary)' }}
            >
              Get Started
            </Link>
            <Link
              href="/login"
              className="w-full sm:w-auto px-10 py-4 bg-tertiary text-primary rounded-full font-bold text-lg hover:bg-hover transition-all hover:scale-105 active:scale-95 touch-target border border-theme"
            >
              Sign In
            </Link>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-card rounded-xl p-6 hover:bg-hover transition-colors">
            <div className="text-4xl mb-4">🎫</div>
            <h3 className="text-xl font-bold text-primary mb-2">Document Shows</h3>
            <p className="text-secondary">
              Keep track of every concert you attend with detailed information,
              setlists, and venue data.
            </p>
          </div>

          <div className="bg-card rounded-xl p-6 hover:bg-hover transition-colors">
            <div className="text-4xl mb-4">📸</div>
            <h3 className="text-xl font-bold text-primary mb-2">Upload Media</h3>
            <p className="text-secondary">
              Share photos, videos, and audio recordings from your favorite
              live music moments.
            </p>
          </div>

          <div className="bg-card rounded-xl p-6 hover:bg-hover transition-colors">
            <div className="text-4xl mb-4">👥</div>
            <h3 className="text-xl font-bold text-primary mb-2">Connect</h3>
            <p className="text-secondary">
              Find friends who share your music taste and discover new shows
              to attend together.
            </p>
          </div>
        </div>

        {/* Additional Features */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-secondary rounded-xl p-6 flex items-start gap-4">
            <div className="text-3xl">🎵</div>
            <div>
              <h3 className="text-lg font-bold text-primary mb-1">Auto-Setlists</h3>
              <p className="text-muted text-sm">
                Automatically import setlists from Setlist.fm for past shows
              </p>
            </div>
          </div>
          
          <div className="bg-secondary rounded-xl p-6 flex items-start gap-4">
            <div className="text-3xl">📍</div>
            <div>
              <h3 className="text-lg font-bold text-primary mb-1">Find Friends</h3>
              <p className="text-muted text-sm">
                Track and find your friends at live shows
              </p>
            </div>
          </div>
          
          <div className="bg-secondary rounded-xl p-6 flex items-start gap-4">
            <div className="text-3xl">🎤</div>
            <div>
              <h3 className="text-lg font-bold text-primary mb-1">Shazam Integration</h3>
              <p className="text-muted text-sm">
                Record audio clips and identify songs during live shows
              </p>
            </div>
          </div>
          
          <div className="bg-secondary rounded-xl p-6 flex items-start gap-4">
            <div className="text-3xl">📱</div>
            <div>
              <h3 className="text-lg font-bold text-primary mb-1">Dark Mode</h3>
              <p className="text-muted text-sm">
                Designed for dark venues - won&apos;t disturb others around you
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-16 text-center">
          <p className="text-muted text-sm">
            Powered by Google Places API and Setlist.fm
          </p>
        </div>
      </div>
    </div>
  );
}
