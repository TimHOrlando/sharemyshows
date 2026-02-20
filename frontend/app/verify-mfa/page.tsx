'use client';

import { useState, FormEvent, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { authService } from '@/lib/auth';

function VerifyMFAContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { verifyMFA } = useAuth();

  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendMessage, setResendMessage] = useState('');

  useEffect(() => {
    const emailParam = searchParams.get('email');
    const codeParam = searchParams.get('code');

    if (emailParam) {
      setEmail(emailParam);
    } else {
      // If no email in URL, redirect to login
      router.push('/login');
    }

    // Auto-fill code if provided in URL
    if (codeParam) {
      setCode(codeParam);
    }
  }, [searchParams, router]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!code || code.length !== 6) {
      setError('Please enter a valid 6-digit code');
      return;
    }

    setIsLoading(true);

    try {
      await verifyMFA(email, code);
      // Verification successful, redirect to dashboard
      router.push('/dashboard');
    } catch (error) {
      const errorMessage = (error as { response?: { data?: { message?: string } } }).response?.data?.message || 'Invalid or expired code. Please try again.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = async () => {
    setError('');
    setResendMessage('');
    setResendLoading(true);

    try {
      const response = await authService.resendMFA(email);
      setResendMessage(response.message || 'Verification code resent successfully!');
      setCode(''); // Clear the code input
    } catch (error) {
      const errorMessage = (error as { response?: { data?: { message?: string } } }).response?.data?.message || 'Failed to resend code. Please try again.';
      setError(errorMessage);
    } finally {
      setResendLoading(false);
    }
  };

  const handleCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, ''); // Only allow digits
    if (value.length <= 6) {
      setCode(value);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-primary py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-card p-8 rounded-xl shadow-2xl">
        <div>
          <h2 className="text-center text-3xl font-extrabold text-primary">
            Verify Your Account
          </h2>
          <p className="mt-2 text-center text-sm text-secondary">
            Enter the 6-digit code sent to
          </p>
          <p className="text-center text-sm font-medium text-primary">
            {email}
          </p>
        </div>

        {error && (
          <div className="rounded-md bg-red-500/20 border border-red-500/50 p-4">
            <p className="text-sm font-medium text-red-400">{error}</p>
          </div>
        )}

        {resendMessage && (
          <div className="rounded-md bg-green-500/20 border border-green-500/50 p-4">
            <p className="text-sm font-medium text-green-400">{resendMessage}</p>
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="code" className="block text-sm font-medium text-secondary text-center">
              Verification Code
            </label>
            <input
              id="code"
              name="code"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              required
              value={code}
              onChange={handleCodeChange}
              className="mt-2 appearance-none relative block w-full px-3 py-3 border border-theme placeholder-muted text-primary bg-secondary rounded-md focus:outline-none focus:ring-accent focus:border-accent focus:z-10 text-center text-2xl tracking-widest font-mono"
              placeholder="000000"
              maxLength={6}
              autoComplete="one-time-code"
            />
            <p className="mt-2 text-xs text-muted text-center">
              Enter the 6-digit code from your email
            </p>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading || code.length !== 6}
              className={`group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white ${
                isLoading || code.length !== 6
                  ? 'bg-accent opacity-50 cursor-not-allowed'
                  : 'bg-accent hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent'
              }`}
            >
              {isLoading ? 'Verifying...' : 'Verify Code'}
            </button>
          </div>

          <div className="text-center space-y-2">
            <button
              type="button"
              onClick={handleResendCode}
              disabled={resendLoading}
              className="text-sm font-medium text-accent hover:opacity-80 disabled:opacity-50"
            >
              {resendLoading ? 'Resending...' : "Didn't receive a code? Resend"}
            </button>

            <div>
              <Link href="/login" className="text-sm font-medium text-secondary hover:text-primary">
                Back to login
              </Link>
            </div>
          </div>
        </form>

        <div className="mt-6 p-4 bg-tertiary rounded-md">
          <p className="text-xs text-secondary">
            <strong>Note:</strong> The verification code expires in 10 minutes.
            If you don&apos;t see the email, check your spam folder.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function VerifyMFAPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-primary">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto"></div>
          <p className="mt-4 text-secondary">Loading...</p>
        </div>
      </div>
    }>
      <VerifyMFAContent />
    </Suspense>
  );
}
