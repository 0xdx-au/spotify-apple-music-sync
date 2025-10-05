"""
Authentication service for OAuth flows with Spotify and Apple Music
Handles user sessions, token management, and profile data
"""

import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import base64

from ..core.config import settings
from ..core.security import security_manager
from .spotify_service import SpotifyService
from .apple_music_service import AppleMusicService

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling OAuth authentication flows"""
    
    def __init__(self):
        self.spotify_service = SpotifyService()
        self.apple_music_service = AppleMusicService()
        # In production, use Redis or database for session storage
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.oauth_states: Dict[str, Dict[str, Any]] = {}
    
    def generate_oauth_url(self, provider: str, redirect_uri: str) -> Dict[str, str]:
        """Generate OAuth authorization URL for the given provider"""
        state = str(uuid.uuid4())
        
        if provider == 'spotify':
            scopes = [
                'user-read-private',
                'user-read-email',
                'playlist-read-private',
                'playlist-read-collaborative'
            ]
            
            auth_url = (
                f"https://accounts.spotify.com/authorize?"
                f"client_id={settings.SPOTIFY_CLIENT_ID}&"
                f"response_type=code&"
                f"redirect_uri={redirect_uri}&"
                f"scope={'+'.join(scopes)}&"
                f"state={state}&"
                f"show_dialog=true"
            )
        
        elif provider == 'apple-music':
            # Apple Music uses MusicKit JS for web authentication
            # For now, return a placeholder URL
            auth_url = f"https://beta.music.apple.com/authorize?state={state}"
        
        else:
            raise ValueError(f"Unsupported OAuth provider: {provider}")
        
        # Store state for validation
        self.oauth_states[state] = {
            "provider": provider,
            "redirect_uri": redirect_uri,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }
        
        return {
            "auth_url": auth_url,
            "state": state
        }
    
    async def handle_oauth_callback(self, provider: str, code: str, state: str) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for tokens"""
        # Validate state
        if state not in self.oauth_states:
            raise ValueError("Invalid OAuth state")
        
        oauth_state = self.oauth_states[state]
        if oauth_state["expires_at"] < datetime.utcnow():
            raise ValueError("OAuth state expired")
        
        if oauth_state["provider"] != provider:
            raise ValueError("Provider mismatch")
        
        # Clean up state
        del self.oauth_states[state]
        
        if provider == 'spotify':
            return await self._handle_spotify_callback(code, oauth_state["redirect_uri"])
        elif provider == 'apple-music':
            return await self._handle_apple_music_callback(code, oauth_state["redirect_uri"])
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def _handle_spotify_callback(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle Spotify OAuth callback"""
        try:
            # Exchange code for tokens
            token_url = "https://accounts.spotify.com/api/token"
            
            credentials = base64.b64encode(
                f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}".encode()
            ).decode()
            
            headers = {
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, headers=headers, data=data) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error(f"Spotify token exchange failed: {error_text}")
                        raise Exception("Failed to exchange code for token")
                    
                    token_data = await response.json()
            
            # Get user profile
            access_token = token_data["access_token"]
            user_profile = await self._get_spotify_user_profile(access_token)
            
            # Create user session
            user_id = f"spotify_{user_profile['id']}"
            session_data = {
                "user_id": user_id,
                "provider": "spotify",
                "spotify_token": access_token,
                "spotify_refresh_token": token_data.get("refresh_token"),
                "apple_music_token": None,
                "profile": user_profile,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600))
            }
            
            self.user_sessions[user_id] = session_data
            
            # Create JWT token for frontend
            jwt_payload = {
                "user_id": user_id,
                "spotify_connected": True,
                "apple_music_connected": False
            }
            
            jwt_token = security_manager.create_access_token(jwt_payload)
            
            return {
                "token": jwt_token,
                "user": {
                    "id": user_id,
                    "displayName": user_profile.get("display_name", user_profile["id"]),
                    "email": user_profile.get("email"),
                    "spotifyConnected": True,
                    "appleMusicConnected": False,
                    "avatar": user_profile.get("images", [{}])[0].get("url") if user_profile.get("images") else None
                }
            }
        
        except Exception as e:
            logger.error(f"Spotify OAuth callback failed: {e}")
            raise
    
    async def _handle_apple_music_callback(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle Apple Music OAuth callback (placeholder)"""
        # Apple Music OAuth is more complex and typically done client-side
        # This is a placeholder for the server-side implementation
        raise NotImplementedError("Apple Music OAuth not yet implemented")
    
    async def _get_spotify_user_profile(self, access_token: str) -> Dict[str, Any]:
        """Get Spotify user profile"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.spotify.com/v1/me", headers=headers) as response:
                if not response.ok:
                    raise Exception("Failed to get user profile")
                return await response.json()
    
    def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user session data"""
        session = self.user_sessions.get(user_id)
        if session and session["expires_at"] > datetime.utcnow():
            return session
        elif session:
            # Session expired, clean up
            del self.user_sessions[user_id]
        return None
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from session"""
        session = self.get_user_session(user_id)
        if session:
            profile = session["profile"].copy()
            return {
                "id": user_id,
                "displayName": profile.get("display_name", profile.get("id", "User")),
                "email": profile.get("email"),
                "spotifyConnected": bool(session.get("spotify_token")),
                "appleMusicConnected": bool(session.get("apple_music_token")),
                "avatar": profile.get("images", [{}])[0].get("url") if profile.get("images") else None
            }
        return None
    
    async def connect_additional_service(self, user_id: str, provider: str, access_token: str) -> Dict[str, Any]:
        """Connect an additional service to existing user account"""
        session = self.get_user_session(user_id)
        if not session:
            raise ValueError("User session not found")
        
        if provider == "spotify":
            session["spotify_token"] = access_token
            user_profile = await self._get_spotify_user_profile(access_token)
            # Merge profile data if needed
        elif provider == "apple-music":
            session["apple_music_token"] = access_token
            # Get Apple Music profile if needed
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        return self.get_user_profile(user_id)
    
    def disconnect_service(self, user_id: str, provider: str) -> Dict[str, Any]:
        """Disconnect a service from user account"""
        session = self.get_user_session(user_id)
        if not session:
            raise ValueError("User session not found")
        
        if provider == "spotify":
            session["spotify_token"] = None
            session["spotify_refresh_token"] = None
        elif provider == "apple-music":
            session["apple_music_token"] = None
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        return self.get_user_profile(user_id)