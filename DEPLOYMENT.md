# Production Deployment Guide

## 🎯 Overview
This guide is for **YOU as the developer** to deploy PlaylistSync for **your users**. Users don't need Spotify developer accounts - they just sign in with their regular Spotify accounts.

## 🔧 Developer Setup (One-Time)

### 1. Create Spotify App (Developer Only)
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Create new app:
   - **Name**: `PlaylistSync`
   - **Description**: `Sync playlists between Spotify and Apple Music`
   - **Website**: `https://your-domain.com`
   - **Redirect URI**: `https://your-domain.com/api/auth/spotify/callback`

### 2. Get API Credentials
- **Client ID**: Copy from dashboard
- **Client Secret**: Click "Show Client Secret"

### 3. Configure Environment
```bash
# Update .env with your credentials
SPOTIFY_CLIENT_ID=your_actual_client_id_here
SPOTIFY_CLIENT_SECRET=your_actual_secret_here

# For production deployment
ENVIRONMENT=production
ALLOWED_ORIGINS=["https://your-domain.com"]
```

### 4. Update Redirect URI for Production
- Development: `https://localhost:8000/api/auth/spotify/callback`
- Production: `https://your-domain.com/api/auth/spotify/callback`

## 🚀 Deployment Options

### Option 1: Docker Deployment
```bash
# Build for production
docker-compose -f docker-compose.prod.yml up -d

# Or with custom environment
docker-compose up -d
```

### Option 2: Cloud Deployment
- Deploy backend to Heroku, AWS, Google Cloud, etc.
- Deploy frontend to Netlify, Vercel, etc.
- Update CORS settings in backend
- Update API_URL in frontend

## 👤 User Flow (No Developer Account Needed)
1. User visits your website
2. Clicks "Connect with Spotify"
3. Redirected to Spotify OAuth (using YOUR app credentials)
4. User signs in with their regular Spotify account
5. User grants permissions to YOUR app
6. User can now sync their playlists

## 🔒 Security Notes
- Your Spotify credentials are server-side only
- Users never see your API keys
- OAuth tokens are per-user and temporary
- All communication encrypted with TLS 1.3

## 📋 Production Checklist
- [ ] Real domain configured
- [ ] SSL certificate installed
- [ ] Spotify app redirect URI updated
- [ ] Environment variables secured
- [ ] CORS configured for production domain
- [ ] Rate limiting configured
- [ ] Monitoring and logging enabled

## 🛠️ For Development/Testing
Use the demo mode in the app to test without real credentials during development.