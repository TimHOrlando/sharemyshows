export interface PasswordRule {
  id: string;
  label: string;
  test: (password: string) => boolean;
  isWarning?: boolean;
}

export const passwordRules: PasswordRule[] = [
  {
    id: 'minLength',
    label: 'At least 12 characters',
    test: (pw) => pw.length >= 12,
  },
  {
    id: 'uppercase',
    label: 'At least 1 uppercase letter',
    test: (pw) => /[A-Z]/.test(pw),
  },
  {
    id: 'lowercase',
    label: 'At least 1 lowercase letter',
    test: (pw) => /[a-z]/.test(pw),
  },
  {
    id: 'specialChar',
    label: 'At least 1 special character (e.g. !@#$%^&*)',
    test: (pw) => /[^a-zA-Z0-9_]/.test(pw),
  },
  {
    id: 'noUnderscore',
    label: 'Underscores are not allowed',
    test: (pw) => !pw.includes('_'),
    isWarning: true,
  },
];

export function validatePassword(password: string): boolean {
  return passwordRules.every((rule) => rule.test(password));
}
