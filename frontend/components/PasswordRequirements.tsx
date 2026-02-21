'use client';

import { passwordRules } from '@/lib/passwordValidation';

interface PasswordRequirementsProps {
  password: string;
}

export default function PasswordRequirements({ password }: PasswordRequirementsProps) {
  if (!password) return null;

  return (
    <div className="mt-2 p-3 bg-tertiary rounded-lg space-y-1.5">
      <p className="text-xs font-medium text-secondary mb-2">Password requirements:</p>
      {passwordRules.map((rule) => {
        const passed = rule.test(password);

        // Warning rules (underscore) only show when violated
        if (rule.isWarning && passed) return null;

        return (
          <div key={rule.id} className="flex items-center gap-2">
            {rule.isWarning && !passed ? (
              <svg className="h-4 w-4 text-yellow-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            ) : passed ? (
              <svg className="h-4 w-4 text-green-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="h-4 w-4 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
            <span className={`text-xs ${
              rule.isWarning && !passed
                ? 'text-yellow-400'
                : passed
                  ? 'text-green-400'
                  : 'text-red-400'
            }`}>
              {rule.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
