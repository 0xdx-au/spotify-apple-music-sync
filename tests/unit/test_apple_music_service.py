"""
Unit tests for Apple Music API service
Tests track matching algorithms and error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from src.services.apple_music_service import AppleMusicService, AppleMusicRateLimiter
from src.services.exceptions import (
    APIException, 
    RateLimitException, 
    AuthenticationException, 
    TrackNotFoundError
)


class TestAppleMusicRateLimiter:
    """Test Apple Music rate limiting functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_under_limit(self):
        """Test rate limiter allows requests under limit"""
        limiter = AppleMusicRateLimiter(max_requests=10, window_seconds=60)
        
        for _ in range(10):
            await limiter.acquire()
        
        assert len(limiter.requests) == 10
    
    @pytest.mark.asyncio
    async def test_rate_limiter_waits_when_limit_exceeded(self):
        """Test rate limiter waits when limit is exceeded"""
        limiter = AppleMusicRateLimiter(max_requests=2, window_seconds=1)
        
        # Make 2 requests
        await limiter.acquire()
        await limiter.acquire()
        
        # Third request should wait
        start_time = datetime.utcnow()
        await limiter.acquire()
        end_time = datetime.utcnow()
        
        assert (end_time - start_time).total_seconds() >= 0.5


class TestAppleMusicService:
    """Test Apple Music API service functionality"""
    
    @pytest.fixture
    def apple_music_service(self):
        """Create Apple Music service instance for testing"""
        return AppleMusicService()
    
    @pytest.fixture
    def mock_jwt_token(self):
        """Mock JWT token for Apple Music API"""
        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"
    
    @pytest.mark.asyncio
    async def test_search_track_by_isrc_success(self, apple_music_service):
        """Test successful track search by ISRC"""
        mock_search_response = {
            "results": {
                "songs": {
                    "data": [
                        {
                            "id": "apple_track_id",
                            "attributes": {
                                "name": "Test Track",
                                "artistName": "Test Artist",
                                "albumName": "Test Album",
                                "durationInMillis": 180000,
                                "isrc": "TEST123456",
                                "previews": [{"url": "https://example.com/preview.m4a"}],
                                "url": "https://music.apple.com/track/test"
                            }
                        }
                    ]
                }
            }
        }
        
        with patch.object(apple_music_service, '_make_request', AsyncMock(return_value=mock_search_response)):
            result = await apple_music_service.search_track(
                artist="Test Artist",
                title="Test Track",
                isrc="TEST123456"
            )
            
            assert result is not None
            assert result["id"] == "apple_track_id"
            assert result["name"] == "Test Track"
            assert result["artist"] == "Test Artist"
            assert result["isrc"] == "TEST123456"
    
    @pytest.mark.asyncio
    async def test_search_track_by_artist_title_success(self, apple_music_service):
        """Test successful track search by artist and title"""
        mock_search_response = {
            "results": {
                "songs": {
                    "data": [
                        {
                            "id": "apple_track_id",
                            "attributes": {
                                "name": "Test Track",
                                "artistName": "Test Artist",
                                "albumName": "Test Album",
                                "durationInMillis": 180000,
                                "url": "https://music.apple.com/track/test"
                            }
                        }
                    ]
                }
            }
        }
        
        with patch.object(apple_music_service, '_make_request', AsyncMock(return_value=mock_search_response)):
            result = await apple_music_service.search_track(
                artist="Test Artist",
                title="Test Track"
            )
            
            assert result is not None
            assert result["id"] == "apple_track_id"
            assert result["name"] == "Test Track"
    
    @pytest.mark.asyncio
    async def test_search_track_not_found(self, apple_music_service):
        """Test track search when no match is found"""
        # Mock empty search responses for all strategies
        empty_response = {
            "results": {
                "songs": {
                    "data": []
                }
            }
        }
        
        with patch.object(apple_music_service, '_make_request', AsyncMock(return_value=empty_response)):
            with pytest.raises(TrackNotFoundError):
                await apple_music_service.search_track(
                    artist="Nonexistent Artist",
                    title="Nonexistent Track"
                )
    
    def test_find_best_match_exact_match(self, apple_music_service):
        """Test best match finding with exact match"""
        songs = [
            {
                "id": "exact_match",
                "attributes": {
                    "name": "Test Track",
                    "artistName": "Test Artist",
                    "albumName": "Test Album"
                }
            },
            {
                "id": "partial_match",
                "attributes": {
                    "name": "Test Track (Remix)",
                    "artistName": "Test Artist",
                    "albumName": "Test Album"
                }
            }
        ]
        
        best_match = apple_music_service._find_best_match(
            songs, "Test Artist", "Test Track", "Test Album"
        )
        
        assert best_match is not None
        assert best_match["id"] == "exact_match"
    
    def test_find_best_match_no_good_match(self, apple_music_service):
        """Test best match finding when no good match exists"""
        songs = [
            {
                "id": "poor_match",
                "attributes": {
                    "name": "Completely Different Song",
                    "artistName": "Different Artist",
                    "albumName": "Different Album"
                }
            }
        ]
        
        best_match = apple_music_service._find_best_match(
            songs, "Test Artist", "Test Track", "Test Album"
        )
        
        # Should return None for poor matches (below 0.7 threshold)
        assert best_match is None
    
    def test_find_best_match_partial_match(self, apple_music_service):
        """Test best match finding with partial match"""
        songs = [
            {
                "id": "partial_match",
                "attributes": {
                    "name": "Test Track",
                    "artistName": "Test Artist feat. Someone",
                    "albumName": "Test Album (Deluxe)"
                }
            }
        ]
        
        best_match = apple_music_service._find_best_match(
            songs, "Test Artist", "Test Track", "Test Album"
        )
        
        assert best_match is not None
        assert best_match["id"] == "partial_match"
    
    @pytest.mark.asyncio
    async def test_create_playlist_success(self, apple_music_service):
        """Test successful playlist creation"""
        mock_playlist_response = {
            "data": [
                {
                    "id": "new_playlist_id",
                    "type": "library-playlists",
                    "attributes": {
                        "name": "Test Playlist",
                        "description": "A test playlist"
                    }
                }
            ]
        }
        
        with patch.object(apple_music_service, '_make_request', AsyncMock(return_value=mock_playlist_response)):
            result = await apple_music_service.create_playlist(
                name="Test Playlist",
                description="A test playlist",
                user_token="test_user_token"
            )
            
            assert result["id"] == "new_playlist_id"
            assert result["attributes"]["name"] == "Test Playlist"
    
    @pytest.mark.asyncio
    async def test_create_playlist_no_user_token(self, apple_music_service):
        """Test playlist creation failure without user token"""
        with pytest.raises(AuthenticationException):
            await apple_music_service.create_playlist(
                name="Test Playlist",
                user_token=None
            )
    
    @pytest.mark.asyncio
    async def test_add_tracks_to_playlist_success(self, apple_music_service):
        """Test successful addition of tracks to playlist"""
        track_ids = ["track1", "track2", "track3"]
        
        with patch.object(apple_music_service, '_make_request', AsyncMock()) as mock_request:
            result = await apple_music_service.add_tracks_to_playlist(
                playlist_id="test_playlist",
                track_ids=track_ids,
                user_token="test_user_token"
            )
            
            assert result is True
            # Should have been called once (all tracks fit in one batch)
            assert mock_request.call_count == 1
    
    @pytest.mark.asyncio
    async def test_add_tracks_to_playlist_batch_processing(self, apple_music_service):
        """Test batch processing for large track lists"""
        # Create 50 track IDs (should be split into 2 batches of 25)
        track_ids = [f"track{i}" for i in range(50)]
        
        with patch.object(apple_music_service, '_make_request', AsyncMock()) as mock_request:
            result = await apple_music_service.add_tracks_to_playlist(
                playlist_id="test_playlist",
                track_ids=track_ids,
                user_token="test_user_token"
            )
            
            assert result is True
            # Should have been called twice (2 batches of 25)
            assert mock_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_add_tracks_to_playlist_no_user_token(self, apple_music_service):
        """Test adding tracks to playlist without user token"""
        with pytest.raises(AuthenticationException):
            await apple_music_service.add_tracks_to_playlist(
                playlist_id="test_playlist",
                track_ids=["track1"],
                user_token=None
            )
    
    @pytest.mark.asyncio
    async def test_make_request_handles_rate_limit(self, apple_music_service):
        """Test rate limit handling in _make_request"""
        mock_response_429 = Mock()
        mock_response_429.status = 429
        mock_response_429.headers = {'Retry-After': '2'}
        
        with patch.object(apple_music_service, '_get_developer_token', return_value="test_token"):
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = mock_session_class.return_value.__aenter__.return_value
                mock_session.request.return_value.__aenter__.return_value = mock_response_429
                
                with pytest.raises(RateLimitException) as exc_info:
                    await apple_music_service._make_request(
                        "GET",
                        "https://api.music.apple.com/v1/test"
                    )
                
                assert exc_info.value.retry_after == 2
    
    @pytest.mark.asyncio
    async def test_make_request_handles_auth_error(self, apple_music_service):
        """Test authentication error handling in _make_request"""
        mock_response_401 = Mock()
        mock_response_401.status = 401
        mock_response_401.text = AsyncMock(return_value="Unauthorized")
        
        with patch.object(apple_music_service, '_get_developer_token', return_value="test_token"):
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = mock_session_class.return_value.__aenter__.return_value
                # First call returns 401, retry also returns 401
                mock_session.request.return_value.__aenter__.side_effect = [
                    mock_response_401,
                    mock_response_401
                ]
                
                with pytest.raises(AuthenticationException):
                    await apple_music_service._make_request(
                        "GET",
                        "https://api.music.apple.com/v1/test"
                    )
    
    def test_format_track_response(self, apple_music_service):
        """Test track response formatting"""
        apple_music_track = {
            "id": "apple_track_id",
            "attributes": {
                "name": "Test Track",
                "artistName": "Test Artist",
                "albumName": "Test Album",
                "durationInMillis": 180000,
                "isrc": "TEST123456",
                "previews": [{"url": "https://example.com/preview.m4a"}],
                "url": "https://music.apple.com/track/test"
            }
        }
        
        formatted = apple_music_service._format_track_response(apple_music_track)
        
        assert formatted["id"] == "apple_track_id"
        assert formatted["name"] == "Test Track"
        assert formatted["artist"] == "Test Artist"
        assert formatted["album"] == "Test Album"
        assert formatted["duration_ms"] == 180000
        assert formatted["isrc"] == "TEST123456"
        assert formatted["preview_url"] == "https://example.com/preview.m4a"
        assert formatted["external_urls"]["apple_music"] == "https://music.apple.com/track/test"
    
    @pytest.mark.asyncio
    async def test_developer_token_generation_missing_config(self, apple_music_service):
        """Test developer token generation with missing configuration"""
        with patch.dict('src.core.config.settings.__dict__', {
            'APPLE_MUSIC_KEY_ID': '',
            'APPLE_MUSIC_TEAM_ID': '',
            'APPLE_MUSIC_PRIVATE_KEY': ''
        }):
            with pytest.raises(AuthenticationException):
                apple_music_service._generate_developer_token()
    
    @pytest.mark.asyncio
    async def test_developer_token_caching(self, apple_music_service):
        """Test developer token caching mechanism"""
        mock_token = "cached_token"
        
        with patch.object(apple_music_service, '_generate_developer_token', return_value=mock_token) as mock_generate:
            # First call should generate token
            token1 = apple_music_service._get_developer_token()
            
            # Second call should use cached token
            token2 = apple_music_service._get_developer_token()
            
            assert token1 == token2 == mock_token
            # Should only generate once due to caching
            assert mock_generate.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])