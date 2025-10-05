"""
Unit tests for Spotify API service
Tests all programmatic logic before development completion
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

from src.services.spotify_service import SpotifyService, SpotifyRateLimiter
from src.services.exceptions import APIException, RateLimitException, AuthenticationException


class TestSpotifyRateLimiter:
    """Test rate limiting functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_under_limit(self):
        """Test that rate limiter allows requests under the limit"""
        limiter = SpotifyRateLimiter(max_requests=5, window_seconds=60)
        
        # Make 5 requests quickly
        for _ in range(5):
            await limiter.acquire()
        
        # Should not raise any exception
        assert len(limiter.requests) == 5
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_requests_over_limit(self):
        """Test that rate limiter blocks requests over the limit"""
        limiter = SpotifyRateLimiter(max_requests=2, window_seconds=1)
        
        # Make 2 requests
        await limiter.acquire()
        await limiter.acquire()
        
        # Third request should be delayed
        start_time = datetime.utcnow()
        await limiter.acquire()
        end_time = datetime.utcnow()
        
        # Should have waited at least some time
        assert (end_time - start_time).total_seconds() >= 0.5
    
    @pytest.mark.asyncio
    async def test_rate_limiter_cleans_old_requests(self):
        """Test that rate limiter cleans up old requests"""
        limiter = SpotifyRateLimiter(max_requests=2, window_seconds=1)
        
        # Add old request
        old_time = datetime.utcnow() - timedelta(seconds=2)
        limiter.requests.append(old_time)
        
        # Make a new request
        await limiter.acquire()
        
        # Old request should be cleaned up
        assert len(limiter.requests) == 1


