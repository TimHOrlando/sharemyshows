'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface Friend {
  id: number;
  username: string;
}

interface LocationSharePickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (selectedIds: number[] | null) => void;
  initialSelection: number[] | null; // null = all friends
  showId?: number;
}

export default function LocationSharePickerModal({
  isOpen,
  onClose,
  onConfirm,
  initialSelection,
  showId,
}: LocationSharePickerModalProps) {
  const [friends, setFriends] = useState<Friend[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [shareAll, setShareAll] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isOpen) return;

    const fetchFriends = async () => {
      setLoading(true);
      try {
        if (showId) {
          // Fetch only friends who are at this show
          const response = await api.get(`/shows/${showId}/friends-at-show`);
          setFriends(response.data.friends || []);
        } else {
          // Fallback: fetch all accepted friends
          const response = await api.get('/friends');
          const accepted = (response.data.friends || [])
            .filter((f: { status: string }) => f.status === 'accepted')
            .map((f: { friend: { id: number; username: string } }) => ({
              id: f.friend.id,
              username: f.friend.username,
            }));
          setFriends(accepted);
        }
      } catch (error) {
        console.error('Failed to fetch friends:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchFriends();
  }, [isOpen, showId]);

  // Initialize selection state when friends load or initialSelection changes
  useEffect(() => {
    if (!isOpen || friends.length === 0) return;

    if (initialSelection === null) {
      setShareAll(true);
      setSelected(new Set(friends.map(f => f.id)));
    } else {
      setShareAll(false);
      setSelected(new Set(initialSelection));
    }
  }, [isOpen, friends, initialSelection]);

  const toggleFriend = (id: number) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
    setShareAll(false);
  };

  const toggleShareAll = () => {
    if (shareAll) {
      // Switching from all to selective — keep all selected so user can deselect
      setShareAll(false);
    } else {
      setShareAll(true);
      setSelected(new Set(friends.map(f => f.id)));
    }
  };

  const handleConfirm = () => {
    if (shareAll) {
      onConfirm(null);
    } else {
      onConfirm(Array.from(selected));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-secondary rounded-xl w-full max-w-md mx-4 max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-theme">
          <h2 className="text-lg font-bold text-primary">Share Location With</h2>
          <button onClick={onClose} className="p-1 text-muted hover:text-primary transition-colors">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Share with All toggle */}
        <div className="px-4 py-3 border-b border-theme">
          <button
            onClick={toggleShareAll}
            className="w-full flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center">
                <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <span className="text-primary font-medium">{showId ? 'All Friends Here' : 'All Friends'}</span>
            </div>
            <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
              shareAll ? 'border-accent bg-accent' : 'border-muted'
            }`}>
              {shareAll && (
                <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              )}
            </div>
          </button>
        </div>

        {/* Friend list */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-accent"></div>
            </div>
          ) : friends.length === 0 ? (
            <div className="px-4 py-8 text-center">
              <p className="text-sm text-muted">
                {showId ? 'No friends at this show yet' : 'No friends yet'}
              </p>
              {showId && (
                <p className="text-xs text-muted mt-2">
                  Your location will be shared with friends when they arrive
                </p>
              )}
            </div>
          ) : (
            friends.map((friend) => (
              <button
                key={friend.id}
                onClick={() => toggleFriend(friend.id)}
                className="w-full flex items-center justify-between px-4 py-3 border-b border-theme last:border-b-0 hover:bg-tertiary transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center">
                    <span className="text-sm font-bold text-accent">
                      {friend.username.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <span className="text-primary text-sm">{friend.username}</span>
                </div>
                <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                  selected.has(friend.id) ? 'border-accent bg-accent' : 'border-muted'
                }`}>
                  {selected.has(friend.id) && (
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
              </button>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-theme">
          <button
            onClick={handleConfirm}
            disabled={!shareAll && selected.size === 0}
            className="w-full px-4 py-2.5 bg-accent text-white rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {shareAll
              ? (friends.length === 0 && showId ? 'Share with All Friends' : (showId ? 'Share with All Friends Here' : 'Share with All Friends'))
              : selected.size === 0
                ? 'Select Friends'
                : `Share with ${selected.size} Friend${selected.size !== 1 ? 's' : ''}`}
          </button>
        </div>
      </div>
    </div>
  );
}
