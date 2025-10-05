"""
Spotify Web API service implementation
Handles authentication, playlist retrieval, and track information
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import base64
import json

from ..core.config import settings, TLS_CONFIG
from ..models.playlist import TrackResponse, PlaylistResponse

logger = logging.getLogger(__name__)

class SpotifyRateLimiter:
    """Rate limiter for Spotify API calls"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    async def acquire(self):
        """Acquire permission to make a request"""
        now = datetime.utcnow()
        # Remove old requests outside the window
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < timedelta(seconds=self.window_seconds)]
        
        if len(self.requests) >= self.max_requests:
            # Wait until we can make another request
            oldest_request = min(self.requests)
            wait_time = (oldest_request + timedelta(seconds=self.window_seconds) - now).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        self.requests.append(now)

class SpotifyService:
    """Service for interacting with Spotify Web API"""
    
    def __init__(self):
        self.base_url = "https://api.spotify.com/v1"
        self.auth_url = "https://accounts.spotify.com/api/token"
        self.rate_limiter = SpotifyRateLimiter(settings.SPOTIFY_RATE_LIMIT, 60)
    
    async def _make_request(
        self, 
        method: str, 
        url: str, 
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a rate-limited request to Spotify API"""
        await self.rate_limiter.acquire()
        
        ssl_context = aiohttp.TCPConnector(ssl_context=TLS_CONFIG)
        async with aiohttp.ClientSession(connector=ssl_context) as session:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data
            ) as response:
                if response.status == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 1))
                    logger.warning(f"Rate limited by Spotify, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(method, url, headers, params, data)
                
                if not response.ok:
                    error_text = await response.text()
                    logger.error(f"Spotify API error {response.status}: {error_text}")
                    raise Exception(f"Spotify API error: {response.status}")
                
                return await response.json()
    
    async def get_user_playlists(self, access_token: str) -> List[Dict[str, Any]]:
        """Get user's Spotify playlists"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        playlists = []
        url = f"{self.base_url}/me/playlists"
        
        while url:
            response = await self._make_request("GET", url, headers, {"limit": 50})
            
            for item in response.get("items", []):
                playlist_data = {
                    "id": item["id"],
                    "name": item["name"],
                    "description": item.get("description", ""),
                    "track_count": item["tracks"]["total"],
                    "owner": item["owner"]["display_name"] or item["owner"]["id"],
                    "public": item["public"],
                    "collaborative": item["collaborative"],
                    "external_urls": item.get("external_urls", {}),
                    "images": item.get("images", [])
                }
                playlists.append(playlist_data)
            
            url = response.get("next")
        
        return playlists
    
    async def get_playlist_tracks(self, playlist_id: str, access_token: str) -> List[Dict[str, Any]]:
        """Get tracks from a Spotify playlist"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        tracks = []
        url = f"{self.base_url}/playlists/{playlist_id}/tracks"
        
        while url:
            response = await self._make_request("GET", url, headers, {"limit": 50})
            
            for item in response.get("items", []):
                if not item.get("track") or item["track"]["type"] != "track":
                    continue  # Skip non-track items
                
                track = item["track"]
                track_data = {
                    "id": track["id"],
                    "name": track["name"],
                    "artist": ", ".join([artist["name"] for artist in track["artists"]]),
                    "album": track["album"]["name"],
                    "duration_ms": track["duration_ms"],
                    "isrc": track.get("external_ids", {}).get("isrc"),
                    "preview_url": track.get("preview_url"),
                    "external_urls": track.get("external_urls", {})
                }
                tracks.append(track_data)
            
            url = response.get("next")
        
        return tracks
    
    async def search_track(
        self, 
        query: str, 
        access_token: str, 
        limit: int = 1
    ) -> List[Dict[str, Any]]:
        """Search for tracks on Spotify"""
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "q": query,
            "type": "track",
            "limit": limit
        }
        
        response = await self._make_request("GET", f"{self.base_url}/search", headers, params)
        tracks = []
        
        for track in response.get("tracks", {}).get("items", []):
            track_data = {
                "id": track["id"],
                "name": track["name"],
                "artist": ", ".join([artist["name"] for artist in track["artists"]]),
                "album": track["album"]["name"],
                "duration_ms": track["duration_ms"],
                "isrc": track.get("external_ids", {}).get("isrc"),
                "preview_url": track.get("preview_url"),
                "external_urls": track.get("external_urls", {})
            }
            tracks.append(track_data)
        
        return tracks
    
    async def get_client_credentials_token(self) -> str:
        """Get client credentials token for public API access"""
        if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
            raise ValueError("Spotify client credentials not configured")
        
        credentials = base64.b64encode(
            f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}".encode()
        ).decode()
        
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {"grant_type": "client_credentials"}
        
        ssl_context = aiohttp.TCPConnector(ssl_context=TLS_CONFIG)
        async with aiohttp.ClientSession(connector=ssl_context) as session:
            async with session.post(self.auth_url, headers=headers, data=data) as response:
                if not response.ok:
                    error_text = await response.text()
                    logger.error(f"Spotify auth error: {error_text}")
                    raise Exception("Failed to get Spotify client credentials token")
                
                token_data = await response.json()
                return token_data["access_token"]