# OAuth Setup Guide for Multi-User Deployment

## Overview
This guide explains how to configure Spotify and Apple Music OAuth applications to allow **ANY USER** to sign in to your hosted service.

## 🎵 Spotify OAuth Setup

### 1. Create Spotify App
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click "Create app"
3. Fill in details:
   - **App name**: `Your Service Name - Playlist Sync`
   - **App description**: `Sync playlists between Spotify and Apple Music`
   - **Website**: `https://your-domain.com` (your production URL)
   - **Redirect URI**: `https://your-domain.com/auth/spotify/callback`
   - **Which API/SDKs are you planning to use?**: Web API

### 2. Configure App Settings
1. Go to your app settings
2. Add **Redirect URIs**:
   - Production: `https://your-domain.com/auth/spotify/callback`  
   - Development: `http://localhost:8000/auth/spotify/callback`
3. **IMPORTANT**: Set app to **PUBLIC** mode:
   - In app settings, request "Quota Extension"
   - Submit for review with these details:
     - **Use case**: "Multi-user playlist synchronization service"
     - **User benefit**: "Allows users to sync playlists between Spotify and Apple Music"
     - **Data usage**: "Read user playlists only, no data storage of personal information"

### 3. Required Scopes
Your app requests these scopes (already configured in code):
- `user-read-private` - Read user profile
- `user-read-email` - Read user email  
- `playlist-read-private` - Read private playlists
- `playlist-read-collaborative` - Read collaborative playlists

## 🍎 Apple Music Setup

### 1. Apple Developer Account Required
- You need a paid Apple Developer account ($99/year)
- Cannot test Apple Music integration without this

### 2. Create MusicKit Identifier
1. Go to [Apple Developer Portal](https://developer.apple.com/account/resources/identifiers/list/musicId)
2. Create new **MusicKit Identifier**:
   - **Bundle ID**: `com.yourcompany.playlist-sync`
   - **Description**: `Playlist Sync Service`

### 3. Create MusicKit Key
1. Go to **Keys** section
2. Create new key with **MusicKit** service enabled
3. Download the `.p8` key file
4. Note the **Key ID** and **Team ID**

### 4. Configure Web Domains (Important!)
1. In MusicKit settings, add **Authorized Domains**:
   - Production: `your-domain.com`
   - Development: `localhost:3000`, `localhost:8000`

## 🔧 Environment Configuration

Update your `.env` file with the credentials:

```bash
# Spotify Configuration (from Spotify Dashboard)
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Apple Music Configuration (from Apple Developer)
APPLE_MUSIC_KEY_ID=your_key_id
APPLE_MUSIC_TEAM_ID=your_team_id
APPLE_MUSIC_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
your_private_key_content_here
-----END PRIVATE KEY-----

# Production URLs
FRONTEND_URL=https://your-domain.com
BACKEND_URL=https://api.your-domain.com
SPOTIFY_REDIRECT_URI=https://api.your-domain.com/auth/spotify/callback
```

## 🌐 Production Deployment

### 1. Domain Setup
- **Frontend**: `https://your-domain.com` 
- **API**: `https://api.your-domain.com`
- **SSL Certificate**: Required (Let's Encrypt or similar)

### 2. CORS Configuration
Update `ALLOWED_ORIGINS` in config:
```python
ALLOWED_ORIGINS = [
    "https://your-domain.com",
    "http://localhost:3000"  # Keep for development
]
```

### 3. Redirect URI Updates
Both services need to point to your production domain:
- **Spotify**: `https://api.your-domain.com/auth/spotify/callback`
- **Apple Music**: Authorize `your-domain.com` domain

## 🧪 Testing Multi-User Flow

### Test with Different Users
1. Open incognito/private browser windows
2. Have different people test with their accounts
3. Verify OAuth flows work independently
4. Check token isolation between users

### Common Issues & Fixes

**"App not approved for public use" (Spotify)**
- Solution: Submit app for quota extension review
- Takes 1-2 weeks for approval
- Provide clear use case description

**"Unauthorized domain" (Apple Music)**  
- Solution: Add your domain to MusicKit authorized domains
- Include both www and non-www versions

**CORS errors**
- Solution: Update `ALLOWED_ORIGINS` to include your frontend domain

**Redirect URI mismatch**
- Solution: Ensure exact match between OAuth app config and environment variables

## 🔒 Security Considerations

### Production Checklist
- ✅ Use HTTPS everywhere
- ✅ TLS 1.3 enforcement
- ✅ Secure JWT secret key (32+ random characters)
- ✅ Rate limiting enabled
- ✅ No secrets in client-side code
- ✅ Proper CORS configuration
- ✅ Session timeout implemented

### User Privacy
- Only request minimum required OAuth scopes
- Don't store user tokens longer than necessary  
- Implement proper session cleanup
- Allow users to disconnect/revoke access

## 🚀 Quick Start for Demo

For a **working demo right now** on localhost:

1. **Create Spotify App** with redirect URI: `http://localhost:8000/auth/spotify/callback`
2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Add your Spotify credentials to .env
   ```
3. **Start services**:
   ```bash
   # Backend
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   
   # Frontend  
   cd web-frontend && npm start
   ```
4. **Test OAuth**: Visit `http://localhost:3000`, click "Connect Spotify"

The service will work for you and anyone else who accesses your local IP address on your network.

## 🌟 Making it Public

To make it work for **ANYONE** on the internet:

1. **Deploy to cloud** (Vercel, Railway, DigitalOcean, etc.)
2. **Get SSL certificate** 
3. **Update OAuth redirect URIs** to production URLs
4. **Submit Spotify app for public approval**
5. **Configure Apple Music domain authorization**

Once deployed with proper OAuth setup, any user can visit your site and authenticate with their own Spotify/Apple Music accounts!