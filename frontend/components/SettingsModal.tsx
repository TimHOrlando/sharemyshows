'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { authService } from '@/lib/auth';
import { useTheme, ThemeName, ThemeColors } from '@/contexts/ThemeContext';

// Helper function to get theme colors
function getThemeColors(themeName: ThemeName, customColors: ThemeColors): ThemeColors {
  const themeColorMap: Record<string, ThemeColors> = {
    forest: {
      bgPrimary: '#1b211a', bgSecondary: '#232b22', bgTertiary: '#2d372c', bgCard: '#232b22',
      bgHover: '#3a4639', textPrimary: '#ebd5ab', textSecondary: '#8bae66', textMuted: '#628141',
      accentPrimary: '#8bae66', accentHover: '#9fc07a', borderPrimary: '#2d372c',
    },
    sage: {
      bgPrimary: '#1e2721', bgSecondary: '#2d3830', bgTertiary: '#3d4a40', bgCard: '#2d3830',
      bgHover: '#4a5d4e', textPrimary: '#e8efe9', textSecondary: '#a3b5a6', textMuted: '#7a8f7d',
      accentPrimary: '#9db99a', accentHover: '#b5cfb2', borderPrimary: '#3d4a40',
    },
    dark: {
      bgPrimary: '#121212', bgSecondary: '#181818', bgTertiary: '#282828', bgCard: '#242424',
      bgHover: '#2a2a2a', textPrimary: '#ffffff', textSecondary: '#b3b3b3', textMuted: '#6a6a6a',
      accentPrimary: '#9333ea', accentHover: '#a855f7', borderPrimary: '#282828',
    },
    light: {
      bgPrimary: '#ffffff', bgSecondary: '#f5f5f5', bgTertiary: '#e5e5e5', bgCard: '#ffffff',
      bgHover: '#f0f0f0', textPrimary: '#121212', textSecondary: '#535353', textMuted: '#9a9a9a',
      accentPrimary: '#628141', accentHover: '#8bae66', borderPrimary: '#e5e5e5',
    },
    midnight: {
      bgPrimary: '#0f172a', bgSecondary: '#1e293b', bgTertiary: '#334155', bgCard: '#1e293b',
      bgHover: '#334155', textPrimary: '#f8fafc', textSecondary: '#94a3b8', textMuted: '#64748b',
      accentPrimary: '#6366f1', accentHover: '#818cf8', borderPrimary: '#334155',
    },
    concert: {
      bgPrimary: '#18181b', bgSecondary: '#27272a', bgTertiary: '#3f3f46', bgCard: '#27272a',
      bgHover: '#3f3f46', textPrimary: '#fafafa', textSecondary: '#a1a1aa', textMuted: '#71717a',
      accentPrimary: '#dc2626', accentHover: '#ef4444', borderPrimary: '#3f3f46',
    },
    purple: {
      bgPrimary: '#1a1625', bgSecondary: '#251f33', bgTertiary: '#352d47', bgCard: '#251f33',
      bgHover: '#352d47', textPrimary: '#f5f3ff', textSecondary: '#c4b5fd', textMuted: '#8b5cf6',
      accentPrimary: '#a78bfa', accentHover: '#c4b5fd', borderPrimary: '#352d47',
    },
    custom: customColors,
  };
  return themeColorMap[themeName] || themeColorMap.forest;
}

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const { user, refreshUser } = useAuth();
  const { theme, setTheme, themes, customColors, applyCustomTheme } = useTheme();
  const [editingColors, setEditingColors] = useState<ThemeColors>(customColors);
  const [showPalette, setShowPalette] = useState(false);
  const [isEditingEmail, setIsEditingEmail] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [emailSuccess, setEmailSuccess] = useState('');
  const [isUpdatingEmail, setIsUpdatingEmail] = useState(false);
  const [showMFACodeInput, setShowMFACodeInput] = useState(false);
  const [mfaCode, setMfaCode] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  useEffect(() => {
    setEditingColors(getThemeColors(theme, customColors));
  }, [theme, customColors]);

  const handleEnableMFA = async () => {
    setIsLoading(true);
    setError('');
    try {
      await authService.enableMFA();
      setShowMFACodeInput(true);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to enable MFA';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyMFA = async () => {
    setIsLoading(true);
    setError('');
    try {
      await authService.verifyMFA(mfaCode);
      setSuccessMessage('MFA enabled successfully!');
      setShowMFACodeInput(false);
      setMfaCode('');
      await refreshUser();
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Invalid code';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisableMFA = async () => {
    setIsLoading(true);
    setError('');
    try {
      await authService.disableMFA();
      setSuccessMessage('MFA disabled successfully!');
      await refreshUser();
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to disable MFA';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      return;
    }

    setIsChangingPassword(true);
    try {
      await authService.changePassword(currentPassword, newPassword);
      setPasswordSuccess('Password changed successfully!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setShowPasswordForm(false);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to change password';
      setPasswordError(errorMessage);
    } finally {
      setIsChangingPassword(false);
    }
  };

  
  const handleUpdateEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    setEmailError('');
    setEmailSuccess('');

    if (!newEmail || !newEmail.includes('@')) {
      setEmailError('Please enter a valid email address');
      return;
    }

    setIsUpdatingEmail(true);
    try {
      await authService.updateEmail(newEmail);
      setEmailSuccess('Email updated successfully!');
      setIsEditingEmail(false);
      setNewEmail('');
      await refreshUser();
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update email';
      setEmailError(errorMessage);
    } finally {
      setIsUpdatingEmail(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="fixed inset-0 bg-black/60" onClick={onClose} />
        
        <div className="relative bg-primary rounded-2xl shadow-theme-lg w-full max-w-lg max-h-[90vh] overflow-y-auto border border-theme">
          <div className="sticky top-0 bg-primary border-b border-theme px-6 py-4 flex items-center justify-between z-10">
            <h2 className="text-xl font-bold text-primary">Settings</h2>
            <button onClick={onClose} className="p-2 rounded-full hover:bg-hover transition-colors text-secondary">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="p-6 space-y-6">
            {/* Theme Settings */}
            <div className="bg-secondary rounded-lg p-6">
              <h3 className="text-lg font-medium text-primary mb-4">Appearance</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-secondary">Theme</span>
                  <div className="relative">
                    <select
                      value={theme}
                      onChange={(e) => setTheme(e.target.value as ThemeName)}
                      className="appearance-none bg-tertiary text-primary px-4 py-2 pr-10 rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent cursor-pointer min-w-[180px]"
                    >
                      {themes.map((t) => (
                        <option key={t.name} value={t.name}>{t.label}</option>
                      ))}
                      <option value="custom">Custom Theme</option>
                    </select>
                    <svg className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>

                {/* Collapsible Color Palette */}
                <div className="mt-4 bg-tertiary rounded-lg overflow-hidden">
                  <button
                    onClick={() => setShowPalette(!showPalette)}
                    className="w-full px-4 py-3 flex items-center justify-between hover:bg-hover transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-primary">Color Palette</span>
                      {/* Horizontal color swatch preview */}
                      <div className="flex h-6 rounded overflow-hidden border border-theme-secondary">
                        <div className="w-4" style={{ backgroundColor: editingColors.bgPrimary }} title="Background" />
                        <div className="w-4" style={{ backgroundColor: editingColors.bgCard }} title="Cards" />
                        <div className="w-4" style={{ backgroundColor: editingColors.bgHover }} title="Hover" />
                        <div className="w-4" style={{ backgroundColor: editingColors.textPrimary }} title="Text" />
                        <div className="w-4" style={{ backgroundColor: editingColors.textMuted }} title="Muted" />
                        <div className="w-4" style={{ backgroundColor: editingColors.accentPrimary }} title="Accent" />
                        <div className="w-4" style={{ backgroundColor: editingColors.borderPrimary }} title="Border" />
                      </div>
                    </div>
                    <svg className={`h-5 w-5 text-muted transform transition-transform ${showPalette ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  
                  {showPalette && (
                    <div className="px-4 pb-4 space-y-3">
                      {theme !== 'custom' && <p className="text-xs text-muted pb-2">Select Custom Theme to edit colors</p>}
                      <ColorPicker label="Background" value={editingColors.bgPrimary} onChange={(v) => theme === 'custom' && setEditingColors(prev => ({ ...prev, bgPrimary: v }))} disabled={theme !== 'custom'} />
                      <ColorPicker label="Cards" value={editingColors.bgCard} onChange={(v) => theme === 'custom' && setEditingColors(prev => ({ ...prev, bgCard: v }))} disabled={theme !== 'custom'} />
                      <ColorPicker label="Hover" value={editingColors.bgHover} onChange={(v) => theme === 'custom' && setEditingColors(prev => ({ ...prev, bgHover: v }))} disabled={theme !== 'custom'} />
                      <ColorPicker label="Text" value={editingColors.textPrimary} onChange={(v) => theme === 'custom' && setEditingColors(prev => ({ ...prev, textPrimary: v }))} disabled={theme !== 'custom'} />
                      <ColorPicker label="Muted Text" value={editingColors.textMuted} onChange={(v) => theme === 'custom' && setEditingColors(prev => ({ ...prev, textMuted: v }))} disabled={theme !== 'custom'} />
                      <ColorPicker label="Accent" value={editingColors.accentPrimary} onChange={(v) => theme === 'custom' && setEditingColors(prev => ({ ...prev, accentPrimary: v }))} disabled={theme !== 'custom'} />
                      <ColorPicker label="Border" value={editingColors.borderPrimary} onChange={(v) => theme === 'custom' && setEditingColors(prev => ({ ...prev, borderPrimary: v }))} disabled={theme !== 'custom'} />
                      
                      {theme === 'custom' && (
                        <div className="flex gap-2 pt-2">
                          <button onClick={() => applyCustomTheme(editingColors)} className="w-full py-2 px-4 rounded-lg font-medium text-white transition-colors bg-accent hover:opacity-90">
                            Apply Changes
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Security Settings */}
            <div className="bg-secondary rounded-lg p-6">
              <h3 className="text-lg font-medium text-primary mb-4">Security</h3>
              {error && <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400 text-sm">{error}</div>}
              {successMessage && <div className="mb-4 p-3 bg-green-500/20 border border-green-500/50 rounded-lg text-green-400 text-sm">{successMessage}</div>}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-primary">Two-Factor Authentication</p>
                    <p className="text-xs text-muted">{user?.mfa_enabled ? 'Enabled' : 'Add an extra layer of security'}</p>
                  </div>
                  {user?.mfa_enabled ? (
                    <button onClick={handleDisableMFA} disabled={isLoading} className="px-4 py-2 text-sm font-medium text-red-400 bg-red-500/20 rounded-lg hover:bg-red-500/30 transition-colors disabled:opacity-50">
                      {isLoading ? 'Disabling...' : 'Disable'}
                    </button>
                  ) : (
                    <button onClick={handleEnableMFA} disabled={isLoading} className="px-4 py-2 text-sm font-medium text-white bg-accent rounded-lg hover:opacity-90 transition-colors disabled:opacity-50">
                      {isLoading ? 'Enabling...' : 'Enable'}
                    </button>
                  )}
                </div>
                {showMFACodeInput && (
                  <div className="mt-4 p-4 bg-tertiary rounded-lg">
                    <p className="text-sm text-secondary mb-3">Enter the code from your authenticator app:</p>
                    <div className="flex gap-2">
                      <input type="text" value={mfaCode} onChange={(e) => setMfaCode(e.target.value)} placeholder="000000" maxLength={6} className="flex-1 px-4 py-2 bg-secondary text-primary rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent" />
                      <button onClick={handleVerifyMFA} disabled={isLoading || mfaCode.length !== 6} className="px-4 py-2 text-sm font-medium text-white bg-accent rounded-lg hover:opacity-90 transition-colors disabled:opacity-50">Verify</button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Account Information */}
            <div className="bg-secondary rounded-lg p-6">
              <h3 className="text-lg font-medium text-primary mb-4">Account Information</h3>
              
              {emailError && <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400 text-sm">{emailError}</div>}
              {emailSuccess && <div className="mb-4 p-3 bg-green-500/20 border border-green-500/50 rounded-lg text-green-400 text-sm">{emailSuccess}</div>}
              
              <div className="space-y-4">
                <div>
                  <dt className="text-sm text-muted">Username</dt>
                  <dd className="mt-1 text-sm text-primary">{user?.username}</dd>
                </div>
                
                <div>
                  <dt className="text-sm text-muted mb-1">Email</dt>
                  {!isEditingEmail ? (
                    <dd className="flex items-center justify-between">
                      <span className="text-sm text-primary">{user?.email}</span>
                      <button
                        onClick={() => {
                          setNewEmail(user?.email || '');
                          setIsEditingEmail(true);
                          setEmailError('');
                          setEmailSuccess('');
                        }}
                        className="text-sm text-accent hover:underline"
                      >
                        Edit
                      </button>
                    </dd>
                  ) : (
                    <form onSubmit={handleUpdateEmail} className="space-y-3">
                      <input
                        type="email"
                        value={newEmail}
                        onChange={(e) => setNewEmail(e.target.value)}
                        placeholder="Enter new email"
                        className="w-full px-4 py-2 bg-tertiary text-primary rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent"
                        autoFocus
                      />
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            setIsEditingEmail(false);
                            setNewEmail('');
                            setEmailError('');
                          }}
                          className="flex-1 py-2 px-4 text-sm font-medium text-primary bg-hover rounded-lg hover:opacity-90 transition-colors"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={isUpdatingEmail}
                          className="flex-1 py-2 px-4 text-sm font-medium text-white bg-accent rounded-lg hover:opacity-90 transition-colors disabled:opacity-50"
                        >
                          {isUpdatingEmail ? 'Saving...' : 'Save'}
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              </div>
            </div>

            {/* Change Password */}
            <div className="bg-secondary rounded-lg overflow-hidden">
              <button onClick={() => setShowPasswordForm(!showPasswordForm)} className="w-full px-6 py-4 flex items-center justify-between hover:bg-hover transition-colors">
                <h3 className="text-lg font-medium text-primary">Change Password</h3>
                <svg className={`h-5 w-5 text-muted transform transition-transform ${showPasswordForm ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {showPasswordForm && (
                <form onSubmit={handleChangePassword} className="px-6 pb-6 space-y-4">
                  {passwordError && <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400 text-sm">{passwordError}</div>}
                  {passwordSuccess && <div className="p-3 bg-green-500/20 border border-green-500/50 rounded-lg text-green-400 text-sm">{passwordSuccess}</div>}
                  <div><label className="block text-sm text-muted mb-1">Current Password</label><input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required className="w-full px-4 py-2 bg-tertiary text-primary rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent" /></div>
                  <div><label className="block text-sm text-muted mb-1">New Password</label><input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required className="w-full px-4 py-2 bg-tertiary text-primary rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent" /></div>
                  <div><label className="block text-sm text-muted mb-1">Confirm New Password</label><input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required className="w-full px-4 py-2 bg-tertiary text-primary rounded-lg border border-theme focus:outline-none focus:ring-2 focus:ring-accent" /></div>
                  <button type="submit" disabled={isChangingPassword} className="w-full py-2 px-4 text-sm font-medium text-white bg-accent rounded-lg hover:opacity-90 transition-colors disabled:opacity-50">{isChangingPassword ? 'Changing Password...' : 'Change Password'}</button>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ColorPicker({ label, value, onChange, disabled }: { label: string; value: string; onChange: (value: string) => void; disabled?: boolean }) {
  return (
    <div className={`flex items-center justify-between ${disabled ? 'opacity-70' : ''}`}>
      <span className="text-sm text-secondary">{label}</span>
      <div className="flex items-center gap-2">
        <input type="color" value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled} className={`w-8 h-8 rounded border-0 bg-transparent ${disabled ? 'cursor-not-allowed' : 'cursor-pointer'}`} />
        <input type="text" value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled} className={`w-20 px-2 py-1 text-xs bg-secondary text-primary rounded border border-theme font-mono ${disabled ? 'cursor-not-allowed' : ''}`} />
      </div>
    </div>
  );
}





