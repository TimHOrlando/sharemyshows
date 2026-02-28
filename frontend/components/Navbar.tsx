'use client';

import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '@/lib/api';

interface NavbarProps {
  onOpenSettings?: () => void;
}

interface NotificationItem {
  id: number;
  type: string;
  message: string;
  data: { show_id?: number; artist?: string; venue?: string; date?: string };
  from_user: { id: number; username: string } | null;
  read: boolean;
  created_at: string;
}

export default function Navbar({ onOpenSettings }: NavbarProps = {}) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [unreadDMs, setUnreadDMs] = useState(0);

  // Notification state
  const [unreadNotifications, setUnreadNotifications] = useState(0);
  const [notifDropdownOpen, setNotifDropdownOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loadingNotifs, setLoadingNotifs] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const [dmRes, notifRes] = await Promise.all([
        api.get('/dm/unread-count'),
        api.get('/notifications/unread-count'),
      ]);
      setUnreadDMs(dmRes.data.unread_count || 0);
      setUnreadNotifications(notifRes.data.unread_count || 0);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    if (!user) return;
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, [user, fetchUnreadCount]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setNotifDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const openNotifDropdown = async () => {
    if (notifDropdownOpen) {
      setNotifDropdownOpen(false);
      return;
    }
    setNotifDropdownOpen(true);
    setLoadingNotifs(true);
    try {
      const res = await api.get('/notifications?per_page=10');
      setNotifications(res.data.notifications || []);
    } catch {
      setNotifications([]);
    } finally {
      setLoadingNotifs(false);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.put('/notifications/mark-read');
      setUnreadNotifications(0);
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    } catch {
      // ignore
    }
  };

  const handleNotifClick = async (notif: NotificationItem) => {
    // Mark as read
    if (!notif.read) {
      try {
        await api.put(`/notifications/${notif.id}/read`);
        setNotifications(prev => prev.map(n => n.id === notif.id ? { ...n, read: true } : n));
        setUnreadNotifications(prev => Math.max(0, prev - 1));
      } catch {
        // ignore
      }
    }
    // Navigate
    if (notif.type === 'show_added' && notif.data.show_id) {
      setNotifDropdownOpen(false);
      router.push(`/shows/${notif.data.show_id}`);
    }
  };

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logout();
      router.push('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setIsLoggingOut(false);
    }
  };

  const isActive = (path: string) => pathname === path;

  const navLinks = [
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/shows', label: 'My Shows' },
    { href: '/feed', label: 'Feed' },
    { href: '/messages', label: 'Messages', badge: unreadDMs },
    { href: '/friends', label: 'Friends' },
  ];

  const formatTimeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  return (
    <nav className="bg-secondary border-b border-theme sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/dashboard" className="flex items-center gap-2">
              <svg className="w-7 h-7 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" /></svg>
              <h1 className="text-xl font-bold text-accent">ShareMyShows</h1>
            </Link>
          </div>

          {/* Desktop Nav */}
          {user && (
            <div className="hidden md:flex items-center space-x-1">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`relative px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                    isActive(link.href)
                      ? 'bg-accent text-white'
                      : 'text-secondary hover:text-primary hover:bg-hover'
                  }`}
                >
                  {link.label}
                  {link.badge && link.badge > 0 ? (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
                      {link.badge > 99 ? '99+' : link.badge}
                    </span>
                  ) : null}
                </Link>
              ))}
            </div>
          )}

          {/* Right side actions */}
          <div className="flex items-center gap-2">
            {user && (
              <>
                <span className="hidden sm:block text-sm text-secondary px-3">
                  {user.username}
                </span>

                {/* Notification Bell */}
                <div className="relative" ref={notifRef}>
                  <button
                    onClick={openNotifDropdown}
                    className="p-2 rounded-full text-secondary hover:text-primary hover:bg-hover transition-colors touch-target relative"
                    title="Notifications"
                  >
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                    {unreadNotifications > 0 && (
                      <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[10px] font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
                        {unreadNotifications > 99 ? '99+' : unreadNotifications}
                      </span>
                    )}
                  </button>

                  {/* Notification Dropdown */}
                  {notifDropdownOpen && (
                    <div className="fixed left-4 right-4 top-[4.5rem] sm:absolute sm:left-auto sm:right-0 sm:top-full sm:mt-2 sm:w-80 bg-secondary border border-theme rounded-xl shadow-lg overflow-hidden z-50">
                      <div className="px-4 py-3 border-b border-theme flex items-center justify-between">
                        <h3 className="font-medium text-primary text-sm">Notifications</h3>
                        {unreadNotifications > 0 && (
                          <button
                            onClick={handleMarkAllRead}
                            className="text-xs text-accent hover:underline"
                          >
                            Mark all read
                          </button>
                        )}
                      </div>
                      <div className="max-h-80 overflow-y-auto">
                        {loadingNotifs ? (
                          <div className="p-4 text-center text-sm text-muted">Loading...</div>
                        ) : notifications.length === 0 ? (
                          <div className="p-4 text-center text-sm text-muted">No notifications yet</div>
                        ) : (
                          notifications.map((notif) => (
                            <button
                              key={notif.id}
                              onClick={() => handleNotifClick(notif)}
                              className={`w-full text-left px-4 py-3 border-b border-theme last:border-b-0 hover:bg-hover transition-colors ${
                                !notif.read ? 'bg-accent/5' : ''
                              }`}
                            >
                              <div className="flex items-start gap-3">
                                <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                                  <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z" />
                                  </svg>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm text-primary leading-snug">{notif.message}</p>
                                  <p className="text-xs text-muted mt-1">{formatTimeAgo(notif.created_at)}</p>
                                </div>
                                {!notif.read && (
                                  <span className="w-2 h-2 rounded-full bg-accent flex-shrink-0 mt-2" />
                                )}
                              </div>
                            </button>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                </div>

                <button
                  onClick={onOpenSettings}
                  className="p-2 rounded-full text-secondary hover:text-primary hover:bg-hover transition-colors touch-target"
                  title="Settings"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </button>

                <button
                  onClick={handleLogout}
                  disabled={isLoggingOut}
                  className="p-2 rounded-full text-secondary hover:text-primary hover:bg-hover transition-colors touch-target disabled:opacity-50"
                  title="Logout"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                </button>

                {/* Mobile menu button */}
                <button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="md:hidden p-2 rounded-full text-secondary hover:text-primary hover:bg-hover transition-colors touch-target"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    {mobileMenuOpen ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    )}
                  </svg>
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && user && (
        <div className="md:hidden border-t border-theme bg-secondary">
          <div className="px-4 py-3 space-y-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium transition-colors ${
                  isActive(link.href)
                    ? 'bg-accent text-white'
                    : 'text-secondary hover:text-primary hover:bg-hover'
                }`}
              >
                {link.label}
                {link.badge && link.badge > 0 ? (
                  <span className="bg-red-500 text-white text-xs rounded-full px-2 py-0.5 ml-auto">
                    {link.badge > 99 ? '99+' : link.badge}
                  </span>
                ) : null}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}