class TestSpotifyService:
    """Test Spotify API service functionality"""
    
    @pytest.fixture
    def spotify_service(self):
        """Create Spotify service instance for testing"""
        return SpotifyService()
    
    @pytest.fixture
    def mock_response_data(self):
        """Mock response data for Spotify API"""
        return {
            "items": [
                {
                    "id": "test_playlist_id",
                    "name": "Test Playlist",
                    "description": "A test playlist",
                    "tracks": {"total": 10},
                    "owner": {"display_name": "Test User", "id": "test_user"},
                    "public": True,
                    "collaborative": False,
                    "external_urls": {"spotify": "https://spotify.com/playlist/test"},
                    "images": [{"url": "https://example.com/image.jpg", "height": 300, "width": 300}]
                }
            ],
            "next": None
        }
    
    @pytest.mark.asyncio
    async def test_get_user_playlists_success(self, spotify_service, mock_response_data):
        """Test successful retrieval of user playlists"""
        with patch.object(spotify_service, '_make_request', AsyncMock(return_value=mock_response_data)):
            playlists = await spotify_service.get_user_playlists("test_token")
            
            assert len(playlists) == 1
            playlist = playlists[0]
            assert playlist["id"] == "test_playlist_id"
            assert playlist["name"] == "Test Playlist"
            assert playlist["track_count"] == 10
            assert playlist["owner"] == "Test User"
    
    @pytest.mark.asyncio
    async def test_get_playlist_tracks_success(self, spotify_service):
        """Test successful retrieval of playlist tracks"""
        mock_tracks_data = {
            "items": [
                {
                    "track": {
                        "type": "track",
                        "id": "test_track_id",
                        "name": "Test Track",
                        "artists": [{"name": "Test Artist"}],
                        "album": {"name": "Test Album"},
                        "duration_ms": 180000,
                        "external_ids": {"isrc": "TEST123456"},
                        "preview_url": "https://example.com/preview.mp3",
                        "external_urls": {"spotify": "https://spotify.com/track/test"}
                    }
                }
            ],
            "next": None
        }
        
        with patch.object(spotify_service, '_make_request', AsyncMock(return_value=mock_tracks_data)):
            tracks = await spotify_service.get_playlist_tracks("test_playlist_id", "test_token")
            
            assert len(tracks) == 1
            track = tracks[0]
            assert track["id"] == "test_track_id"
            assert track["name"] == "Test Track"
            assert track["artist"] == "Test Artist"
            assert track["album"] == "Test Album"
            assert track["isrc"] == "TEST123456"
    
    @pytest.mark.asyncio
    async def test_get_playlist_tracks_filters_non_tracks(self, spotify_service):
        """Test that non-track items are filtered out"""
        mock_tracks_data = {
            "items": [
                {
                    "track": {
                        "type": "episode",  # This should be filtered out
                        "id": "episode_id",
                        "name": "Test Episode"
                    }
                },
                {
                    "track": None  # This should be filtered out
                },
                {
                    "track": {
                        "type": "track",
                        "id": "test_track_id",
                        "name": "Test Track",
                        "artists": [{"name": "Test Artist"}],
                        "album": {"name": "Test Album"},
                        "duration_ms": 180000,
                        "external_ids": {},
                        "external_urls": {}
                    }
                }
            ],
            "next": None
        }
        
        with patch.object(spotify_service, '_make_request', AsyncMock(return_value=mock_tracks_data)):
            tracks = await spotify_service.get_playlist_tracks("test_playlist_id", "test_token")
            
            # Only the valid track should be returned
            assert len(tracks) == 1
            assert tracks[0]["id"] == "test_track_id"
    
    @pytest.mark.asyncio
    async def test_search_track_success(self, spotify_service):
        """Test successful track search"""
        mock_search_data = {
            "tracks": {
                "items": [
                    {
                        "id": "search_track_id",
                        "name": "Search Track",
                        "artists": [{"name": "Search Artist"}],
                        "album": {"name": "Search Album"},
                        "duration_ms": 200000,
                        "external_ids": {"isrc": "SEARCH123"},
                        "preview_url": "https://example.com/search.mp3",
                        "external_urls": {"spotify": "https://spotify.com/track/search"}
                    }
                ]
            }
        }
        
        with patch.object(spotify_service, '_make_request', AsyncMock(return_value=mock_search_data)):
            tracks = await spotify_service.search_track("test query", "test_token")
            
            assert len(tracks) == 1
            track = tracks[0]
            assert track["id"] == "search_track_id"
            assert track["name"] == "Search Track"
    
    @pytest.mark.asyncio
    async def test_make_request_handles_rate_limit(self, spotify_service):
        """Test that _make_request handles rate limiting properly"""
        mock_response_429 = Mock()
        mock_response_429.status = 429
        mock_response_429.headers = {'Retry-After': '1'}
        
        mock_response_200 = Mock()
        mock_response_200.status = 200
        mock_response_200.ok = True
        mock_response_200.json = AsyncMock(return_value={"success": True})
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = mock_session_class.return_value.__aenter__.return_value
            mock_session.request.return_value.__aenter__.side_effect = [
                mock_response_429,  # First call returns rate limit
                mock_response_200   # Second call succeeds
            ]
            
            with patch('asyncio.sleep', AsyncMock()) as mock_sleep:
                result = await spotify_service._make_request(
                    "GET", 
                    "https://api.spotify.com/v1/test", 
                    {"Authorization": "Bearer test"}
                )
                
                # Should have slept for 1 second
                mock_sleep.assert_called_once_with(1)
                assert result == {"success": True}
    
    @pytest.mark.asyncio
    async def test_make_request_handles_api_error(self, spotify_service):
        """Test that _make_request handles API errors properly"""
        mock_response = Mock()
        mock_response.status = 400
        mock_response.ok = False
        mock_response.text = AsyncMock(return_value="Bad Request")
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = mock_session_class.return_value.__aenter__.return_value
            mock_session.request.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(Exception, match="Spotify API error: 400"):
                await spotify_service._make_request(
                    "GET", 
                    "https://api.spotify.com/v1/test", 
                    {"Authorization": "Bearer test"}
                )
    
    @pytest.mark.asyncio
    async def test_get_client_credentials_token_success(self, spotify_service):
        """Test successful client credentials token retrieval"""
        mock_token_response = {
            "access_token": "test_client_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value=mock_token_response)
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = mock_session_class.return_value.__aenter__.return_value
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            with patch.dict('src.core.config.settings.__dict__', {
                'SPOTIFY_CLIENT_ID': 'test_client_id',
                'SPOTIFY_CLIENT_SECRET': 'test_client_secret'
            }):
                token = await spotify_service.get_client_credentials_token()
                assert token == "test_client_token"
    
    @pytest.mark.asyncio
    async def test_get_client_credentials_token_missing_credentials(self, spotify_service):
        """Test client credentials token failure with missing credentials"""
        with patch.dict('src.core.config.settings.__dict__', {
            'SPOTIFY_CLIENT_ID': '',
            'SPOTIFY_CLIENT_SECRET': ''
        }):
            with pytest.raises(ValueError, match="Spotify client credentials not configured"):
                await spotify_service.get_client_credentials_token()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])