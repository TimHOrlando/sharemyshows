// Authentication Types
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  bio?: string;
  profile_picture_url?: string;
  mfa_enabled: boolean;
  appear_offline?: boolean;
  created_at: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  enable_mfa?: boolean;
}

export interface LoginData {
  login: string;
  password: string;
}

export interface MFAVerificationData {
  email: string;
  code: string;
}

export interface RequestPasswordResetData {
  email: string;
}

export interface ResetPasswordData {
  token: string;
  password: string;
}

export interface EnableMFAData {
  enable: boolean;
}

export interface AuthResponse {
  message: string;
  access_token?: string;
  user?: User;
  requires_mfa?: boolean;
  mfa_required?: boolean;
}

export interface ApiError {
  message: string;
  errors?: Record<string, string[]>;
}
