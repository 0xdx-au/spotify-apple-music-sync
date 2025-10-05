"""
Demo service for testing the application without real API credentials
Provides mock data and simulated OAuth flow for development/testing
"""

import uuid
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from ..core.security import security_manager

logger = logging.getLogger(__name__)

class DemoService:
    """Service providing demo/mock functionality for testing"""
    
    def __init__(self):
        self.demo_users = {}
        self.demo_playlists = [
            {
                "id": "demo_playlist_1",
                "name": "My Awesome Mix",
                "description": "A great collection of songs",
                "track_count": 42,
                "owner": "demo_user",
                "public": True,
                "collaborative": False,
                "external_urls": {"spotify": "https://open.spotify.com/playlist/demo1"},
                "images": [{"url": "https://via.placeholder.com/300x300/1db954/ffffff?text=Playlist+1"}]
            },
            {
                "id": "demo_playlist_2", 
                "name": "Chill Vibes",
                "description": "Perfect for relaxing",
                "track_count": 28,
                "owner": "demo_user",
                "public": False,
                "collaborative": True,
                "external_urls": {"spotify": "https://open.spotify.com/playlist/demo2"},
                "images": [{"url": "https://via.placeholder.com/300x300/ff6b6b/ffffff?text=Playlist+2"}]
            },
            {
                "id": "demo_playlist_3",
                "name": "Workout Energy",
                "description": "High energy tracks for exercise",
                "track_count": 35,
                "owner": "demo_user",
                "public": True,
                "collaborative": False,
                "external_urls": {"spotify": "https://open.spotify.com/playlist/demo3"},
                "images": [{"url": "https://via.placeholder.com/300x300/9c27b0/ffffff?text=Playlist+3"}]
            },
            {
                "id": "demo_playlist_4",
                "name": "Study Focus",
                "description": "Instrumental music for concentration",
                "track_count": 52,
                "owner": "demo_user",
                "public": False,
                "collaborative": False,
                "external_urls": {"spotify": "https://open.spotify.com/playlist/demo4"},
                "images": [{"url": "https://via.placeholder.com/300x300/2196f3/ffffff?text=Playlist+4"}]
            },
            {
                "id": "demo_playlist_5",
                "name": "Road Trip Classics",
                "description": "Perfect songs for long drives",
                "track_count": 67,
                "owner": "demo_user", 
                "public": True,
                "collaborative": False,
                "external_urls": {"spotify": "https://open.spotify.com/playlist/demo5"},
                "images": [{"url": "https://via.placeholder.com/300x300/ff9800/ffffff?text=Playlist+5"}]
            }
        ]
        
        self.demo_sync_history = [
            {
                "task_id": str(uuid.uuid4()),
                "status": "completed",
                "progress": 100,
                "total_tracks": 42,
                "synced_tracks": 40,
                "failed_tracks": 2,
                "spotify_playlist": self.demo_playlists[0],
                "apple_music_playlist": {
                    "id": "apple_demo_1",
                    "name": "My Awesome Mix (from Spotify)",
                    "track_count": 40
                },
                "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "updated_at": (datetime.utcnow() - timedelta(hours=2, minutes=5)).isoformat(),
                "completed_at": (datetime.utcnow() - timedelta(hours=1, minutes=55)).isoformat(),
                "error_message": None
            },
            {
                "task_id": str(uuid.uuid4()),
                "status": "partial", 
                "progress": 100,
                "total_tracks": 28,
                "synced_tracks": 25,
                "failed_tracks": 3,
                "spotify_playlist": self.demo_playlists[1],
                "apple_music_playlist": {
                    "id": "apple_demo_2",
                    "name": "Chill Vibes (from Spotify)",
                    "track_count": 25
                },
                "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "updated_at": (datetime.utcnow() - timedelta(days=1, minutes=-3)).isoformat(),
                "completed_at": (datetime.utcnow() - timedelta(days=1, minutes=-1)).isoformat(),
                "error_message": None
            },
            {
                "task_id": str(uuid.uuid4()),
                "status": "failed",
                "progress": 15,
                "total_tracks": 35,
                "synced_tracks": 5,
                "failed_tracks": 30,
                "spotify_playlist": self.demo_playlists[2],
                "apple_music_playlist": None,
                "created_at": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                "updated_at": (datetime.utcnow() - timedelta(days=3, minutes=-1)).isoformat(),
                "completed_at": (datetime.utcnow() - timedelta(days=3, minutes=-1)).isoformat(),
                "error_message": "Apple Music API rate limit exceeded"
            }
        ]
    
    def create_demo_user(self) -> Dict[str, Any]:
        """Create a demo user session"""
        user_id = "demo_user_" + str(uuid.uuid4())[:8]
        
        user_data = {
            "id": user_id,
            "displayName": "Demo User",
            "email": "demo@example.com",
            "spotifyConnected": True,
            "appleMusicConnected": True,
            "avatar": "https://via.placeholder.com/64x64/1db954/ffffff?text=DU"
        }
        
        # Create JWT token
        jwt_payload = {
            "user_id": user_id,
            "demo_mode": True,
            "spotify_connected": True,
            "apple_music_connected": True
        }
        
        jwt_token = security_manager.create_access_token(jwt_payload)
        
        # Store demo user session
        self.demo_users[user_id] = {
            "profile": user_data,
            "created_at": datetime.utcnow(),
            "demo_mode": True
        }
        
        return {
            "token": jwt_token,
            "user": user_data
        }
    
    def get_demo_playlists(self) -> List[Dict[str, Any]]:
        """Get demo Spotify playlists"""
        return self.demo_playlists.copy()
    
    def get_demo_sync_history(self) -> List[Dict[str, Any]]:
        """Get demo sync history"""
        return self.demo_sync_history.copy()
    
    def simulate_sync(self, playlist_id: str) -> Dict[str, Any]:
        """Simulate starting a playlist sync"""
        playlist = next((p for p in self.demo_playlists if p["id"] == playlist_id), None)
        if not playlist:
            raise ValueError("Demo playlist not found")
        
        task_id = str(uuid.uuid4())
        
        # Create a new "in progress" sync
        demo_sync = {
            "task_id": task_id,
            "status": "in_progress",
            "progress": 45,  # Simulate partial progress
            "total_tracks": playlist["track_count"],
            "synced_tracks": int(playlist["track_count"] * 0.45),
            "failed_tracks": 2,
            "spotify_playlist": playlist,
            "apple_music_playlist": {
                "id": f"apple_demo_{task_id[:8]}",
                "name": f"{playlist['name']} (from Spotify)",
                "track_count": int(playlist["track_count"] * 0.45)
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "error_message": None
        }
        
        # Add to history
        self.demo_sync_history.insert(0, demo_sync)
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Demo sync started successfully",
            "created_at": datetime.utcnow().isoformat()
        }
    
    def get_demo_sync_status(self, task_id: str) -> Dict[str, Any]:
        """Get demo sync status"""
        sync = next((s for s in self.demo_sync_history if s["task_id"] == task_id), None)
        if sync:
            return sync
        
        # Return a not found response
        raise ValueError("Demo sync task not found")
    
    def get_demo_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get demo user profile"""
        if user_id in self.demo_users:
            return self.demo_users[user_id]["profile"]
        return None