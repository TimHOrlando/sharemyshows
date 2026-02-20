'use client';

import { useState } from 'react';
import { useTheme, ThemeName, ThemeColors } from '@/contexts/ThemeContext';

export default function ThemeSwitcher() {
  const { theme, setTheme, themes, customColors, applyCustomTheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const [showCustomizer, setShowCustomizer] = useState(false);
  const [editingColors, setEditingColors] = useState<ThemeColors>(customColors);

  const handleSaveCustomTheme = () => {
    applyCustomTheme(editingColors);
    setShowCustomizer(false);
  };

  const updateColor = (key: keyof ThemeColors, value: string) => {
    setEditingColors(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-full bg-tertiary hover:bg-hover transition-colors text-primary text-sm font-medium"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
        </svg>
        <span className="hidden sm:inline">Theme</span>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => {
              setIsOpen(false);
              setShowCustomizer(false);
            }}
          />
          
          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-72 bg-elevated rounded-xl shadow-theme-lg border border-theme z-50 overflow-hidden">
            {!showCustomizer ? (
              <>
                <div className="p-3 border-b border-theme">
                  <h3 className="text-sm font-semibold text-primary">Choose Theme</h3>
                </div>
                <div className="p-2 space-y-1 max-h-80 overflow-y-auto">
                  {themes.map((t) => (
                    <button
                      key={t.name}
                      onClick={() => {
                        setTheme(t.name);
                        setIsOpen(false);
                      }}
                      className={`w-full flex items-center gap-3 p-3 rounded-lg transition-colors ${
                        theme === t.name 
                          ? 'bg-accent text-white' 
                          : 'hover:bg-hover text-primary'
                      }`}
                    >
                      <ThemePreview themeName={t.name} customColors={customColors} />
                      <div className="text-left flex-1">
                        <p className="text-sm font-medium">{t.label}</p>
                        <p className={`text-xs ${theme === t.name ? 'text-white/70' : 'text-secondary'}`}>
                          {t.description}
                        </p>
                      </div>
                      {theme === t.name && (
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </button>
                  ))}
                  
                  {/* Custom theme option */}
                  <button
                    onClick={() => {
                      if (theme === 'custom') {
                        setIsOpen(false);
                      } else {
                        setEditingColors(customColors);
                        setShowCustomizer(true);
                      }
                    }}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg transition-colors ${
                      theme === 'custom' 
                        ? 'bg-accent text-white' 
                        : 'hover:bg-hover text-primary'
                    }`}
                  >
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 flex items-center justify-center flex-shrink-0">
                      <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                    </div>
                    <div className="text-left flex-1">
                      <p className="text-sm font-medium">Custom Theme</p>
                      <p className={`text-xs ${theme === 'custom' ? 'text-white/70' : 'text-secondary'}`}>
                        Create your own colors
                      </p>
                    </div>
                    {theme === 'custom' ? (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    )}
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="p-3 border-b border-theme flex items-center gap-2">
                  <button
                    onClick={() => setShowCustomizer(false)}
                    className="p-1 rounded hover:bg-hover"
                  >
                    <svg className="w-5 h-5 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  <h3 className="text-sm font-semibold text-primary">Custom Theme</h3>
                </div>
                <div className="p-3 space-y-3 max-h-96 overflow-y-auto">
                  <ColorPicker label="Background" value={editingColors.bgPrimary} onChange={(v) => updateColor('bgPrimary', v)} />
                  <ColorPicker label="Cards" value={editingColors.bgCard} onChange={(v) => updateColor('bgCard', v)} />
                  <ColorPicker label="Hover" value={editingColors.bgHover} onChange={(v) => updateColor('bgHover', v)} />
                  <ColorPicker label="Text" value={editingColors.textPrimary} onChange={(v) => updateColor('textPrimary', v)} />
                  <ColorPicker label="Muted Text" value={editingColors.textMuted} onChange={(v) => updateColor('textMuted', v)} />
                  <ColorPicker label="Accent" value={editingColors.accentPrimary} onChange={(v) => updateColor('accentPrimary', v)} />
                  <ColorPicker label="Border" value={editingColors.borderPrimary} onChange={(v) => updateColor('borderPrimary', v)} />
                </div>
                <div className="p-3 border-t border-theme">
                  <button
                    onClick={handleSaveCustomTheme}
                    className="w-full py-2 px-4 rounded-lg font-medium text-white transition-colors"
                    style={{ backgroundColor: editingColors.accentPrimary }}
                  >
                    Apply Custom Theme
                  </button>
                </div>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function ColorPicker({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-secondary">{label}</span>
      <div className="flex items-center gap-2">
        <input
          type="color"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-8 h-8 rounded cursor-pointer border-0 bg-transparent"
        />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-20 px-2 py-1 text-xs bg-tertiary text-primary rounded border border-theme font-mono"
        />
      </div>
    </div>
  );
}

function ThemePreview({ themeName, customColors }: { themeName: ThemeName; customColors: ThemeColors }) {
  const colors: Record<ThemeName, { bg: string; accent: string }> = {
    forest: { bg: '#1b211a', accent: '#8bae66' },
    sage: { bg: '#1e2721', accent: '#9db99a' },
    dark: { bg: '#121212', accent: '#9333ea' },
    light: { bg: '#ffffff', accent: '#9333ea' },
    midnight: { bg: '#0f172a', accent: '#6366f1' },
    concert: { bg: '#18181b', accent: '#dc2626' },
    purple: { bg: '#1a1625', accent: '#a78bfa' },
    custom: { bg: customColors.bgPrimary, accent: customColors.accentPrimary },
  };

  const { bg, accent } = colors[themeName];

  return (
    <div 
      className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
      style={{ backgroundColor: bg, border: '2px solid ' + accent }}
    >
      <div 
        className="w-3 h-3 rounded-full"
        style={{ backgroundColor: accent }}
      />
    </div>
  );
}

