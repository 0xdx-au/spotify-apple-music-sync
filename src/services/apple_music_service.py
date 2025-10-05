"""
Apple Music API service implementation
Handles authentication, playlist creation, and track search with comprehensive error handling
"""

import asyncio
import aiohttp
import logging
import jwt
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json

from ..core.config import settings, TLS_CONFIG
from ..models.playlist import TrackResponse, PlaylistResponse
from .exceptions import APIException, RateLimitException, AuthenticationException, TrackNotFoundError

logger = logging.getLogger(__name__)

class AppleMusicRateLimiter:
    """Rate limiter for Apple Music API calls"""
    
    def __init__(self, max_requests: int = 333, window_seconds: int = 60):
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
                logger.warning(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
        
        self.requests.append(now)

class AppleMusicService:
    """Service for interacting with Apple Music API"""
    
    def __init__(self):
        self.base_url = "https://api.music.apple.com/v1"
        self.rate_limiter = AppleMusicRateLimiter(settings.APPLE_MUSIC_RATE_LIMIT, 60)
        self._developer_token = None
        self._token_expiry = None
    
    def _generate_developer_token(self) -> str:
        """Generate JWT token for Apple Music API authentication"""
        if not all([settings.APPLE_MUSIC_KEY_ID, settings.APPLE_MUSIC_TEAM_ID, settings.APPLE_MUSIC_PRIVATE_KEY]):
            raise AuthenticationException("Apple Music API credentials not configured")
        
        try:
            # JWT payload
            payload = {
                'iss': settings.APPLE_MUSIC_TEAM_ID,
                'iat': int(datetime.utcnow().timestamp()),
                'exp': int((datetime.utcnow() + timedelta(hours=6)).timestamp()),
                'aud': 'appstoreconnect-v1'
            }
            
            # JWT header
            header = {
                'alg': 'ES256',
                'kid': settings.APPLE_MUSIC_KEY_ID
            }
            
            # Generate token
            token = jwt.encode(
                payload, 
                settings.APPLE_MUSIC_PRIVATE_KEY, 
                algorithm='ES256',
                headers=header
            )
            
            return token
        except Exception as e:
            logger.error(f"Failed to generate Apple Music developer token: {e}")
            raise AuthenticationException(f"Failed to generate Apple Music token: {str(e)}")
    
    def _get_developer_token(self) -> str:
        """Get valid developer token, generating if necessary"""
        now = datetime.utcnow()
        
        if self._developer_token and self._token_expiry and now < self._token_expiry:
            return self._developer_token
        
        self._developer_token = self._generate_developer_token()
        self._token_expiry = now + timedelta(hours=5, minutes=30)  # Refresh 30 mins before expiry
        
        return self._developer_token
    
    async def _make_request(
        self, 
        method: str, 
        url: str, 
        user_token: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a rate-limited request to Apple Music API with comprehensive error handling"""
        await self.rate_limiter.acquire()
        
        headers = {
            "Authorization": f"Bearer {self._get_developer_token()}",
            "Content-Type": "application/json"
        }
        
        if user_token:
            headers["Music-User-Token"] = user_token
        
        try:
            ssl_context = aiohttp.TCPConnector(ssl_context=TLS_CONFIG)
            async with aiohttp.ClientSession(connector=ssl_context) as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=data
                ) as response:
                    # Handle rate limiting
                    if response.status == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited by Apple Music API, waiting {retry_after} seconds")
                        raise RateLimitException(f"Rate limited, retry after {retry_after} seconds", retry_after)
                    
                    # Handle authentication errors
                    if response.status == 401:
                        error_text = await response.text()
                        logger.error(f"Apple Music authentication error: {error_text}")
                        # Try to regenerate token once
                        self._developer_token = None
                        headers["Authorization"] = f"Bearer {self._get_developer_token()}"
                        # Retry once with new token
                        async with session.request(
                            method=method,
                            url=url,
                            headers=headers,
                            params=params,
                            json=data
                        ) as retry_response:
                            if retry_response.status == 401:
                                raise AuthenticationException("Apple Music authentication failed after token refresh")
                            response = retry_response
                    
                    # Handle other client errors
                    if 400 <= response.status < 500:
                        error_text = await response.text()
                        logger.error(f"Apple Music client error {response.status}: {error_text}")
                        raise APIException(f"Apple Music API client error: {response.status}", response.status)
                    
                    # Handle server errors with retry
                    if response.status >= 500:
                        error_text = await response.text()
                        logger.error(f"Apple Music server error {response.status}: {error_text}")
                        raise APIException(f"Apple Music API server error: {response.status}", response.status)
                    
                    if not response.ok:
                        error_text = await response.text()
                        logger.error(f"Apple Music API error {response.status}: {error_text}")
                        raise APIException(f"Apple Music API error: {response.status}", response.status)
                    
                    return await response.json()
                    
        except aiohttp.ClientError as e:
            logger.error(f"Apple Music API network error: {e}")
            raise APIException(f"Network error connecting to Apple Music API: {str(e)}")
        except asyncio.TimeoutError:
            logger.error("Apple Music API request timeout")
            raise APIException("Apple Music API request timeout")
    
    async def search_track(
        self, 
        artist: str, 
        title: str, 
        album: Optional[str] = None,
        isrc: Optional[str] = None,
        user_token: Optional[str] = None,
        country: str = "us"
    ) -> Optional[Dict[str, Any]]:
        """Search for a track on Apple Music with fallback strategies"""
        
        # Strategy 1: Search by ISRC if available
        if isrc:
            try:
                params = {
                    "term": f"isrc:{isrc}",
                    "types": "songs",
                    "limit": 1
                }
                
                response = await self._make_request("GET", f"{self.base_url}/catalog/{country}/search", user_token, params)
                
                if response.get("results", {}).get("songs", {}).get("data"):
                    track = response["results"]["songs"]["data"][0]
                    return self._format_track_response(track)
                    
            except Exception as e:
                logger.warning(f"ISRC search failed for {isrc}: {e}")
        
        # Strategy 2: Search by artist and title
        try:
            search_term = f"{artist} {title}".strip()
            params = {
                "term": search_term,
                "types": "songs",
                "limit": 10  # Get more results to find best match
            }
            
            response = await self._make_request("GET", f"{self.base_url}/catalog/{country}/search", user_token, params)
            
            songs = response.get("results", {}).get("songs", {}).get("data", [])
            
            if songs:
                # Find best match based on similarity
                best_match = self._find_best_match(songs, artist, title, album)
                if best_match:
                    return self._format_track_response(best_match)
        
        except Exception as e:
            logger.warning(f"Artist/title search failed for '{artist} - {title}': {e}")
        
        # Strategy 3: Simplified search (artist only or title only)
        for simplified_term in [artist, title]:
            if not simplified_term:
                continue
                
            try:
                params = {
                    "term": simplified_term,
                    "types": "songs",
                    "limit": 10
                }
                
                response = await self._make_request("GET", f"{self.base_url}/catalog/{country}/search", user_token, params)
                
                songs = response.get("results", {}).get("songs", {}).get("data", [])
                
                if songs:
                    best_match = self._find_best_match(songs, artist, title, album)
                    if best_match:
                        return self._format_track_response(best_match)
                        
            except Exception as e:
                logger.warning(f"Simplified search failed for '{simplified_term}': {e}")
        
        # No match found
        logger.info(f"No match found on Apple Music for '{artist} - {title}'")
        raise TrackNotFoundError(f"Track not found: {artist} - {title}")
    
    def _find_best_match(
        self, 
        songs: List[Dict], 
        target_artist: str, 
        target_title: str, 
        target_album: Optional[str] = None
    ) -> Optional[Dict]:
        """Find the best matching song from search results"""
        from difflib import SequenceMatcher
        
        best_match = None
        best_score = 0.0
        
        for song in songs:
            attrs = song.get("attributes", {})
            song_artist = attrs.get("artistName", "").lower()
            song_title = attrs.get("name", "").lower()
            song_album = attrs.get("albumName", "").lower()
            
            # Calculate similarity scores
            artist_score = SequenceMatcher(None, target_artist.lower(), song_artist).ratio()
            title_score = SequenceMatcher(None, target_title.lower(), song_title).ratio()
            
            # Weight: title is most important, then artist
            total_score = (title_score * 0.6) + (artist_score * 0.4)
            
            # Bonus for album match
            if target_album and song_album:
                album_score = SequenceMatcher(None, target_album.lower(), song_album).ratio()
                total_score += album_score * 0.2
            
            # Minimum threshold for consideration
            if total_score > 0.7 and total_score > best_score:
                best_score = total_score
                best_match = song
        
        return best_match
    
    def _format_track_response(self, track: Dict[str, Any]) -> Dict[str, Any]:
        """Format Apple Music track response to standard format"""
        attrs = track.get("attributes", {})
        return {
            "id": track["id"],
            "name": attrs.get("name", ""),
            "artist": attrs.get("artistName", ""),
            "album": attrs.get("albumName", ""),
            "duration_ms": attrs.get("durationInMillis", 0),
            "isrc": attrs.get("isrc"),
            "preview_url": attrs.get("previews", [{}])[0].get("url") if attrs.get("previews") else None,
            "external_urls": {"apple_music": attrs.get("url", "")}
        }
    
    async def create_playlist(
        self, 
        name: str, 
        description: Optional[str] = None,
        user_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new playlist on Apple Music"""
        if not user_token:
            raise AuthenticationException("User token required to create playlists")
        
        playlist_data = {
            "data": [
                {
                    "type": "library-playlists",
                    "attributes": {
                        "name": name,
                        "description": description or ""
                    }
                }
            ]
        }
        
        try:
            response = await self._make_request(
                "POST", 
                f"{self.base_url}/me/library/playlists", 
                user_token, 
                data=playlist_data
            )
            
            if response.get("data") and len(response["data"]) > 0:
                return response["data"][0]
            else:
                raise APIException("Failed to create playlist: No data returned")
                
        except Exception as e:
            logger.error(f"Failed to create Apple Music playlist '{name}': {e}")
            raise
    
    async def add_tracks_to_playlist(
        self, 
        playlist_id: str, 
        track_ids: List[str],
        user_token: Optional[str] = None
    ) -> bool:
        """Add tracks to an Apple Music playlist"""
        if not user_token:
            raise AuthenticationException("User token required to modify playlists")
        
        if not track_ids:
            return True
        
        # Apple Music API has limits on batch operations
        batch_size = 25
        
        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i:i + batch_size]
            
            track_data = {
                "data": [
                    {
                        "id": track_id,
                        "type": "songs"
                    } for track_id in batch
                ]
            }
            
            try:
                await self._make_request(
                    "POST",
                    f"{self.base_url}/me/library/playlists/{playlist_id}/tracks",
                    user_token,
                    data=track_data
                )
                
                logger.info(f"Added {len(batch)} tracks to playlist {playlist_id}")
                
            except Exception as e:
                logger.error(f"Failed to add tracks to playlist {playlist_id}: {e}")
                raise
        
        return True