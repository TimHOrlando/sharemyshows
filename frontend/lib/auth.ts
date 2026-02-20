import api from './api';
import { RegisterData, LoginData, MFAVerificationData, AuthResponse, User, RequestPasswordResetData, ResetPasswordData, EnableMFAData } from './types';

export const authService = {
  // Register a new user
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/register', data);

    // If MFA not required, store token
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }

    return response.data;
  },

  // Login user
  async login(data: LoginData): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/login', data);

    // If MFA not required, store token
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }

    return response.data;
  },

  // Verify MFA code (accepts MFAVerificationData or just a code string)
  async verifyMFA(dataOrCode: MFAVerificationData | string): Promise<AuthResponse> {
    const data = typeof dataOrCode === 'string'
      ? { code: dataOrCode, email: '' }
      : dataOrCode;
    const response = await api.post<AuthResponse>('/auth/verify-mfa', data);

    // Store token after successful MFA verification
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }

    return response.data;
  },

  // Get current user profile
  async getProfile(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  // Logout user
  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } finally {
      // Always clear local storage even if API call fails
      localStorage.removeItem('access_token');
    }
  },

  // Resend MFA code
  async resendMFA(email: string): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/auth/resend-mfa', { email });
    return response.data;
  },

  // Request password reset
  async requestPasswordReset(data: RequestPasswordResetData): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/auth/request-password-reset', data);
    return response.data;
  },

  // Reset password
  async resetPassword(data: ResetPasswordData): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/auth/reset-password', data);
    return response.data;
  },

  // Enable or disable MFA from profile
  async toggleMFA(data: EnableMFAData): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/profile/mfa', data);
    return response.data;
  },

  // Enable MFA (convenience method for SettingsModal)
  async enableMFA(): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/profile/mfa', { enable: true });
    return response.data;
  },

  // Disable MFA (convenience method for SettingsModal)
  async disableMFA(): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/profile/mfa', { enable: false });
    return response.data;
  },

  // Verify MFA code when enabling from profile
  async verifyMFAEnable(code: string, email: string): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/auth/profile/verify-mfa', { code, email });
    return response.data;
  },

  // Change password
  async changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    });
    return response.data;
  },

  // Update email address
  async updateEmail(email: string): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/auth/profile/email', { email });
    return response.data;
  },

  // Request temporary password
  async requestTempPassword(deliveryMethod: 'email' | 'sms', phoneNumber?: string): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/auth/request-temp-password', {
      delivery_method: deliveryMethod,
      phone_number: phoneNumber
    });
    return response.data;
  },

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },
};
