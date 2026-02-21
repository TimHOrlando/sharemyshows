'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type ThemeName = 'forest' | 'sage' | 'dark' | 'light' | 'midnight' | 'concert' | 'purple' | 'custom';

export interface ThemeColors {
  bgPrimary: string;
  bgSecondary: string;
  bgTertiary: string;
  bgCard: string;
  bgHover: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  accentPrimary: string;
  accentHover: string;
  borderPrimary: string;
}

export interface Theme {
  name: ThemeName;
  label: string;
  description: string;
}

export const defaultThemes: Theme[] = [
  { name: 'forest', label: 'Forest', description: 'Rich forest greens with cream (Default)' },
  { name: 'sage', label: 'Sage', description: 'Soft sage green tones' },
  { name: 'dark', label: 'Classic Dark', description: 'Dark theme with purple accents' },
  { name: 'midnight', label: 'Midnight Blue', description: 'Deep blue tones' },
  { name: 'concert', label: 'Concert Red', description: 'Bold red accents' },
  { name: 'purple', label: 'Purple Haze', description: 'Vibrant purple tones' },
  { name: 'light', label: 'Light', description: 'Light theme for daytime' },
];

const defaultCustomColors: ThemeColors = {
  bgPrimary: '#1b211a',
  bgSecondary: '#232b22',
  bgTertiary: '#2d372c',
  bgCard: '#232b22',
  bgHover: '#3a4639',
  textPrimary: '#ebd5ab',
  textSecondary: '#8bae66',
  textMuted: '#628141',
  accentPrimary: '#8bae66',
  accentHover: '#9fc07a',
  borderPrimary: '#2d372c',
};

interface ThemeContextType {
  theme: ThemeName;
  setTheme: (theme: ThemeName) => void;
  themes: Theme[];
  customColors: ThemeColors;
  setCustomColors: (colors: ThemeColors) => void;
  applyCustomTheme: (colors: ThemeColors) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeName>('forest');
  const [customColors, setCustomColorsState] = useState<ThemeColors>(defaultCustomColors);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem('sharemyshows-theme') as ThemeName;
    const savedCustomColors = localStorage.getItem('sharemyshows-custom-colors');
    
    if (savedCustomColors) {
      try {
        const colors = JSON.parse(savedCustomColors);
        setCustomColorsState(colors);
      } catch (e) {
        console.error('Failed to parse custom colors:', e);
      }
    }
    
    if (savedTheme && (defaultThemes.some(t => t.name === savedTheme) || savedTheme === 'custom')) {
      setThemeState(savedTheme);
      applyThemeToDOM(savedTheme, savedCustomColors ? JSON.parse(savedCustomColors) : defaultCustomColors);
    }
  }, []);

  const applyThemeToDOM = (themeName: ThemeName, colors?: ThemeColors) => {
    if (themeName === 'forest') {
      document.documentElement.removeAttribute('data-theme');
      removeCustomProperties();
    } else if (themeName === 'custom' && colors) {
      document.documentElement.setAttribute('data-theme', 'custom');
      applyCustomProperties(colors);
    } else {
      document.documentElement.setAttribute('data-theme', themeName);
      removeCustomProperties();
    }
  };

  const applyCustomProperties = (colors: ThemeColors) => {
    const root = document.documentElement;
    root.style.setProperty('--bg-primary', colors.bgPrimary);
    root.style.setProperty('--bg-secondary', colors.bgSecondary);
    root.style.setProperty('--bg-tertiary', colors.bgTertiary);
    root.style.setProperty('--bg-card', colors.bgCard);
    root.style.setProperty('--bg-hover', colors.bgHover);
    root.style.setProperty('--text-primary', colors.textPrimary);
    root.style.setProperty('--text-secondary', colors.textSecondary);
    root.style.setProperty('--text-muted', colors.textMuted);
    root.style.setProperty('--accent-primary', colors.accentPrimary);
    root.style.setProperty('--accent-hover', colors.accentHover);
    root.style.setProperty('--border-primary', colors.borderPrimary);
  };

  const removeCustomProperties = () => {
    const root = document.documentElement;
    const properties = [
      '--bg-primary', '--bg-secondary', '--bg-tertiary', '--bg-card', '--bg-hover',
      '--text-primary', '--text-secondary', '--text-muted',
      '--accent-primary', '--accent-hover', '--border-primary'
    ];
    properties.forEach(prop => root.style.removeProperty(prop));
  };

  const syncThemeToBackend = (themeName: ThemeName) => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api'}/auth/profile/theme`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ theme: themeName }),
    }).catch(() => {});
  };

  const setTheme = (newTheme: ThemeName) => {
    setThemeState(newTheme);
    localStorage.setItem('sharemyshows-theme', newTheme);
    applyThemeToDOM(newTheme, customColors);
    syncThemeToBackend(newTheme);
  };

  const setCustomColors = (colors: ThemeColors) => {
    setCustomColorsState(colors);
    localStorage.setItem('sharemyshows-custom-colors', JSON.stringify(colors));
  };

  const applyCustomTheme = (colors: ThemeColors) => {
    setCustomColors(colors);
    setThemeState('custom');
    localStorage.setItem('sharemyshows-theme', 'custom');
    document.documentElement.setAttribute('data-theme', 'custom');
    applyCustomProperties(colors);
  };

  if (!mounted) {
    return null;
  }

  return (
    <ThemeContext.Provider value={{ 
      theme, 
      setTheme, 
      themes: defaultThemes, 
      customColors, 
      setCustomColors,
      applyCustomTheme 
    }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
