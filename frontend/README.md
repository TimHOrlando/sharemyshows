# ShareMyShows Frontend

Next.js 14 frontend for ShareMyShows - a social concert documentation platform.

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **Authentication:** JWT (stored in localStorage + cookies)

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend server running on http://localhost:5000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env.local
```

Edit `.env.local` and set the backend API URL:
```
NEXT_PUBLIC_API_URL=http://localhost:5000/api
```

3. Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Features

### Authentication System

- **User Registration** (`/register`)
  - Username, email, password validation
  - Optional full name field
  - MFA support (email verification)

- **User Login** (`/login`)
  - Email and password authentication
  - MFA verification flow
  - JWT token management

- **MFA Verification** (`/verify-mfa`)
  - 6-digit code input
  - Code resend functionality
  - 10-minute expiration

- **Protected Routes**
  - Automatic redirect to login for unauthenticated users
  - Loading states during authentication check

- **Dashboard** (`/dashboard`)
  - User profile information
  - MFA status indicator
  - Quick actions (placeholder for future features)

### Authentication Context

The app uses React Context (`AuthContext`) to manage authentication state globally:
- User profile data
- Login/logout functions
- Registration with MFA support
- Token management

### API Integration

All API calls go through the centralized `api` client (`lib/api.ts`):
- Automatic JWT token attachment
- Request/response interceptors
- Automatic redirect on 401 errors
- Cookie support for JWT

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout with AuthProvider
│   ├── page.tsx            # Landing page (redirects if authenticated)
│   ├── login/
│   │   └── page.tsx        # Login page
│   ├── register/
│   │   └── page.tsx        # Registration page
│   ├── verify-mfa/
│   │   └── page.tsx        # MFA verification page
│   └── dashboard/
│       └── page.tsx        # Protected dashboard
├── components/
│   ├── Navbar.tsx          # Navigation bar with logout
│   └── ProtectedRoute.tsx  # HOC for protected pages
├── contexts/
│   └── AuthContext.tsx     # Authentication context provider
├── lib/
│   ├── api.ts              # Axios instance with interceptors
│   ├── auth.ts             # Authentication service functions
│   └── types.ts            # TypeScript type definitions
└── .env.local              # Environment variables
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Authentication Flow

### Registration Flow

1. User fills out registration form
2. Frontend validates input (username length, email format, password match)
3. POST to `/api/auth/register`
4. If MFA required → redirect to `/verify-mfa`
5. If MFA not required → redirect to `/dashboard`

### Login Flow

1. User enters email and password
2. Frontend validates input
3. POST to `/api/auth/login`
4. If MFA required → redirect to `/verify-mfa`
5. If MFA not required → store token, redirect to `/dashboard`

### MFA Verification Flow

1. User receives 6-digit code via email
2. User enters code on `/verify-mfa` page
3. POST to `/api/auth/verify-mfa`
4. On success → store token, redirect to `/dashboard`
5. User can resend code if needed

### Logout Flow

1. User clicks "Logout" in navbar
2. POST to `/api/auth/logout`
3. Clear localStorage token
4. Redirect to `/login`

## API Endpoints Used

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/verify-mfa` - Verify MFA code
- `POST /api/auth/resend-mfa` - Resend MFA code
- `GET /api/auth/profile` - Get current user profile
- `POST /api/auth/logout` - Logout user

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:5000/api` |

## CORS Configuration

The backend must be configured to allow requests from the frontend origin:
- Development: `http://localhost:3000`
- Production: Your production domain

## Security Features

- JWT tokens stored in localStorage
- Cookie support for additional security
- Automatic token cleanup on 401 errors
- Protected routes with authentication checks
- Input validation on all forms
- HTTPS required in production (JWT_COOKIE_SECURE)

## Troubleshooting

### "Failed to load user" error
- Ensure backend is running on http://localhost:5000
- Check that CORS is properly configured in backend
- Verify JWT token is valid (check localStorage)

### MFA code not received
- Check spam folder
- Verify email configuration in backend `.env`
- Ensure `MAIL_PASSWORD` uses Gmail app password
- Check backend logs for email sending errors

### Redirect loop on login
- Clear browser localStorage
- Ensure backend is returning correct response format
- Check browser console for errors
