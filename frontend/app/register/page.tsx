'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import PasswordRequirements from '@/components/PasswordRequirements';
import { validatePassword } from '@/lib/passwordValidation';

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    enableMFA: false,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    // Username validation
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    }

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (!validatePassword(formData.password)) {
      newErrors.password = 'Password does not meet all requirements';
    }

    // Confirm password validation
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setErrors({});
    setSuccessMessage('');

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const result = await register(
        formData.username,
        formData.email,
        formData.password,
        formData.enableMFA
      );

      if (result.requiresMFA) {
        // Redirect to MFA verification page
        router.push(`/verify-mfa?email=${encodeURIComponent(formData.email)}`);
      } else {
        // Registration successful, redirect to dashboard
        setSuccessMessage(result.message || 'Registration successful!');
        setTimeout(() => {
          router.push('/dashboard');
        }, 1500);
      }
    } catch (error) {
      const err = error as { response?: { data?: { error?: string; message?: string; errors?: Record<string, string> } } };
      const errorMessage = err.response?.data?.error || err.response?.data?.message || 'Registration failed. Please try again.';
      const fieldErrors = err.response?.data?.errors;

      if (fieldErrors) {
        setErrors(fieldErrors);
      } else if (errorMessage.toLowerCase().includes('username')) {
        setErrors({ username: errorMessage });
      } else if (errorMessage.toLowerCase().includes('email')) {
        setErrors({ email: errorMessage });
      } else {
        setErrors({ general: errorMessage });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-primary py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-card p-8 rounded-xl shadow-2xl">
        <div>
          <h2 className="text-center text-3xl font-extrabold text-primary">
            ShareMyShows
          </h2>
          <p className="mt-2 text-center text-sm text-secondary">
            Create your account
          </p>
        </div>

        {successMessage && (
          <div className="rounded-md bg-green-500/20 border border-green-500/50 p-4">
            <p className="text-sm font-medium text-green-400">{successMessage}</p>
          </div>
        )}

        {errors.general && (
          <div className="rounded-md bg-red-500/20 border border-red-500/50 p-4">
            <p className="text-sm font-medium text-red-400">{errors.general}</p>
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-secondary">
                Username *
              </label>
              <input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                required
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className={`mt-1 appearance-none relative block w-full px-3 py-3 border ${
                  errors.username ? 'border-red-500' : 'border-theme'
                } placeholder-muted text-primary bg-secondary rounded-md focus:outline-none focus:ring-accent focus:border-accent focus:z-10 sm:text-sm`}
                placeholder="johndoe"
              />
              {errors.username && (
                <p className="mt-1 text-sm text-red-400">{errors.username}</p>
              )}
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-secondary">
                Email address *
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className={`mt-1 appearance-none relative block w-full px-3 py-3 border ${
                  errors.email ? 'border-red-500' : 'border-theme'
                } placeholder-muted text-primary bg-secondary rounded-md focus:outline-none focus:ring-accent focus:border-accent focus:z-10 sm:text-sm`}
                placeholder="john@example.com"
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-400">{errors.email}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-secondary">
                Password *
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className={`mt-1 appearance-none relative block w-full px-3 py-3 pr-12 border ${
                    errors.password ? 'border-red-500' : 'border-theme'
                  } placeholder-muted text-primary bg-secondary rounded-md focus:outline-none focus:ring-accent focus:border-accent focus:z-10 sm:text-sm`}
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center w-10 justify-center"
                >
                  {showPassword ? (
                    <svg className="h-5 w-5 text-muted hover:text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5 text-muted hover:text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-red-400">{errors.password}</p>
              )}
              <PasswordRequirements password={formData.password} />
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-secondary">
                Confirm Password *
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  className={`mt-1 appearance-none relative block w-full px-3 py-3 pr-12 border ${
                    errors.confirmPassword ? 'border-red-500' : 'border-theme'
                  } placeholder-muted text-primary bg-secondary rounded-md focus:outline-none focus:ring-accent focus:border-accent focus:z-10 sm:text-sm`}
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center w-10 justify-center"
                >
                  {showConfirmPassword ? (
                    <svg className="h-5 w-5 text-muted hover:text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5 text-muted hover:text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="mt-1 text-sm text-red-400">{errors.confirmPassword}</p>
              )}
            </div>

            {/* Enable MFA */}
            <div className="flex items-center">
              <input
                id="enableMFA"
                name="enableMFA"
                type="checkbox"
                checked={formData.enableMFA}
                onChange={(e) => setFormData({ ...formData, enableMFA: e.target.checked })}
                className="h-5 w-5 text-accent focus:ring-accent border-theme rounded"
              />
              <label htmlFor="enableMFA" className="ml-3 block text-sm text-secondary">
                Enable Multi-Factor Authentication (MFA) for extra security
              </label>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading || (formData.password.length > 0 && !validatePassword(formData.password)) || (formData.confirmPassword.length > 0 && formData.password !== formData.confirmPassword)}
              className={`group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white ${
                isLoading || (formData.password.length > 0 && !validatePassword(formData.password)) || (formData.confirmPassword.length > 0 && formData.password !== formData.confirmPassword)
                  ? 'bg-accent opacity-50 cursor-not-allowed'
                  : 'bg-accent hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent'
              }`}
            >
              {isLoading ? 'Creating account...' : 'Create account'}
            </button>
          </div>

          <div className="text-center">
            <p className="text-sm text-secondary">
              Already signed up?{' '}
              <Link href="/login" className="font-medium text-accent hover:opacity-80">
                Sign in
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
