import React, { useState } from 'react';
import { Camera, Music, MessageSquare, List, Plus, User, Users, LogOut, Calendar, MapPin, Clock } from 'lucide-react';

const ShareMyShowsDemo = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedShow, setSelectedShow] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showPhotosModal, setShowPhotosModal] = useState(false);
  const [showAudioModal, setShowAudioModal] = useState(false);
  const [showCommentsModal, setShowCommentsModal] = useState(false);
  const [showSetlistModal, setShowSetlistModal] = useState(false);
  const [currentShowForContent, setCurrentShowForContent] = useState(null);
  const [showAllShowsModal, setShowAllShowsModal] = useState(false);
  const [showAllArtistsModal, setShowAllArtistsModal] = useState(false);
  const [showAllVenuesModal, setShowAllVenuesModal] = useState(false);
  const [showAllPhotosModal, setShowAllPhotosModal] = useState(false);
  const [showAllAudioModal, setShowAllAudioModal] = useState(false);
  const [showAllCommentsModal, setShowAllCommentsModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [showForgotPasswordModal, setShowForgotPasswordModal] = useState(false);
  const [showFriendsModal, setShowFriendsModal] = useState(false);
  const [showChatModal, setShowChatModal] = useState(false);
  const [isCheckedIn, setIsCheckedIn] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    { id: 1, username: 'musiclover87', message: 'This opening act is amazing!', timestamp: new Date(Date.now() - 300000) },
    { id: 2, username: 'concert_junkie', message: 'Right?! Can\'t wait for the main set', timestamp: new Date(Date.now() - 240000) },
    { id: 3, username: 'You', message: 'Best seats ever! Can you see from where you are?', timestamp: new Date(Date.now() - 180000) },
  ]);

  // Sample data
  const stats = {
    shows: 23,
    artists: 45,
    venues: 18,
    photos: 342,
    audio: 156,
    comments: 89
  };

  const sampleShows = [
    {
      id: 1,
      artist: 'Arctic Monkeys',
      venue: 'Madison Square Garden',
      location: 'New York, NY',
      date: '2024-10-15',
      photos: 24,
      audio: 8,
      comments: 5,
      songs: 18
    },
    {
      id: 2,
      artist: 'Taylor Swift',
      venue: 'SoFi Stadium',
      location: 'Los Angeles, CA',
      date: '2024-09-22',
      photos: 31,
      audio: 12,
      comments: 7,
      songs: 22
    },
    {
      id: 3,
      artist: 'The 1975',
      venue: 'Radio City Music Hall',
      location: 'New York, NY',
      date: '2024-08-10',
      photos: 18,
      audio: 6,
      comments: 4,
      songs: 16
    }
  ];

  // Aggregated artist data
  const artistData = [
    { name: 'Arctic Monkeys', count: 3, lastSeen: '2024-10-15' },
    { name: 'Taylor Swift', count: 5, lastSeen: '2024-09-22' },
    { name: 'The 1975', count: 2, lastSeen: '2024-08-10' },
    { name: 'Foo Fighters', count: 4, lastSeen: '2024-07-12' },
    { name: 'Billie Eilish', count: 2, lastSeen: '2024-06-05' },
  ];

  // Aggregated venue data
  const venueData = [
    { name: 'Madison Square Garden', location: 'New York, NY', count: 8, lastVisit: '2024-10-15' },
    { name: 'SoFi Stadium', location: 'Los Angeles, CA', count: 3, lastVisit: '2024-09-22' },
    { name: 'Radio City Music Hall', location: 'New York, NY', count: 5, lastVisit: '2024-08-10' },
    { name: 'Red Rocks Amphitheatre', location: 'Morrison, CO', count: 2, lastVisit: '2024-07-01' },
  ];

  // Friends data
  const friendsData = [
    { 
      id: 1, 
      username: 'musiclover87', 
      status: 'friends', 
      atSameShow: true,
      lastSeen: 'Active now',
      mutualFriends: 5
    },
    { 
      id: 2, 
      username: 'concert_junkie', 
      status: 'friends', 
      atSameShow: true,
      lastSeen: 'Active now',
      mutualFriends: 3
    },
    { 
      id: 3, 
      username: 'rockfan_nyc', 
      status: 'friends', 
      atSameShow: false,
      lastSeen: '2 hours ago',
      mutualFriends: 8
    },
    { 
      id: 4, 
      username: 'indie_vibes', 
      status: 'pending', 
      atSameShow: false,
      lastSeen: '1 day ago',
      mutualFriends: 2
    },
  ];

  // Login Component
  const LoginPage = () => (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="bg-green-600 w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center">
            <Music className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">ShareMyShows</h1>
          <p className="text-gray-400">Document Your Concert Experiences</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-8 shadow-2xl">
          <div className="space-y-4">
            <div>
              <label className="text-white text-sm font-medium mb-2 block">Username or Email</label>
              <input
                type="text"
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-lg"
                placeholder="Enter username or email"
              />
            </div>
            
            <div>
              <label className="text-white text-sm font-medium mb-2 block">Password</label>
              <input
                type="password"
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-lg"
                placeholder="Enter password"
              />
            </div>

            <button
              onClick={() => setIsLoggedIn(true)}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg transition-colors text-lg"
            >
              Log In
            </button>

            <div className="flex justify-between text-sm">
              <button 
                onClick={() => setShowForgotPasswordModal(true)}
                className="text-green-500 hover:text-green-400"
              >
                Forgot Password?
              </button>
              <button 
                onClick={() => setShowRegisterModal(true)}
                className="text-green-500 hover:text-green-400"
              >
                Register
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Register Modal
  const RegisterModal = ({ onClose }) => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [enableMfa, setEnableMfa] = useState(false);
    const [mfaMethod, setMfaMethod] = useState('email');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [errors, setErrors] = useState({});
    const [touched, setTouched] = useState({});

    const validatePassword = (password) => {
      const errors = [];
      if (password.length < 15) {
        errors.push('At least 15 characters');
      }
      if (password.length >= 15 && password.length <= 35) {
        if (!/[A-Z]/.test(password)) errors.push('1 uppercase letter');
        if (!/[a-z]/.test(password)) errors.push('1 lowercase letter');
        if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) errors.push('1 special character (not _)');
      }
      return errors;
    };

    const validateForm = () => {
      const newErrors = {};
      if (!username.trim()) newErrors.username = 'Username is required';
      if (!email.trim()) newErrors.email = 'Email is required';
      if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        newErrors.email = 'Valid email is required';
      }
      
      const passwordErrors = validatePassword(password);
      if (passwordErrors.length > 0) {
        newErrors.password = 'Password must have: ' + passwordErrors.join(', ');
      }
      
      if (password !== confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }

      if (enableMfa && mfaMethod === 'sms' && !phoneNumber.trim()) {
        newErrors.phoneNumber = 'Phone number is required for SMS verification';
      }

      return newErrors;
    };

    const handleSubmit = () => {
      const newErrors = validateForm();
      if (Object.keys(newErrors).length === 0) {
        // Registration successful
        onClose();
        setIsLoggedIn(true);
      } else {
        setErrors(newErrors);
        setTouched({
          username: true,
          email: true,
          password: true,
          confirmPassword: true,
          phoneNumber: true
        });
      }
    };

    const handleBlur = (field) => {
      setTouched({ ...touched, [field]: true });
      const newErrors = validateForm();
      setErrors(newErrors);
    };

    const getPasswordStrength = (password) => {
      const errors = validatePassword(password);
      if (!password) return { strength: 0, color: 'bg-gray-600', label: '' };
      if (errors.length === 0) return { strength: 100, color: 'bg-green-500', label: 'Strong' };
      if (errors.length <= 2) return { strength: 66, color: 'bg-yellow-500', label: 'Medium' };
      return { strength: 33, color: 'bg-red-500', label: 'Weak' };
    };

    const passwordStrength = getPasswordStrength(password);

    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 z-50">
        <div className="bg-gray-800 rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-3xl font-bold">Create Account</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-white text-3xl leading-none">
              ×
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-white text-sm font-medium mb-2 block">
                Username <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  if (touched.username) handleBlur('username');
                }}
                onBlur={() => handleBlur('username')}
                className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                  touched.username && errors.username ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                }`}
                placeholder="Choose a username"
              />
              {touched.username && errors.username && (
                <p className="text-red-500 text-sm mt-1">{errors.username}</p>
              )}
            </div>

            <div>
              <label className="text-white text-sm font-medium mb-2 block">
                Email Address <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (touched.email) handleBlur('email');
                }}
                onBlur={() => handleBlur('email')}
                className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                  touched.email && errors.email ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                }`}
                placeholder="your@email.com"
              />
              {touched.email && errors.email && (
                <p className="text-red-500 text-sm mt-1">{errors.email}</p>
              )}
            </div>

            <div>
              <label className="text-white text-sm font-medium mb-2 block">
                Password <span className="text-red-500">*</span>
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (touched.password) handleBlur('password');
                }}
                onBlur={() => handleBlur('password')}
                className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                  touched.password && errors.password ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                }`}
                placeholder="Create a strong password"
              />
              {password && (
                <div className="mt-2">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-400">Password strength:</span>
                    <span className={`font-semibold ${passwordStrength.color.replace('bg-', 'text-')}`}>
                      {passwordStrength.label}
                    </span>
                  </div>
                  <div className="w-full bg-gray-600 rounded-full h-2">
                    <div
                      className={`${passwordStrength.color} h-2 rounded-full transition-all`}
                      style={{ width: `${passwordStrength.strength}%` }}
                    />
                  </div>
                </div>
              )}
              {touched.password && errors.password && (
                <p className="text-red-500 text-sm mt-1">{errors.password}</p>
              )}
              <p className="text-gray-400 text-xs mt-1">
                Must be 15+ characters. If 15-35 chars: 1 uppercase, 1 lowercase, 1 special char (not _). 36+ chars: no additional requirements
              </p>
            </div>

            <div>
              <label className="text-white text-sm font-medium mb-2 block">
                Confirm Password <span className="text-red-500">*</span>
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  if (touched.confirmPassword) handleBlur('confirmPassword');
                }}
                onBlur={() => handleBlur('confirmPassword')}
                className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                  touched.confirmPassword && errors.confirmPassword ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                }`}
                placeholder="Confirm your password"
              />
              {touched.confirmPassword && errors.confirmPassword && (
                <p className="text-red-500 text-sm mt-1">{errors.confirmPassword}</p>
              )}
            </div>

            {/* MFA Option */}
            <div className="border-t border-gray-700 pt-4">
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableMfa}
                  onChange={(e) => setEnableMfa(e.target.checked)}
                  className="w-5 h-5 text-green-600 bg-gray-700 border-gray-600 rounded focus:ring-green-500"
                />
                <div>
                  <div className="font-semibold">Enable Multi-Factor Authentication</div>
                  <div className="text-gray-400 text-sm">Add extra security to your account</div>
                </div>
              </label>

              {enableMfa && (
                <div className="mt-4 ml-8 space-y-3">
                  <label className="text-white text-sm font-medium block">Verification Method</label>
                  <div className="space-y-2">
                    <label className="flex items-center space-x-3 p-3 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-650">
                      <input
                        type="radio"
                        name="registerMfaMethod"
                        value="email"
                        checked={mfaMethod === 'email'}
                        onChange={(e) => setMfaMethod(e.target.value)}
                        className="w-5 h-5 text-green-600 focus:ring-green-500"
                      />
                      <div>
                        <div className="font-semibold">Email Verification</div>
                        <div className="text-gray-400 text-sm">Receive codes at your email</div>
                      </div>
                    </label>
                    <label className="flex items-center space-x-3 p-3 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-650">
                      <input
                        type="radio"
                        name="registerMfaMethod"
                        value="sms"
                        checked={mfaMethod === 'sms'}
                        onChange={(e) => setMfaMethod(e.target.value)}
                        className="w-5 h-5 text-green-600 focus:ring-green-500"
                      />
                      <div>
                        <div className="font-semibold">SMS Verification</div>
                        <div className="text-gray-400 text-sm">Receive codes via text</div>
                      </div>
                    </label>
                  </div>

                  {mfaMethod === 'sms' && (
                    <div className="mt-3">
                      <label className="text-white text-sm font-medium mb-2 block">
                        Phone Number <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="tel"
                        value={phoneNumber}
                        onChange={(e) => {
                          setPhoneNumber(e.target.value);
                          if (touched.phoneNumber) handleBlur('phoneNumber');
                        }}
                        onBlur={() => handleBlur('phoneNumber')}
                        placeholder="+1 (555) 123-4567"
                        className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                          touched.phoneNumber && errors.phoneNumber ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                        }`}
                      />
                      {touched.phoneNumber && errors.phoneNumber && (
                        <p className="text-red-500 text-sm mt-1">{errors.phoneNumber}</p>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                onClick={onClose}
                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-4 rounded-lg transition-colors text-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg transition-colors text-lg"
              >
                Create Account
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Forgot Password Modal
  const ForgotPasswordModal = ({ onClose }) => {
    const [step, setStep] = useState(1); // 1: choose method, 2: enter code, 3: new password
    const [verificationMethod, setVerificationMethod] = useState('email');
    const [emailOrPhone, setEmailOrPhone] = useState('');
    const [verificationCode, setVerificationCode] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [errors, setErrors] = useState({});
    const [touched, setTouched] = useState({});

    const validatePassword = (password) => {
      const errors = [];
      if (password.length < 15) {
        errors.push('At least 15 characters');
      }
      if (password.length >= 15 && password.length <= 35) {
        if (!/[A-Z]/.test(password)) errors.push('1 uppercase letter');
        if (!/[a-z]/.test(password)) errors.push('1 lowercase letter');
        if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) errors.push('1 special character (not _)');
      }
      return errors;
    };

    const handleSendCode = () => {
      if (!emailOrPhone.trim()) {
        setErrors({ emailOrPhone: verificationMethod === 'email' ? 'Email is required' : 'Phone number is required' });
        return;
      }
      // Send code logic here
      setStep(2);
    };

    const handleVerifyCode = () => {
      if (!verificationCode.trim()) {
        setErrors({ verificationCode: 'Verification code is required' });
        return;
      }
      // Verify code logic here
      setStep(3);
    };

    const handleResetPassword = () => {
      const newErrors = {};
      const passwordErrors = validatePassword(newPassword);
      if (passwordErrors.length > 0) {
        newErrors.newPassword = 'Password must have: ' + passwordErrors.join(', ');
      }
      if (newPassword !== confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }

      if (Object.keys(newErrors).length === 0) {
        // Password reset successful
        onClose();
      } else {
        setErrors(newErrors);
        setTouched({ newPassword: true, confirmPassword: true });
      }
    };

    const getPasswordStrength = (password) => {
      const errors = validatePassword(password);
      if (!password) return { strength: 0, color: 'bg-gray-600', label: '' };
      if (errors.length === 0) return { strength: 100, color: 'bg-green-500', label: 'Strong' };
      if (errors.length <= 2) return { strength: 66, color: 'bg-yellow-500', label: 'Medium' };
      return { strength: 33, color: 'bg-red-500', label: 'Weak' };
    };

    const passwordStrength = getPasswordStrength(newPassword);

    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 z-50">
        <div className="bg-gray-800 rounded-lg p-8 max-w-xl w-full">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-3xl font-bold">Reset Password</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-white text-3xl leading-none">
              ×
            </button>
          </div>

          {step === 1 && (
            <div className="space-y-4">
              <p className="text-gray-400">Choose how you'd like to receive your verification code:</p>
              
              <div className="space-y-3">
                <label className="flex items-center space-x-3 p-4 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-650">
                  <input
                    type="radio"
                    name="forgotMethod"
                    value="email"
                    checked={verificationMethod === 'email'}
                    onChange={(e) => setVerificationMethod(e.target.value)}
                    className="w-5 h-5 text-green-600 focus:ring-green-500"
                  />
                  <div className="flex-1">
                    <div className="font-semibold">Email Verification</div>
                    <div className="text-gray-400 text-sm">We'll send a code to your email</div>
                  </div>
                </label>
                <label className="flex items-center space-x-3 p-4 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-650">
                  <input
                    type="radio"
                    name="forgotMethod"
                    value="sms"
                    checked={verificationMethod === 'sms'}
                    onChange={(e) => setVerificationMethod(e.target.value)}
                    className="w-5 h-5 text-green-600 focus:ring-green-500"
                  />
                  <div className="flex-1">
                    <div className="font-semibold">SMS Verification</div>
                    <div className="text-gray-400 text-sm">We'll text a code to your phone</div>
                  </div>
                </label>
              </div>

              <div>
                <label className="text-white text-sm font-medium mb-2 block">
                  {verificationMethod === 'email' ? 'Email Address' : 'Phone Number'}
                </label>
                <input
                  type={verificationMethod === 'email' ? 'email' : 'tel'}
                  value={emailOrPhone}
                  onChange={(e) => setEmailOrPhone(e.target.value)}
                  placeholder={verificationMethod === 'email' ? 'your@email.com' : '+1 (555) 123-4567'}
                  className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                    errors.emailOrPhone ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                  }`}
                />
                {errors.emailOrPhone && (
                  <p className="text-red-500 text-sm mt-1">{errors.emailOrPhone}</p>
                )}
              </div>

              <button
                onClick={handleSendCode}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg transition-colors text-lg"
              >
                Send Verification Code
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <p className="text-gray-400">
                We've sent a verification code to {verificationMethod === 'email' ? 'your email' : 'your phone'}.
              </p>
              
              <div>
                <label className="text-white text-sm font-medium mb-2 block">Verification Code</label>
                <input
                  type="text"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  placeholder="Enter 6-digit code"
                  className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg text-center tracking-widest ${
                    errors.verificationCode ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                  }`}
                  maxLength="6"
                />
                {errors.verificationCode && (
                  <p className="text-red-500 text-sm mt-1">{errors.verificationCode}</p>
                )}
              </div>

              <button
                onClick={handleVerifyCode}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg transition-colors text-lg"
              >
                Verify Code
              </button>
              
              <button
                onClick={handleSendCode}
                className="w-full text-green-500 hover:text-green-400 text-sm"
              >
                Resend Code
              </button>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <p className="text-gray-400">Create a new password for your account.</p>
              
              <div>
                <label className="text-white text-sm font-medium mb-2 block">New Password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new password"
                  className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                    touched.newPassword && errors.newPassword ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                  }`}
                />
                {newPassword && (
                  <div className="mt-2">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-400">Password strength:</span>
                      <span className={`font-semibold ${passwordStrength.color.replace('bg-', 'text-')}`}>
                        {passwordStrength.label}
                      </span>
                    </div>
                    <div className="w-full bg-gray-600 rounded-full h-2">
                      <div
                        className={`${passwordStrength.color} h-2 rounded-full transition-all`}
                        style={{ width: `${passwordStrength.strength}%` }}
                      />
                    </div>
                  </div>
                )}
                {touched.newPassword && errors.newPassword && (
                  <p className="text-red-500 text-sm mt-1">{errors.newPassword}</p>
                )}
                <p className="text-gray-400 text-xs mt-1">
                  Must be 15+ characters. If 15-35 chars: 1 uppercase, 1 lowercase, 1 special char (not _). 36+ chars: no additional requirements
                </p>
              </div>

              <div>
                <label className="text-white text-sm font-medium mb-2 block">Confirm New Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm new password"
                  className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                    touched.confirmPassword && errors.confirmPassword ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                  }`}
                />
                {touched.confirmPassword && errors.confirmPassword && (
                  <p className="text-red-500 text-sm mt-1">{errors.confirmPassword}</p>
                )}
              </div>

              <button
                onClick={handleResetPassword}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg transition-colors text-lg"
              >
                Reset Password
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Dashboard Component
  const Dashboard = () => (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white pb-32 md:pb-8">
      {/* Header */}
      <header className="bg-black bg-opacity-50 backdrop-blur-sm sticky top-0 z-10 border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="bg-green-600 w-10 h-10 rounded-full flex items-center justify-center">
              <Music className="w-6 h-6" />
            </div>
            <h1 className="text-2xl font-bold">ShareMyShows</h1>
          </div>
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => setShowFriendsModal(true)}
              className="text-gray-400 hover:text-white transition-colors relative"
              title="Friends"
            >
              <Users className="w-6 h-6" />
              {friendsData.filter(f => f.status === 'pending').length > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                  {friendsData.filter(f => f.status === 'pending').length}
                </span>
              )}
            </button>
            <button 
              onClick={() => setShowSettingsModal(true)}
              className="text-gray-400 hover:text-white transition-colors"
              title="Settings"
            >
              <User className="w-6 h-6" />
            </button>
            <button 
              onClick={() => setIsLoggedIn(false)}
              className="text-gray-400 hover:text-white"
              title="Logout"
            >
              <LogOut className="w-6 h-6" />
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4">
        {/* Stats Bar - Desktop/Tablet Only */}
        <div className="block bg-gray-800 bg-opacity-50 border-b border-gray-700 rounded-b-lg my-4 max-md:hidden">
          <div className="py-3 px-2">
            <div className="flex justify-center items-center gap-1">
              <StatBarItem title="Shows" count={stats.shows} icon={<Music />} onClick={() => setShowAllShowsModal(true)} />
              <StatBarItem title="Artists" count={stats.artists} icon={<User />} onClick={() => setShowAllArtistsModal(true)} />
              <StatBarItem title="Venues" count={stats.venues} icon={<MapPin />} onClick={() => setShowAllVenuesModal(true)} />
              <StatBarItem title="Photos" count={stats.photos} icon={<Camera />} onClick={() => setShowAllPhotosModal(true)} />
              <StatBarItem title="Audio" count={stats.audio} icon={<Music />} onClick={() => setShowAllAudioModal(true)} />
              <StatBarItem title="Comments" count={stats.comments} icon={<MessageSquare />} onClick={() => setShowAllCommentsModal(true)} />
            </div>
          </div>
        </div>

        {/* Your Shows Header with Add Button - Desktop/Tablet */}
        <div className="flex mb-6 justify-between items-center max-md:hidden">
          <h2 className="text-3xl font-bold">Your Shows</h2>
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-full flex items-center space-x-2 transition-colors text-lg"
          >
            <Plus className="w-6 h-6" />
            <span>Add Show</span>
          </button>
        </div>

        {/* Mobile Header */}
        <div className="my-4 space-y-4 md:hidden">
          <h2 className="text-3xl font-bold">Your Shows</h2>
        </div>

        {/* Show Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-8">
          {sampleShows.map(show => (
            <ShowCard 
              key={show.id} 
              show={show} 
              onClick={() => setSelectedShow(show)}
              onPhotosClick={(show) => { setCurrentShowForContent(show); setShowPhotosModal(true); }}
              onAudioClick={(show) => { setCurrentShowForContent(show); setShowAudioModal(true); }}
              onCommentsClick={(show) => { setCurrentShowForContent(show); setShowCommentsModal(true); }}
              onSetlistClick={(show) => { setCurrentShowForContent(show); setShowSetlistModal(true); }}
            />
          ))}
        </div>
      </div>

      {/* Mobile Bottom Nav with Stats and Add Button */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 z-20 max-h-[60vh] overflow-y-auto md:hidden">
        {/* Add Show Button - Mobile */}
        <div className="px-4 py-3 border-b border-gray-700 sticky top-0 bg-gray-900 z-10">
          <button
            onClick={() => setShowAddModal(true)}
            className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-full flex items-center justify-center space-x-2 transition-colors text-lg"
          >
            <Plus className="w-6 h-6" />
            <span>Add Show</span>
          </button>
        </div>
        
        {/* Stats - Mobile Vertical (one per row) */}
        <div className="flex flex-col">
          <StatBarItemMobile title="Shows" count={stats.shows} icon={<Music />} onClick={() => setShowAllShowsModal(true)} />
          <StatBarItemMobile title="Artists" count={stats.artists} icon={<User />} onClick={() => setShowAllArtistsModal(true)} />
          <StatBarItemMobile title="Venues" count={stats.venues} icon={<MapPin />} onClick={() => setShowAllVenuesModal(true)} />
          <StatBarItemMobile title="Photos" count={stats.photos} icon={<Camera />} onClick={() => setShowAllPhotosModal(true)} />
          <StatBarItemMobile title="Audio" count={stats.audio} icon={<Music />} onClick={() => setShowAllAudioModal(true)} />
          <StatBarItemMobile title="Comments" count={stats.comments} icon={<MessageSquare />} onClick={() => setShowAllCommentsModal(true)} />
        </div>
      </div>

      {/* Add Show Modal */}
      {showAddModal && <AddShowModal onClose={() => setShowAddModal(false)} />}
      
      {/* Settings Modal */}
      {showSettingsModal && <SettingsModal onClose={() => setShowSettingsModal(false)} />}
      
      {/* Show Details Modal */}
      {selectedShow && <ShowDetailsModal show={selectedShow} onClose={() => setSelectedShow(null)} />}

      {/* Photos Modal */}
      {showPhotosModal && currentShowForContent && (
        <PhotosModal show={currentShowForContent} onClose={() => setShowPhotosModal(false)} />
      )}

      {/* Audio Modal */}
      {showAudioModal && currentShowForContent && (
        <AudioModal show={currentShowForContent} onClose={() => setShowAudioModal(false)} />
      )}

      {/* Comments Modal */}
      {showCommentsModal && currentShowForContent && (
        <CommentsModal show={currentShowForContent} onClose={() => setShowCommentsModal(false)} />
      )}

      {/* Setlist Modal */}
      {showSetlistModal && currentShowForContent && (
        <SetlistModal show={currentShowForContent} onClose={() => setShowSetlistModal(false)} />
      )}

      {/* All Shows Modal */}
      {showAllShowsModal && <AllShowsModal onClose={() => setShowAllShowsModal(false)} />}

      {/* All Artists Modal */}
      {showAllArtistsModal && <AllArtistsModal onClose={() => setShowAllArtistsModal(false)} />}

      {/* All Venues Modal */}
      {showAllVenuesModal && <AllVenuesModal onClose={() => setShowAllVenuesModal(false)} />}

      {/* All Photos Modal */}
      {showAllPhotosModal && <AllPhotosModal onClose={() => setShowAllPhotosModal(false)} />}

      {/* All Audio Modal */}
      {showAllAudioModal && <AllAudioModal onClose={() => setShowAllAudioModal(false)} />}

      {/* All Comments Modal */}
      {showAllCommentsModal && <AllCommentsModal onClose={() => setShowAllCommentsModal(false)} />}

      {/* Friends Modal */}
      {showFriendsModal && <FriendsModal onClose={() => setShowFriendsModal(false)} />}

      {/* Chat Modal */}
      {showChatModal && <ChatModal onClose={() => setShowChatModal(false)} />}
    </div>
  );

  // Stat Bar Item Component (for horizontal navbar)
  const StatBarItem = ({ title, count, icon, onClick }) => (
    <div 
      onClick={onClick}
      className="flex items-center space-x-2 px-3 py-2 hover:bg-gray-700 rounded-lg transition-colors cursor-pointer flex-shrink-0"
    >
      <div className="text-green-500">
        {React.cloneElement(icon, { className: 'w-4 h-4' })}
      </div>
      <div>
        <div className="text-lg font-bold">{count}</div>
        <div className="text-gray-400 text-xs whitespace-nowrap">{title}</div>
      </div>
    </div>
  );

  // Mobile Stat Bar Item (full-width horizontal rows)
  const StatBarItemMobile = ({ title, count, icon, onClick }) => (
    <div 
      onClick={onClick}
      className="flex items-center justify-between px-4 py-3 hover:bg-gray-800 transition-colors cursor-pointer border-b border-gray-700 last:border-b-0"
    >
      <div className="flex items-center space-x-3">
        <div className="text-green-500">
          {React.cloneElement(icon, { className: 'w-6 h-6' })}
        </div>
        <div className="text-lg text-gray-300">{title}</div>
      </div>
      <div className="text-2xl font-bold">{count}</div>
    </div>
  );

  // Show Card Component
  const ShowCard = ({ show, onClick, onPhotosClick, onAudioClick, onCommentsClick, onSetlistClick }) => (
    <div
      onClick={onClick}
      className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition-all cursor-pointer transform hover:scale-105"
    >
      <div className="mb-4">
        <h3 className="text-2xl font-bold mb-2">{show.artist}</h3>
        <div className="flex items-center text-gray-400 mb-1">
          <MapPin className="w-4 h-4 mr-2" />
          <span className="text-sm">{show.venue}</span>
        </div>
        <div className="flex items-center text-gray-400 mb-1">
          <MapPin className="w-4 h-4 mr-2" />
          <span className="text-sm">{show.location}</span>
        </div>
        <div className="flex items-center text-gray-400">
          <Calendar className="w-4 h-4 mr-2" />
          <span className="text-sm">{new Date(show.date).toLocaleDateString()}</span>
        </div>
      </div>

      <div className="flex justify-between items-center pt-4 border-t border-gray-700">
        <div 
          onClick={(e) => { e.stopPropagation(); onPhotosClick(show); }}
          className="flex items-center space-x-1 text-gray-400 hover:text-pink-500 transition-colors cursor-pointer p-2 rounded hover:bg-gray-700"
        >
          <Camera className="w-5 h-5" />
          <span className="font-semibold">{show.photos}</span>
        </div>
        <div 
          onClick={(e) => { e.stopPropagation(); onAudioClick(show); }}
          className="flex items-center space-x-1 text-gray-400 hover:text-orange-500 transition-colors cursor-pointer p-2 rounded hover:bg-gray-700"
        >
          <Music className="w-5 h-5" />
          <span className="font-semibold">{show.audio}</span>
        </div>
        <div 
          onClick={(e) => { e.stopPropagation(); onCommentsClick(show); }}
          className="flex items-center space-x-1 text-gray-400 hover:text-yellow-500 transition-colors cursor-pointer p-2 rounded hover:bg-gray-700"
        >
          <MessageSquare className="w-5 h-5" />
          <span className="font-semibold">{show.comments}</span>
        </div>
        <div 
          onClick={(e) => { e.stopPropagation(); onSetlistClick(show); }}
          className="flex items-center space-x-1 text-gray-400 hover:text-green-500 transition-colors cursor-pointer p-2 rounded hover:bg-gray-700"
        >
          <List className="w-5 h-5" />
          <span className="font-semibold">{show.songs}</span>
        </div>
      </div>
    </div>
  );

  // Add Show Modal
  const AddShowModal = ({ onClose }) => {
    const [artistQuery, setArtistQuery] = useState('');
    const [artistSuggestions, setArtistSuggestions] = useState([]);
    const [venueQuery, setVenueQuery] = useState('');
    const [venueSuggestions, setVenueSuggestions] = useState([]);
    const [venueCity, setVenueCity] = useState('');
    const [venueState, setVenueState] = useState('');
    const [venueZip, setVenueZip] = useState('');
    const [showDate, setShowDate] = useState('');
    const [showArtistDropdown, setShowArtistDropdown] = useState(false);
    const [showVenueDropdown, setShowVenueDropdown] = useState(false);
    const [errors, setErrors] = useState({});
    const [touched, setTouched] = useState({});

    // Validation functions
    const validateForm = () => {
      const newErrors = {};
      if (!artistQuery.trim()) newErrors.artist = 'Artist name is required';
      if (!venueQuery.trim()) newErrors.venue = 'Venue name is required';
      if (!venueCity.trim()) newErrors.city = 'City is required';
      if (!venueState.trim()) newErrors.state = 'State is required';
      if (!venueZip.trim()) newErrors.zip = 'ZIP code is required';
      if (venueZip && !/^\d{5}$/.test(venueZip)) newErrors.zip = 'ZIP must be 5 digits';
      if (!showDate) newErrors.date = 'Show date is required';
      return newErrors;
    };

    const handleSubmit = () => {
      const newErrors = validateForm();
      if (Object.keys(newErrors).length === 0) {
        // Form is valid, submit
        onClose();
      } else {
        setErrors(newErrors);
        setTouched({
          artist: true,
          venue: true,
          city: true,
          state: true,
          zip: true,
          date: true
        });
      }
    };

    const handleBlur = (field) => {
      setTouched({ ...touched, [field]: true });
      const newErrors = validateForm();
      setErrors(newErrors);
    };

    // Setlist.fm API search
    const searchArtists = async (query) => {
      if (query.length < 2) {
        setArtistSuggestions([]);
        return;
      }

      try {
        const response = await fetch(
          `https://api.setlist.fm/rest/1.0/search/artists?artistName=${encodeURIComponent(query)}&p=1&sort=relevance`,
          {
            headers: {
              'Accept': 'application/json',
              'x-api-key': '6694cdca-10c7-4744-baa2-f0c589ecb212'
            }
          }
        );
        const data = await response.json();
        setArtistSuggestions(data.artist || []);
        setShowArtistDropdown(true);
      } catch (error) {
        console.error('Error fetching artists:', error);
        // Demo fallback data
        setArtistSuggestions([
          { name: 'Arctic Monkeys', mbid: '1' },
          { name: 'The 1975', mbid: '2' },
          { name: 'Taylor Swift', mbid: '3' }
        ]);
        setShowArtistDropdown(true);
      }
    };

    // Google Places API search
    const searchVenues = async (query) => {
      if (query.length < 3) {
        setVenueSuggestions([]);
        return;
      }

      try {
        const response = await fetch(
          `https://maps.googleapis.com/maps/api/place/autocomplete/json?input=${encodeURIComponent(query)}&types=establishment&key=AIzaSyB5ry2_HpVGokAf3EqWnNAkzNUWQ7OfRRg`
        );
        const data = await response.json();
        setVenueSuggestions(data.predictions || []);
        setShowVenueDropdown(true);
      } catch (error) {
        console.error('Error fetching venues:', error);
        // Demo fallback data
        setVenueSuggestions([
          { 
            description: 'Madison Square Garden, New York, NY, USA',
            place_id: '1',
            structured_formatting: { main_text: 'Madison Square Garden' }
          },
          { 
            description: 'Radio City Music Hall, New York, NY, USA',
            place_id: '2',
            structured_formatting: { main_text: 'Radio City Music Hall' }
          }
        ]);
        setShowVenueDropdown(true);
      }
    };

    // Get place details from Google Places
    const getPlaceDetails = async (placeId) => {
      try {
        const response = await fetch(
          `https://maps.googleapis.com/maps/api/place/details/json?place_id=${placeId}&fields=address_components&key=AIzaSyB5ry2_HpVGokAf3EqWnNAkzNUWQ7OfRRg`
        );
        const data = await response.json();
        
        if (data.result && data.result.address_components) {
          const components = data.result.address_components;
          const city = components.find(c => c.types.includes('locality'))?.long_name || '';
          const state = components.find(c => c.types.includes('administrative_area_level_1'))?.short_name || '';
          const zip = components.find(c => c.types.includes('postal_code'))?.long_name || '';
          
          setVenueCity(city);
          setVenueState(state);
          setVenueZip(zip);
        }
      } catch (error) {
        console.error('Error fetching place details:', error);
        // Demo fallback
        setVenueCity('New York');
        setVenueState('NY');
        setVenueZip('10001');
      }
    };

    const handleArtistSelect = (artist) => {
      setArtistQuery(artist.name);
      setShowArtistDropdown(false);
      setErrors({ ...errors, artist: undefined });
    };

    const handleVenueSelect = (venue) => {
      setVenueQuery(venue.structured_formatting?.main_text || venue.description);
      setShowVenueDropdown(false);
      getPlaceDetails(venue.place_id);
      setErrors({ ...errors, venue: undefined });
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 z-50">
        <div className="bg-gray-800 rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <h2 className="text-3xl font-bold mb-6">Add New Show</h2>
          
          <div className="space-y-4">
            {/* Artist Name with Autocomplete */}
            <div className="relative">
              <label className="text-white text-sm font-medium mb-2 block">
                Artist Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={artistQuery}
                onChange={(e) => {
                  setArtistQuery(e.target.value);
                  searchArtists(e.target.value);
                  if (touched.artist) {
                    const newErrors = validateForm();
                    setErrors(newErrors);
                  }
                }}
                onBlur={() => handleBlur('artist')}
                onFocus={() => artistSuggestions.length > 0 && setShowArtistDropdown(true)}
                className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                  touched.artist && errors.artist ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                }`}
                placeholder="Search for artist..."
              />
              {touched.artist && errors.artist && (
                <p className="text-red-500 text-sm mt-1">{errors.artist}</p>
              )}
              {showArtistDropdown && artistSuggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-2 bg-gray-700 rounded-lg shadow-xl max-h-60 overflow-y-auto">
                  {artistSuggestions.map((artist, idx) => (
                    <div
                      key={idx}
                      onClick={() => handleArtistSelect(artist)}
                      className="px-4 py-3 hover:bg-gray-600 cursor-pointer text-white text-lg border-b border-gray-600 last:border-b-0"
                    >
                      {artist.name}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Venue Name with Autocomplete */}
            <div className="relative">
              <label className="text-white text-sm font-medium mb-2 block">
                Venue Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={venueQuery}
                onChange={(e) => {
                  setVenueQuery(e.target.value);
                  searchVenues(e.target.value);
                  if (touched.venue) {
                    const newErrors = validateForm();
                    setErrors(newErrors);
                  }
                }}
                onBlur={() => handleBlur('venue')}
                onFocus={() => venueSuggestions.length > 0 && setShowVenueDropdown(true)}
                className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                  touched.venue && errors.venue ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                }`}
                placeholder="Search for venue..."
              />
              {touched.venue && errors.venue && (
                <p className="text-red-500 text-sm mt-1">{errors.venue}</p>
              )}
              {showVenueDropdown && venueSuggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-2 bg-gray-700 rounded-lg shadow-xl max-h-60 overflow-y-auto">
                  {venueSuggestions.map((venue, idx) => (
                    <div
                      key={idx}
                      onClick={() => handleVenueSelect(venue)}
                      className="px-4 py-3 hover:bg-gray-600 cursor-pointer text-white border-b border-gray-600 last:border-b-0"
                    >
                      <div className="text-lg">{venue.structured_formatting?.main_text || venue.description}</div>
                      <div className="text-sm text-gray-400">{venue.structured_formatting?.secondary_text || ''}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Venue Location Fields */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-white text-sm font-medium mb-2 block">
                  City <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={venueCity}
                  onChange={(e) => {
                    setVenueCity(e.target.value);
                    if (touched.city) {
                      const newErrors = validateForm();
                      setErrors(newErrors);
                    }
                  }}
                  onBlur={() => handleBlur('city')}
                  className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                    touched.city && errors.city ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                  }`}
                  placeholder="City"
                />
                {touched.city && errors.city && (
                  <p className="text-red-500 text-sm mt-1">{errors.city}</p>
                )}
              </div>
              <div>
                <label className="text-white text-sm font-medium mb-2 block">
                  State <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={venueState}
                  onChange={(e) => {
                    setVenueState(e.target.value);
                    if (touched.state) {
                      const newErrors = validateForm();
                      setErrors(newErrors);
                    }
                  }}
                  onBlur={() => handleBlur('state')}
                  className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                    touched.state && errors.state ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                  }`}
                  placeholder="State"
                />
                {touched.state && errors.state && (
                  <p className="text-red-500 text-sm mt-1">{errors.state}</p>
                )}
              </div>
            </div>

            <div>
              <label className="text-white text-sm font-medium mb-2 block">
                ZIP Code <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={venueZip}
                onChange={(e) => {
                  setVenueZip(e.target.value);
                  if (touched.zip) {
                    const newErrors = validateForm();
                    setErrors(newErrors);
                  }
                }}
                onBlur={() => handleBlur('zip')}
                className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                  touched.zip && errors.zip ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                }`}
                placeholder="ZIP Code"
              />
              {touched.zip && errors.zip && (
                <p className="text-red-500 text-sm mt-1">{errors.zip}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-white text-sm font-medium mb-2 block">
                  Show Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={showDate}
                  onChange={(e) => {
                    setShowDate(e.target.value);
                    if (touched.date) {
                      const newErrors = validateForm();
                      setErrors(newErrors);
                    }
                  }}
                  onBlur={() => handleBlur('date')}
                  className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                    touched.date && errors.date ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                  }`}
                />
                {touched.date && errors.date && (
                  <p className="text-red-500 text-sm mt-1">{errors.date}</p>
                )}
              </div>

              <div>
                <label className="text-white text-sm font-medium mb-2 block">Show Time (Optional)</label>
                <input
                  type="time"
                  className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-lg"
                />
              </div>
            </div>

            <div>
              <label className="text-white text-sm font-medium mb-2 block">Comments</label>
              <textarea
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-lg"
                rows="3"
                placeholder="Add any notes about this show..."
              />
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                onClick={onClose}
                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-4 rounded-lg transition-colors text-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg transition-colors text-lg"
              >
                Add Show
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Settings Modal
  const SettingsModal = ({ onClose }) => {
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [mfaEnabled, setMfaEnabled] = useState(false);
    const [errors, setErrors] = useState({});
    const [touched, setTouched] = useState({});
    const [successMessage, setSuccessMessage] = useState('');

    const validatePassword = (password) => {
      const errors = [];
      if (password.length < 15) {
        errors.push('At least 15 characters');
      }
      if (password.length >= 15 && password.length <= 35) {
        if (!/[A-Z]/.test(password)) errors.push('1 uppercase letter');
        if (!/[a-z]/.test(password)) errors.push('1 lowercase letter');
        if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) errors.push('1 special character (not _)');
      }
      // 36+ characters have no additional requirements
      return errors;
    };

    const handlePasswordChange = () => {
      const newErrors = {};
      
      if (!currentPassword) newErrors.currentPassword = 'Current password is required';
      if (!newPassword) newErrors.newPassword = 'New password is required';
      
      const passwordErrors = validatePassword(newPassword);
      if (passwordErrors.length > 0) {
        newErrors.newPassword = 'Password must have: ' + passwordErrors.join(', ');
      }
      
      if (newPassword !== confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }

      if (Object.keys(newErrors).length === 0) {
        setSuccessMessage('Password changed successfully!');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setErrors({});
        setTouched({});
        setTimeout(() => setSuccessMessage(''), 3000);
      } else {
        setErrors(newErrors);
        setTouched({ currentPassword: true, newPassword: true, confirmPassword: true });
      }
    };

    const handleBlur = (field) => {
      setTouched({ ...touched, [field]: true });
      const newErrors = { ...errors };
      
      if (field === 'newPassword' && newPassword) {
        const passwordErrors = validatePassword(newPassword);
        if (passwordErrors.length > 0) {
          newErrors.newPassword = 'Password must have: ' + passwordErrors.join(', ');
        } else {
          delete newErrors.newPassword;
        }
      }
      
      if (field === 'confirmPassword' && confirmPassword) {
        if (newPassword !== confirmPassword) {
          newErrors.confirmPassword = 'Passwords do not match';
        } else {
          delete newErrors.confirmPassword;
        }
      }
      
      setErrors(newErrors);
    };

    const getPasswordStrength = (password) => {
      const errors = validatePassword(password);
      if (!password) return { strength: 0, color: 'bg-gray-600', label: '' };
      if (errors.length === 0) return { strength: 100, color: 'bg-green-500', label: 'Strong' };
      if (errors.length <= 2) return { strength: 66, color: 'bg-yellow-500', label: 'Medium' };
      return { strength: 33, color: 'bg-red-500', label: 'Weak' };
    };

    const passwordStrength = getPasswordStrength(newPassword);

    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 z-50">
        <div className="bg-gray-800 rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-3xl font-bold">Settings</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white text-3xl leading-none"
            >
              ×
            </button>
          </div>

          {successMessage && (
            <div className="bg-green-600 text-white p-3 rounded-lg mb-4">
              {successMessage}
            </div>
          )}

          <div className="space-y-8">
            {/* Change Password Section */}
            <div>
              <h3 className="text-2xl font-bold mb-4">Change Password</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-white text-sm font-medium mb-2 block">
                    Current Password <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => {
                      setCurrentPassword(e.target.value);
                      if (touched.currentPassword && errors.currentPassword) {
                        const newErrors = { ...errors };
                        delete newErrors.currentPassword;
                        setErrors(newErrors);
                      }
                    }}
                    onBlur={() => handleBlur('currentPassword')}
                    className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                      touched.currentPassword && errors.currentPassword ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                    }`}
                    placeholder="Enter current password"
                  />
                  {touched.currentPassword && errors.currentPassword && (
                    <p className="text-red-500 text-sm mt-1">{errors.currentPassword}</p>
                  )}
                </div>

                <div>
                  <label className="text-white text-sm font-medium mb-2 block">
                    New Password <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => {
                      setNewPassword(e.target.value);
                      if (touched.newPassword) {
                        handleBlur('newPassword');
                      }
                    }}
                    onBlur={() => handleBlur('newPassword')}
                    className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                      touched.newPassword && errors.newPassword ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                    }`}
                    placeholder="Enter new password"
                  />
                  {newPassword && (
                    <div className="mt-2">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-400">Password strength:</span>
                        <span className={`font-semibold ${passwordStrength.color.replace('bg-', 'text-')}`}>
                          {passwordStrength.label}
                        </span>
                      </div>
                      <div className="w-full bg-gray-600 rounded-full h-2">
                        <div
                          className={`${passwordStrength.color} h-2 rounded-full transition-all`}
                          style={{ width: `${passwordStrength.strength}%` }}
                        />
                      </div>
                    </div>
                  )}
                  {touched.newPassword && errors.newPassword && (
                    <p className="text-red-500 text-sm mt-1">{errors.newPassword}</p>
                  )}
                  <p className="text-gray-400 text-xs mt-1">
                    Must be 15+ characters. If 15-35 chars: 1 uppercase, 1 lowercase, 1 special char (not _). 36+ chars: no additional requirements
                  </p>
                </div>

                <div>
                  <label className="text-white text-sm font-medium mb-2 block">
                    Confirm New Password <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      if (touched.confirmPassword) {
                        handleBlur('confirmPassword');
                      }
                    }}
                    onBlur={() => handleBlur('confirmPassword')}
                    className={`w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 text-lg ${
                      touched.confirmPassword && errors.confirmPassword ? 'ring-2 ring-red-500' : 'focus:ring-green-500'
                    }`}
                    placeholder="Confirm new password"
                  />
                  {touched.confirmPassword && errors.confirmPassword && (
                    <p className="text-red-500 text-sm mt-1">{errors.confirmPassword}</p>
                  )}
                </div>

                <button
                  onClick={handlePasswordChange}
                  className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg transition-colors text-lg"
                >
                  Change Password
                </button>
              </div>
            </div>

            {/* MFA Section */}
            <div className="border-t border-gray-700 pt-6">
              <h3 className="text-2xl font-bold mb-4">Multi-Factor Authentication</h3>
              <div className="bg-gray-700 rounded-lg p-6">
                <div className="flex justify-between items-center">
                  <div className="flex-1">
                    <h4 className="font-semibold text-lg mb-1">Two-Factor Authentication (MFA)</h4>
                    <p className="text-gray-400 text-sm">
                      Add an extra layer of security to your account by requiring a verification code when logging in.
                    </p>
                  </div>
                  <button
                    onClick={() => setMfaEnabled(!mfaEnabled)}
                    className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ml-4 flex-shrink-0 ${
                      mfaEnabled ? 'bg-green-600' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                        mfaEnabled ? 'translate-x-7' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
                {mfaEnabled && (
                  <div className="mt-4 pt-4 border-t border-gray-600">
                    <p className="text-green-400 text-sm font-semibold mb-3">✓ MFA is enabled</p>
                    <div className="space-y-3">
                      <label className="text-white text-sm font-medium block">Verification Method</label>
                      <div className="space-y-2">
                        <label className="flex items-center space-x-3 p-3 bg-gray-600 rounded-lg cursor-pointer hover:bg-gray-550">
                          <input
                            type="radio"
                            name="mfaMethod"
                            defaultChecked
                            className="w-5 h-5 text-green-600 focus:ring-green-500"
                          />
                          <div>
                            <div className="font-semibold">Email Verification</div>
                            <div className="text-gray-400 text-sm">Receive codes at your registered email</div>
                          </div>
                        </label>
                        <label className="flex items-center space-x-3 p-3 bg-gray-600 rounded-lg cursor-pointer hover:bg-gray-550">
                          <input
                            type="radio"
                            name="mfaMethod"
                            className="w-5 h-5 text-green-600 focus:ring-green-500"
                          />
                          <div>
                            <div className="font-semibold">SMS Verification</div>
                            <div className="text-gray-400 text-sm">Receive codes via text message</div>
                          </div>
                        </label>
                      </div>
                      <div className="mt-3">
                        <label className="text-white text-sm font-medium mb-2 block">Phone Number (for SMS)</label>
                        <input
                          type="tel"
                          placeholder="+1 (555) 123-4567"
                          className="w-full bg-gray-600 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="mt-8 flex justify-end">
            <button
              onClick={onClose}
              className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-6 rounded-lg transition-colors text-lg"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Show Details Modal
  const ShowDetailsModal = ({ show, onClose }) => {
    const [isEditingSetlist, setIsEditingSetlist] = useState(false);
    const [songs, setSongs] = useState([
      'Do I Wanna Know?', 'Brianstorm', 'Crying Lightning', 'Teddy Picker', 'R U Mine?'
    ]);
    const [isRecording, setIsRecording] = useState(false);
    const [recordingProgress, setRecordingProgress] = useState(0);
    const [checkedIn, setCheckedIn] = useState(false);
    
    const friendsAtShow = friendsData.filter(f => f.atSameShow && f.status === 'friends');
    
    // Check if show is current (today or future)
    const showDate = new Date(show.date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const isCurrentOrFutureShow = showDate >= today;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 z-50">
        <div className="bg-gray-800 rounded-lg p-8 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div className="flex justify-between items-start mb-6">
            <div className="flex-1">
              <h2 className="text-4xl font-bold mb-2">{show.artist}</h2>
              <div className="flex items-center text-gray-400 mb-1">
                <MapPin className="w-5 h-5 mr-2" />
                <span className="text-lg">{show.venue}, {show.location}</span>
              </div>
              <div className="flex items-center text-gray-400">
                <Calendar className="w-5 h-5 mr-2" />
                <span className="text-lg">{new Date(show.date).toLocaleDateString()}</span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white text-2xl"
            >
              ×
            </button>
          </div>

          {/* Check-in and Friends Section - Only for Current/Future Shows */}
          {isCurrentOrFutureShow && (
            <div className="mb-6 space-y-3">
              <button
                onClick={() => setCheckedIn(!checkedIn)}
                className={`w-full font-bold py-3 px-4 rounded-lg transition-colors text-lg flex items-center justify-center space-x-2 ${
                  checkedIn 
                    ? 'bg-green-600 hover:bg-green-700' 
                    : 'bg-blue-600 hover:bg-blue-700'
                } text-white`}
              >
                {checkedIn ? (
                  <>
                    <span>✓</span>
                    <span>Checked In</span>
                  </>
                ) : (
                  <>
                    <MapPin className="w-5 h-5" />
                    <span>Check In to Show</span>
                  </>
                )}
              </button>

              {friendsAtShow.length > 0 && checkedIn && (
                <div className="bg-gradient-to-r from-purple-900 to-blue-900 bg-opacity-50 border border-purple-600 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <Users className="w-5 h-5 text-purple-400" />
                      <span className="font-semibold text-purple-200">
                        {friendsAtShow.length} {friendsAtShow.length === 1 ? 'Friend' : 'Friends'} at this show
                      </span>
                    </div>
                    <button
                      onClick={() => setShowChatModal(true)}
                      className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2"
                    >
                      <MessageSquare className="w-4 h-4" />
                      <span>Chat</span>
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {friendsAtShow.map(friend => (
                      <div key={friend.id} className="bg-purple-800 bg-opacity-50 px-3 py-1 rounded-full flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                        <span className="text-purple-100">{friend.username}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Chat Archive for Past Shows */}
          {!isCurrentOrFutureShow && chatMessages.length > 0 && (
            <div className="mb-6">
              <div className="bg-gray-700 border border-gray-600 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <MessageSquare className="w-5 h-5 text-blue-400" />
                    <span className="font-semibold">Show Chat Archive</span>
                  </div>
                  <button
                    onClick={() => setShowChatModal(true)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors text-sm"
                  >
                    View Messages
                  </button>
                </div>
                <p className="text-gray-400 text-sm">
                  {chatMessages.length} messages from you and your friends during this show
                </p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <Camera className="w-8 h-8 mx-auto mb-2 text-pink-500" />
              <div className="text-2xl font-bold">{show.photos}</div>
              <div className="text-gray-400 text-sm">Photos</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <Music className="w-8 h-8 mx-auto mb-2 text-orange-500" />
              <div className="text-2xl font-bold">{show.audio}</div>
              <div className="text-gray-400 text-sm">Audio Clips</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <MessageSquare className="w-8 h-8 mx-auto mb-2 text-yellow-500" />
              <div className="text-2xl font-bold">{show.comments}</div>
              <div className="text-gray-400 text-sm">Comments</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <List className="w-8 h-8 mx-auto mb-2 text-green-500" />
              <div className="text-2xl font-bold">{songs.length}</div>
              <div className="text-gray-400 text-sm">Songs</div>
            </div>
          </div>

          <div className="space-y-6">
            <div>
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-xl font-bold">Setlist</h3>
                <button
                  onClick={() => setIsEditingSetlist(!isEditingSetlist)}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  {isEditingSetlist ? 'Done Editing' : 'Edit Setlist'}
                </button>
              </div>
              
              {isEditingSetlist ? (
                <EditSetlistView 
                  songs={songs} 
                  setSongs={setSongs}
                  isRecording={isRecording}
                  setIsRecording={setIsRecording}
                  recordingProgress={recordingProgress}
                  setRecordingProgress={setRecordingProgress}
                />
              ) : (
                <div className="bg-gray-700 rounded-lg p-4">
                  <div className="space-y-2">
                    {songs.map((song, idx) => (
                      <div key={idx} className="flex items-center text-gray-300 py-2">
                        <span className="text-gray-500 mr-4 font-mono">{idx + 1}.</span>
                        <span className="text-lg">{song}</span>
                      </div>
                    ))}
                  </div>
                  {songs.length === 0 && (
                    <p className="text-gray-400 text-center py-4">No songs added yet. Click "Edit Setlist" to add songs.</p>
                  )}
                </div>
              )}
            </div>

            <div>
              <h3 className="text-xl font-bold mb-3">Photos</h3>
              <div className="grid grid-cols-3 gap-4">
                {[1, 2, 3, 4, 5, 6].map(i => (
                  <div key={i} className="bg-gray-700 rounded-lg aspect-square flex items-center justify-center">
                    <Camera className="w-12 h-12 text-gray-600" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Edit Setlist View Component
  const EditSetlistView = ({ songs, setSongs, isRecording, setIsRecording, recordingProgress, setRecordingProgress }) => {
    const [newSongName, setNewSongName] = useState('');
    const [showAddOptions, setShowAddOptions] = useState(false);
    const [identifiedSong, setIdentifiedSong] = useState(null);

    const handleAddManualSong = () => {
      if (newSongName.trim()) {
        setSongs([...songs, newSongName.trim()]);
        setNewSongName('');
        setShowAddOptions(false);
      }
    };

    const handleRecordSong = async () => {
      setIsRecording(true);
      setRecordingProgress(0);
      setIdentifiedSong(null);

      // Simulate recording progress
      const interval = setInterval(() => {
        setRecordingProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval);
            return 100;
          }
          return prev + 10;
        });
      }, 300);

      // Simulate Shazam API call after 3 seconds
      setTimeout(async () => {
        clearInterval(interval);
        setRecordingProgress(100);
        
        try {
          // Mock Shazam API call
          // In production: const response = await fetch('https://shazam.p.rapidapi.com/songs/v2/detect', {...})
          
          // Simulated result
          const mockResult = {
            title: "Fluorescent Adolescent",
            artist: "Arctic Monkeys"
          };
          
          setIdentifiedSong(mockResult);
          setIsRecording(false);
        } catch (error) {
          console.error('Error identifying song:', error);
          setIsRecording(false);
          alert('Could not identify song. Please try again or add manually.');
        }
      }, 3000);
    };

    const handleAddIdentifiedSong = () => {
      if (identifiedSong) {
        setSongs([...songs, identifiedSong.title]);
        setIdentifiedSong(null);
        setShowAddOptions(false);
      }
    };

    const handleDeleteSong = (index) => {
      setSongs(songs.filter((_, i) => i !== index));
    };

    const moveSongUp = (index) => {
      if (index > 0) {
        const newSongs = [...songs];
        [newSongs[index - 1], newSongs[index]] = [newSongs[index], newSongs[index - 1]];
        setSongs(newSongs);
      }
    };

    const moveSongDown = (index) => {
      if (index < songs.length - 1) {
        const newSongs = [...songs];
        [newSongs[index], newSongs[index + 1]] = [newSongs[index + 1], newSongs[index]];
        setSongs(newSongs);
      }
    };

    return (
      <div className="bg-gray-700 rounded-lg p-4">
        {/* Existing songs list */}
        <div className="space-y-2 mb-4">
          {songs.map((song, idx) => (
            <div key={idx} className="flex items-center justify-between bg-gray-750 rounded-lg p-3">
              <div className="flex items-center flex-1">
                <span className="text-gray-500 mr-4 font-mono font-bold">{idx + 1}.</span>
                <span className="text-lg text-gray-200">{song}</span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => moveSongUp(idx)}
                  disabled={idx === 0}
                  className="text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed p-2"
                >
                  ↑
                </button>
                <button
                  onClick={() => moveSongDown(idx)}
                  disabled={idx === songs.length - 1}
                  className="text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed p-2"
                >
                  ↓
                </button>
                <button
                  onClick={() => handleDeleteSong(idx)}
                  className="text-red-500 hover:text-red-400 p-2"
                >
                  ×
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Add song section */}
        {!showAddOptions ? (
          <button
            onClick={() => setShowAddOptions(true)}
            className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
          >
            <Plus className="w-5 h-5" />
            <span>Add Song</span>
          </button>
        ) : (
          <div className="bg-gray-800 rounded-lg p-4 space-y-4">
            <div className="flex justify-between items-center">
              <h4 className="font-semibold text-lg">Add Song</h4>
              <button
                onClick={() => {
                  setShowAddOptions(false);
                  setNewSongName('');
                  setIdentifiedSong(null);
                }}
                className="text-gray-400 hover:text-white"
              >
                Cancel
              </button>
            </div>

            {/* Manual entry */}
            <div>
              <label className="text-white text-sm font-medium mb-2 block">Enter Song Name</label>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={newSongName}
                  onChange={(e) => setNewSongName(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddManualSong()}
                  placeholder="Type song name..."
                  className="flex-1 bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-lg"
                />
                <button
                  onClick={handleAddManualSong}
                  disabled={!newSongName.trim()}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg transition-colors"
                >
                  Add
                </button>
              </div>
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-600"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-gray-800 text-gray-400">OR</span>
              </div>
            </div>

            {/* Shazam audio recognition */}
            <div>
              <label className="text-white text-sm font-medium mb-2 block">Identify Song (Shazam)</label>
              
              {!isRecording && !identifiedSong && (
                <button
                  onClick={handleRecordSong}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
                >
                  <Music className="w-5 h-5" />
                  <span>Record Song Snippet (30 sec)</span>
                </button>
              )}

              {isRecording && (
                <div className="space-y-3">
                  <div className="flex items-center justify-center space-x-3 py-4">
                    <div className="w-4 h-4 bg-red-500 rounded-full animate-pulse"></div>
                    <span className="text-lg font-semibold">Recording...</span>
                  </div>
                  <div className="w-full bg-gray-600 rounded-full h-3">
                    <div
                      className="bg-blue-500 h-3 rounded-full transition-all duration-300"
                      style={{ width: `${recordingProgress}%` }}
                    />
                  </div>
                  <p className="text-gray-400 text-sm text-center">
                    Hold your phone near the speaker. Identifying...
                  </p>
                </div>
              )}

              {identifiedSong && (
                <div className="bg-gray-700 rounded-lg p-4 space-y-3">
                  <div className="flex items-center space-x-3">
                    <div className="bg-green-600 w-12 h-12 rounded-full flex items-center justify-center">
                      <Music className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="font-bold text-lg">{identifiedSong.title}</div>
                      <div className="text-gray-400">{identifiedSong.artist}</div>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={handleAddIdentifiedSong}
                      className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition-colors"
                    >
                      Add to Setlist
                    </button>
                    <button
                      onClick={() => setIdentifiedSong(null)}
                      className="flex-1 bg-gray-600 hover:bg-gray-550 text-white font-bold py-2 px-4 rounded-lg transition-colors"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Auto-population info */}
        <div className="mt-4 p-4 bg-blue-900 bg-opacity-30 border border-blue-700 rounded-lg">
          <div className="flex items-start space-x-2">
            <div className="text-blue-400 mt-1">ℹ️</div>
            <div className="flex-1">
              <div className="text-blue-300 font-semibold mb-1">Automatic Setlist Updates</div>
              <p className="text-blue-200 text-sm">
                Our system automatically checks setlist.fm monthly for past shows and adds any missing songs to your setlist. 
                Songs you've added manually will never be overwritten.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Photos Modal
  const PhotosModal = ({ show, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-90 flex flex-col z-50">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-700 p-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">{show.artist} - Photos</h2>
            <p className="text-gray-400">{show.venue} • {new Date(show.date).toLocaleDateString()}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-3xl leading-none"
          >
            ×
          </button>
        </div>
      </div>

      {/* Photo Grid */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: show.photos }, (_, i) => (
            <div 
              key={i} 
              className="bg-gray-800 rounded-lg aspect-square flex items-center justify-center hover:bg-gray-700 transition-colors cursor-pointer group"
            >
              <div className="text-center">
                <Camera className="w-12 h-12 text-gray-600 group-hover:text-pink-500 mx-auto mb-2 transition-colors" />
                <span className="text-gray-500 text-sm">Photo {i + 1}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-900 border-t border-gray-700 p-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <span className="text-gray-400">{show.photos} photos</span>
          <button
            onClick={onClose}
            className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-6 rounded-lg transition-colors"
          >
            Back to Shows
          </button>
        </div>
      </div>
    </div>
  );

  // Audio Modal
  const AudioModal = ({ show, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-90 flex flex-col z-50">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-700 p-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">{show.artist} - Audio Clips</h2>
            <p className="text-gray-400">{show.venue} • {new Date(show.date).toLocaleDateString()}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-3xl leading-none"
          >
            ×
          </button>
        </div>
      </div>

      {/* Audio List */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto space-y-3">
          {Array.from({ length: show.audio }, (_, i) => (
            <div 
              key={i} 
              className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors"
            >
              <div className="flex items-center space-x-4">
                <div className="bg-orange-600 w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0">
                  <Music className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">Audio Clip {i + 1}</h3>
                  <p className="text-gray-400 text-sm">1:00 duration</p>
                </div>
                <button className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-full transition-colors">
                  Play
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-900 border-t border-gray-700 p-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <span className="text-gray-400">{show.audio} audio clips</span>
          <button
            onClick={onClose}
            className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-6 rounded-lg transition-colors"
          >
            Back to Shows
          </button>
        </div>
      </div>
    </div>
  );

  // Comments Modal
  const CommentsModal = ({ show, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-90 flex flex-col z-50">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-700 p-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">{show.artist} - Comments</h2>
            <p className="text-gray-400">{show.venue} • {new Date(show.date).toLocaleDateString()}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-3xl leading-none"
          >
            ×
          </button>
        </div>
      </div>

      {/* Comments List */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {Array.from({ length: show.comments }, (_, i) => (
            <div 
              key={i} 
              className="bg-gray-800 rounded-lg p-4"
            >
              <div className="flex items-start space-x-3">
                <MessageSquare className="w-6 h-6 text-yellow-500 flex-shrink-0 mt-1" />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-400 text-sm">
                      {new Date(show.date).toLocaleDateString()} at {new Date(show.date).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-gray-200">
                    This is a sample comment for the show. The energy was incredible and the crowd was amazing!
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-900 border-t border-gray-700 p-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <span className="text-gray-400">{show.comments} comments</span>
          <button
            onClick={onClose}
            className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-6 rounded-lg transition-colors"
          >
            Back to Shows
          </button>
        </div>
      </div>
    </div>
  );

  // Setlist Modal
  const SetlistModal = ({ show, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-90 flex flex-col z-50">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-700 p-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">{show.artist} - Setlist</h2>
            <p className="text-gray-400">{show.venue} • {new Date(show.date).toLocaleDateString()}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-3xl leading-none"
          >
            ×
          </button>
        </div>
      </div>

      {/* Setlist */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="space-y-3">
              {[
                'Do I Wanna Know?', 'Brianstorm', 'Crying Lightning', 'Teddy Picker', 
                'R U Mine?', '505', 'Fluorescent Adolescent', 'Snap Out of It',
                'Why\'d You Only Call Me When You\'re High?', 'Arabella', 'Cornerstone',
                'One Point Perspective', 'Four Out of Five', 'Tranquility Base Hotel & Casino'
              ].slice(0, show.songs).map((song, idx) => (
                <div 
                  key={idx} 
                  className="flex items-center py-3 px-4 bg-gray-750 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  <span className="text-green-500 mr-6 font-mono text-xl font-bold w-8">{idx + 1}</span>
                  <span className="text-lg text-gray-200">{song}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-900 border-t border-gray-700 p-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <span className="text-gray-400">{show.songs} songs</span>
          <button
            onClick={onClose}
            className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-6 rounded-lg transition-colors"
          >
            Back to Shows
          </button>
        </div>
      </div>
    </div>
  );

  // All Shows Modal
  const AllShowsModal = ({ onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-90 flex flex-col z-50">
      <div className="bg-gray-900 border-b border-gray-700 p-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">All Shows</h2>
            <p className="text-gray-400">{stats.shows} total shows</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-3xl leading-none">×</button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sampleShows.map(show => (
            <div key={show.id} className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors">
              <h3 className="text-xl font-bold mb-2">{show.artist}</h3>
              <p className="text-gray-400 text-sm mb-1">{show.venue}</p>
              <p className="text-gray-400 text-sm mb-3">{new Date(show.date).toLocaleDateString()}</p>
              <div className="flex justify-between text-sm">
                <span className="text-pink-500">📷 {show.photos}</span>
                <span className="text-orange-500">🎵 {show.audio}</span>
                <span className="text-yellow-500">💬 {show.comments}</span>
                <span className="text-green-500">📋 {show.songs}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-gray-900 border-t border-gray-700 p-4">
        <div className="max-w-6xl mx-auto flex justify-end">
          <button onClick={onClose} className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-6 rounded-lg transition-colors">
            Close
          </button>
        </div>
      </div>
    </div>
  );

  // All Artists Modal
  const AllArtistsModal = ({ onClose }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const filteredArtists = artistData.filter(artist => 
      artist.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
      <div className="fixed inset-0 bg-black bg-opacity-90 flex flex-col z-50">
        <div className="bg-gray-900 border-b border-gray-700 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h2 className="text-2xl font-bold">All Artists</h2>
                <p className="text-gray-400">{stats.artists} total artists</p>
              </div>
              <button onClick={onClose} className="text-gray-400 hover:text-white text-3xl leading-none">×</button>
            </div>
            <input
              type="text"
              placeholder="Search artists..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-lg"
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-4xl mx-auto space-y-3">
            {filteredArtists.map((artist, idx) => (
              <div key={idx} className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-xl font-bold">{artist.name}</h3>
                    <p className="text-gray-400 text-sm">Last seen: {new Date(artist.lastSeen).toLocaleDateString()}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-green-500">{artist.count}</div>
                    <div className="text-gray-400 text-sm">shows</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-gray-900 border-t border-gray-700 p-4">
          <div className="max-w-4xl mx-auto flex justify-end">
            <button onClick={onClose} className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-6 rounded-lg transition-colors">
              Close
            </button>
          </div>
        </div>
      </div>
    );
  };

  // All Venues Modal
  const AllVenuesModal = ({ onClose }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const filteredVenues = venueData.filter(venue => 
      venue.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      venue.location.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
      <div className="fixed inset-0 bg-black bg-opacity-90 flex flex-col z-50">
        <div className="bg-gray-900 border-b border-gray-700 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h2 className="text-2xl font-bold">All Venues</h2>
                <p className="text-gray-400">{stats.venues} total venues</p>
              </div>
              <button onClick={onClose} className="text-gray-400 hover:text-white text-3xl leading-none">×</button>
            </div>
            <input
              type="text"
              placeholder="Search venues..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-lg"
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-4xl mx-auto space-y-3">
            {filteredVenues.map((venue, idx) => (
              <div key={idx} className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-xl font-bold mb-1">{venue.name}</h3>
                    <p className="text-gray-400 flex items-center">
                      <MapPin className="w-4 h-4 mr-1" />
                      {venue.location}
                    </p>
                    <p className="text-gray-400 text-sm mt-1">Last visit: {new Date(venue.lastVisit).toLocaleDateString()}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-blue-500">{venue.count}</div>
                    <div className="text-gray-400 text-sm">visits</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-gray-900 border-t border-gray-700 p-4">
          <div className="max-w-4xl mx-auto flex justify-end">
            <button onClick={onClose} className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-6 rounded-lg transition-colors">
              Close
            </button>
          </div>
        </div>
      </div>
    );
  };

  // All Photos Modal
  const AllPhotosModal = ({ onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-90 flex flex-col z-50">
      <div className="bg-gray-900 border-b border-gray-700 p-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">All Photos</h2>
            <p className="text-gray-400">{stats.photos} total photos across all shows</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-3xl leading-none">×</button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-6xl mx-auto">
          {sampleShows.map(show => (
            <div key={show.id} className="mb-8">
              <h3 className="text-xl font-bold mb-3">{show.artist} - {new Date(show.date).toLocaleDateString()}</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {Array.from({ length: Math.min(show.photos, 6) }, (_, i) => (
                  <div key={i} className="bg-gray-800 rounded-lg aspect-square flex items-center justify-center hover:bg-gray-700 transition-colors cursor-pointer">
                    <Camera className="w-8 h-8 text-gray-600" />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-gray-900 border-t border-gray-700 p-4">
        <div className="max-w-6xl mx-auto flex justify-end">
          <button onClick={onClose} className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-6 rounded-lg transition-colors">
            Close
          </button>
        </div>
      </div>
    </div>
  );

  // All Audio Modal
  const AllAudioModal = ({ onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-90 flex flex-col z-50">
      <div className="bg-gray-900 border-b border-gray-700 p-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">All Audio Clips</h2>
            <p className="text-gray-400">{stats.audio} total audio clips</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-3xl leading-none">×</button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto">
          {sampleShows.map(show => (
            <div key={show.id} className="mb-6">
              <h3 className="text-xl font-bold mb-3">{show.artist} - {new Date(show.date).toLocaleDateString()}</h3>
              <div className="space-y-2">
                {Array.from({ length: Math.min(show.audio, 3) }, (_, i) => (
                  <div key={i} className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors">
                    <div className="flex items-center space-x-4">
                      <div className="bg-orange-600 w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0">
                        <Music className="w-5 h-5 text-white" />
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold">Audio Clip {i + 1}</h4>
                        <p className="text-gray-400 text-sm">1:00 duration</p>
                      </div>
                      <button className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-full transition-colors text-sm">
                        Play
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-gray-900 border-t border-gray-700 p-4">
        <div className="max-w-4xl mx-auto flex justify-end">
          <button onClick={onClose} className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-6 rounded-lg transition-colors">
            Close
          </button>
        </div>
      </div>
    </div>
  );

  // All Comments Modal
  const AllCommentsModal = ({ onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-90 flex flex-col z-50">
      <div className="bg-gray-900 border-b border-gray-700 p-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">All Comments</h2>
            <p className="text-gray-400">{stats.comments} total comments</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-3xl leading-none">×</button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {sampleShows.map(show => (
            <div key={show.id}>
              <div className="flex items-center space-x-2 mb-3">
                <h3 className="text-lg font-bold">{show.artist}</h3>
                <span className="text-gray-500">•</span>
                <span className="text-gray-400 text-sm">{new Date(show.date).toLocaleDateString()}</span>
              </div>
              {Array.from({ length: show.comments }, (_, i) => (
                <div key={i} className="bg-gray-800 rounded-lg p-4 mb-3">
                  <div className="flex items-start space-x-3">
                    <MessageSquare className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-1" />
                    <div className="flex-1">
                      <p className="text-gray-200 mb-2">
                        Amazing show! The energy was incredible and the setlist was perfect. Can't wait to see them again!
                      </p>
                      <span className="text-gray-500 text-xs">
                        {new Date(show.date).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="bg-gray-900 border-t border-gray-700 p-4">
        <div className="max-w-4xl mx-auto flex justify-end">
          <button onClick={onClose} className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-6 rounded-lg transition-colors">
            Close
          </button>
        </div>
      </div>
    </div>
  );

  // Friends Modal
  const FriendsModal = ({ onClose }) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState('friends'); // 'friends' or 'requests'

    const friends = friendsData.filter(f => f.status === 'friends');
    const requests = friendsData.filter(f => f.status === 'pending');

    return (
      <div className="fixed inset-0 bg-black bg-opacity-90 flex flex-col z-50">
        <div className="bg-gray-900 border-b border-gray-700 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">Friends</h2>
              <button onClick={onClose} className="text-gray-400 hover:text-white text-3xl leading-none">×</button>
            </div>

            {/* Tabs */}
            <div className="flex space-x-4 mb-4">
              <button
                onClick={() => setActiveTab('friends')}
                className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                  activeTab === 'friends' 
                    ? 'bg-green-600 text-white' 
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                Friends ({friends.length})
              </button>
              <button
                onClick={() => setActiveTab('requests')}
                className={`px-4 py-2 rounded-lg font-semibold transition-colors relative ${
                  activeTab === 'requests' 
                    ? 'bg-green-600 text-white' 
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                Requests ({requests.length})
                {requests.length > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {requests.length}
                  </span>
                )}
              </button>
            </div>

            {/* Search */}
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search users or add friends..."
              className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-lg"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-4xl mx-auto space-y-3">
            {activeTab === 'friends' && friends.map(friend => (
              <div key={friend.id} className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors">
                <div className="flex justify-between items-center">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center">
                      <User className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="text-lg font-bold">{friend.username}</h3>
                        {friend.atSameShow && (
                          <span className="bg-purple-600 text-white text-xs px-2 py-1 rounded-full flex items-center space-x-1">
                            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                            <span>At show</span>
                          </span>
                        )}
                      </div>
                      <p className="text-gray-400 text-sm">{friend.lastSeen}</p>
                      <p className="text-gray-500 text-xs">{friend.mutualFriends} mutual friends</p>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    {friend.atSameShow && (
                      <button
                        onClick={() => setShowChatModal(true)}
                        className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center space-x-2"
                      >
                        <MessageSquare className="w-4 h-4" />
                        <span>Chat</span>
                      </button>
                    )}
                    <button className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors">
                      View Profile
                    </button>
                  </div>
                </div>
              </div>
            ))}

            {activeTab === 'requests' && requests.map(friend => (
              <div key={friend.id} className="bg-gray-800 rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-gray-600 rounded-full flex items-center justify-center">
                      <User className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold">{friend.username}</h3>
                      <p className="text-gray-400 text-sm">Sent you a friend request</p>
                      <p className="text-gray-500 text-xs">{friend.mutualFriends} mutual friends</p>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors">
                      Accept
                    </button>
                    <button className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors">
                      Decline
                    </button>
                  </div>
                </div>
              </div>
            ))}

            {activeTab === 'friends' && friends.length === 0 && (
              <div className="text-center py-12">
                <User className="w-16 h-16 mx-auto text-gray-600 mb-4" />
                <p className="text-gray-400 text-lg">No friends yet</p>
                <p className="text-gray-500">Search for users to add as friends!</p>
              </div>
            )}
          </div>
        </div>

        <div className="bg-gray-900 border-t border-gray-700 p-4">
          <div className="max-w-4xl mx-auto flex justify-end">
            <button onClick={onClose} className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-6 rounded-lg transition-colors">
              Close
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Chat Modal
  const ChatModal = ({ onClose, isArchive = false }) => {
    const [newMessage, setNewMessage] = useState('');
    const messagesEndRef = React.useRef(null);

    const scrollToBottom = () => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    React.useEffect(() => {
      scrollToBottom();
    }, [chatMessages]);

    const handleSendMessage = () => {
      if (newMessage.trim() && !isArchive) {
        setChatMessages([...chatMessages, {
          id: chatMessages.length + 1,
          username: 'You',
          message: newMessage,
          timestamp: new Date()
        }]);
        setNewMessage('');
      }
    };

    const formatTime = (date) => {
      const now = new Date();
      const diff = now - date;
      const minutes = Math.floor(diff / 60000);
      
      if (minutes < 1) return 'Just now';
      if (minutes < 60) return `${minutes}m ago`;
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-90 flex flex-col z-50">
        {/* Header */}
        <div className="bg-gray-900 border-b border-gray-700 p-4">
          <div className="max-w-4xl mx-auto flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">
                {isArchive ? 'Show Chat Archive' : 'Show Chat'}
              </h2>
              <p className="text-gray-400">Arctic Monkeys - Madison Square Garden</p>
              {!isArchive && (
                <div className="flex items-center space-x-2 mt-1">
                  <div className="flex -space-x-2">
                    {friendsData.filter(f => f.atSameShow).map(friend => (
                      <div key={friend.id} className="w-6 h-6 bg-green-600 rounded-full border-2 border-gray-900 flex items-center justify-center">
                        <span className="text-xs">👤</span>
                      </div>
                    ))}
                  </div>
                  <span className="text-green-400 text-sm">
                    {friendsData.filter(f => f.atSameShow).length} friends online
                  </span>
                </div>
              )}
              {isArchive && (
                <p className="text-gray-500 text-sm mt-1">
                  Messages from this past show (read-only)
                </p>
              )}
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-white text-3xl leading-none">×</button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 bg-gradient-to-b from-gray-900 to-black">
          <div className="max-w-4xl mx-auto space-y-4">
            {chatMessages.map(msg => (
              <div key={msg.id} className={`flex ${msg.username === 'You' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs lg:max-w-md ${
                  msg.username === 'You' 
                    ? 'bg-green-600' 
                    : 'bg-gray-800'
                } rounded-lg p-3`}>
                  {msg.username !== 'You' && (
                    <div className="text-sm font-semibold text-green-400 mb-1">{msg.username}</div>
                  )}
                  <div className="text-white">{msg.message}</div>
                  <div className="text-xs text-gray-400 mt-1">{formatTime(msg.timestamp)}</div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Message Input - Only for active shows */}
        {!isArchive ? (
          <div className="bg-gray-900 border-t border-gray-700 p-4">
            <div className="max-w-4xl mx-auto flex space-x-3">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Type a message..."
                className="flex-1 bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-lg"
              />
              <button
                onClick={handleSendMessage}
                disabled={!newMessage.trim()}
                className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg transition-colors font-bold"
              >
                Send
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-gray-900 border-t border-gray-700 p-4">
            <div className="max-w-4xl mx-auto flex justify-center">
              <p className="text-gray-400 text-sm">This is a chat archive from a past show</p>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div>
      {!isLoggedIn ? (
        <>
          <LoginPage />
          {showRegisterModal && <RegisterModal onClose={() => setShowRegisterModal(false)} />}
          {showForgotPasswordModal && <ForgotPasswordModal onClose={() => setShowForgotPasswordModal(false)} />}
        </>
      ) : (
        <Dashboard />
      )}
    </div>
  );
};

export default ShareMyShowsDemo;