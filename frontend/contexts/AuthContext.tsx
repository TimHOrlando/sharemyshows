'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '@/lib/types';
import { authService } from '@/lib/auth';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (login: string, password: string) => Promise<{ requiresMFA: boolean; message?: string }>;
  register: (username: string, email: string, password: string, enableMFA?: boolean) => Promise<{ requiresMFA: boolean; message?: string }>;
  verifyMFA: (email: string, code: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Load user on mount
  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      if (authService.isAuthenticated()) {
        const userData = await authService.getProfile();
        setUser(userData);
      }
    } catch (error) {
      console.error('Failed to load user:', error);
      // Clear invalid token
      localStorage.removeItem('access_token');
    } finally {
      setLoading(false);
    }
  };

  const register = async (username: string, email: string, password: string, enableMFA?: boolean) => {
    const response = await authService.register({
      username,
      email,
      password,
      enable_mfa: enableMFA,
    });

    if (response.requires_mfa || response.mfa_required) {
      return { requiresMFA: true, message: response.message };
    }

    if (response.user) {
      setUser(response.user);
    }

    return { requiresMFA: false, message: response.message };
  };

  const login = async (login: string, password: string) => {
    const response = await authService.login({ login, password });

    if (response.requires_mfa || response.mfa_required) {
      return { requiresMFA: true, message: response.message };
    }

    if (response.user) {
      setUser(response.user);
    }

    return { requiresMFA: false, message: response.message };
  };

  const verifyMFA = async (email: string, code: string) => {
    const response = await authService.verifyMFA({ email, code });

    if (response.user) {
      setUser(response.user);
    }
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
  };

  const refreshUser = async () => {
    await loadUser();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        verifyMFA,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
