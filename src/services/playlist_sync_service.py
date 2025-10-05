"""
Playlist synchronization service
Coordinates syncing playlists between Spotify and Apple Music
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from ..models.playlist import (
    SyncStatus, SyncStatusResponse, SyncHistoryItem, TrackSyncResult,
    PlaylistResponse, TrackResponse
)
from .spotify_service import SpotifyService
from .apple_music_service import AppleMusicService

logger = logging.getLogger(__name__)

class PlaylistSyncService:
    """Service for managing playlist synchronization between Spotify and Apple Music"""
    
    def __init__(self, spotify_service: SpotifyService, apple_music_service: AppleMusicService):
        self.spotify_service = spotify_service
        self.apple_music_service = apple_music_service
        
        # In-memory storage for sync tasks (in production, use Redis or database)
        self.sync_tasks: Dict[str, Dict[str, Any]] = {}
        self.sync_history: Dict[str, List[SyncHistoryItem]] = {}
    
    async def start_sync(
        self,
        spotify_playlist_id: str,
        apple_music_token: str,
        spotify_token: str,
        create_new: bool = True,
        apple_music_playlist_name: Optional[str] = None
    ) -> str:
        """Start a background playlist sync operation"""
        task_id = str(uuid.uuid4())
        
        # Initialize task record
        self.sync_tasks[task_id] = {
            "task_id": task_id,
            "status": SyncStatus.PENDING,
            "spotify_playlist_id": spotify_playlist_id,
            "apple_music_token": apple_music_token,
            "spotify_token": spotify_token,
            "create_new": create_new,
            "apple_music_playlist_name": apple_music_playlist_name,
            "progress": 0,
            "total_tracks": 0,
            "synced_tracks": 0,
            "failed_tracks": 0,
            "track_results": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "completed_at": None,
            "error_message": None,
            "spotify_playlist": None,
            "apple_music_playlist": None
        }
        
        # Start background sync
        asyncio.create_task(self._perform_sync(task_id))
        
        logger.info(f"Started sync task {task_id} for playlist {spotify_playlist_id}")
        return task_id
    
    async def _perform_sync(self, task_id: str):
        """Perform the actual playlist synchronization"""
        try:
            task_data = self.sync_tasks[task_id]
            task_data["status"] = SyncStatus.IN_PROGRESS
            task_data["updated_at"] = datetime.utcnow()
            
            # Get Spotify playlist details
            spotify_playlist = await self._get_spotify_playlist_details(
                task_data["spotify_playlist_id"],
                task_data["spotify_token"]
            )
            task_data["spotify_playlist"] = spotify_playlist
            
            # Get tracks from Spotify playlist
            spotify_tracks = await self.spotify_service.get_playlist_tracks(
                task_data["spotify_playlist_id"],
                task_data["spotify_token"]
            )
            
            task_data["total_tracks"] = len(spotify_tracks)
            logger.info(f"Task {task_id}: Found {len(spotify_tracks)} tracks to sync")
            
            # Create or find Apple Music playlist
            apple_playlist_name = (
                task_data["apple_music_playlist_name"] or 
                f"{spotify_playlist['name']} (from Spotify)"
            )
            
            apple_music_playlist = await self._create_apple_music_playlist(
                apple_playlist_name,
                spotify_playlist.get("description", ""),
                task_data["apple_music_token"]
            )
            task_data["apple_music_playlist"] = apple_music_playlist
            
            # Sync tracks one by one
            track_results = []
            synced_count = 0
            failed_count = 0
            
            for i, spotify_track in enumerate(spotify_tracks):
                try:
                    # Update progress
                    task_data["progress"] = int((i / len(spotify_tracks)) * 100)
                    task_data["updated_at"] = datetime.utcnow()
                    
                    # Try to find and add track to Apple Music playlist
                    sync_result = await self._sync_single_track(
                        spotify_track,
                        apple_music_playlist["id"],
                        task_data["apple_music_token"]
                    )
                    
                    track_results.append(sync_result)
                    
                    if sync_result["status"] == "success":
                        synced_count += 1
                    else:
                        failed_count += 1
                    
                    # Small delay to respect rate limits
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Task {task_id}: Error syncing track {spotify_track.get('name', 'unknown')}: {e}")
                    failed_count += 1
                    track_results.append({
                        "spotify_track": spotify_track,
                        "apple_music_track": None,
                        "status": "error",
                        "error_message": str(e)
                    })
            
            # Update final task status
            task_data["synced_tracks"] = synced_count
            task_data["failed_tracks"] = failed_count
            task_data["track_results"] = track_results
            task_data["progress"] = 100
            task_data["completed_at"] = datetime.utcnow()
            task_data["updated_at"] = datetime.utcnow()
            
            if synced_count == len(spotify_tracks):
                task_data["status"] = SyncStatus.COMPLETED
            elif synced_count > 0:
                task_data["status"] = SyncStatus.PARTIAL
            else:
                task_data["status"] = SyncStatus.FAILED
                task_data["error_message"] = "No tracks could be synced"
            
            logger.info(f"Task {task_id}: Completed sync - {synced_count}/{len(spotify_tracks)} tracks synced")
            
            # Add to sync history (simplified - in production, associate with user)
            await self._add_to_history(task_data)
            
        except Exception as e:
            logger.error(f"Task {task_id}: Sync failed with error: {e}")
            task_data["status"] = SyncStatus.FAILED
            task_data["error_message"] = str(e)
            task_data["completed_at"] = datetime.utcnow()
            task_data["updated_at"] = datetime.utcnow()
    
    async def _get_spotify_playlist_details(self, playlist_id: str, token: str) -> Dict[str, Any]:
        """Get Spotify playlist metadata"""
        # Get basic playlist info (this is a simplified version - expand based on actual API)
        playlists = await self.spotify_service.get_user_playlists(token)
        for playlist in playlists:
            if playlist["id"] == playlist_id:
                return playlist
        
        # If not found in user playlists, return basic structure
        return {
            "id": playlist_id,
            "name": f"Playlist {playlist_id}",
            "description": "",
            "track_count": 0,
            "owner": "Unknown",
            "public": False,
            "collaborative": False,
            "external_urls": {},
            "images": []
        }
    
    async def _create_apple_music_playlist(
        self, 
        name: str, 
        description: str, 
        token: str
    ) -> Dict[str, Any]:
        """Create a new Apple Music playlist"""
        try:
            # This would call the actual Apple Music API to create a playlist
            # For now, return a mock response
            playlist_id = str(uuid.uuid4())
            return {
                "id": playlist_id,
                "name": name,
                "description": description,
                "track_count": 0,
                "owner": "User",
                "public": False,
                "collaborative": False,
                "external_urls": {},
                "images": []
            }
        except Exception as e:
            logger.error(f"Failed to create Apple Music playlist: {e}")
            raise
    
    async def _sync_single_track(
        self, 
        spotify_track: Dict[str, Any], 
        apple_playlist_id: str, 
        apple_token: str
    ) -> Dict[str, Any]:
        """Sync a single track to Apple Music"""
        try:
            # Search for track on Apple Music using ISRC first, then artist/title
            search_query = ""
            
            if spotify_track.get("isrc"):
                search_query = f"isrc:{spotify_track['isrc']}"
            else:
                search_query = f"{spotify_track['artist']} {spotify_track['name']}"
            
            # This would call the actual Apple Music search API
            # For now, simulate success for demonstration
            apple_music_track = {
                "id": str(uuid.uuid4()),
                "name": spotify_track["name"],
                "artist": spotify_track["artist"],
                "album": spotify_track["album"],
                "duration_ms": spotify_track["duration_ms"],
                "isrc": spotify_track.get("isrc"),
                "preview_url": None,
                "external_urls": {}
            }
            
            # Add track to Apple Music playlist (would call actual API)
            # For now, simulate success
            
            return {
                "spotify_track": spotify_track,
                "apple_music_track": apple_music_track,
                "status": "success",
                "error_message": None
            }
            
        except Exception as e:
            return {
                "spotify_track": spotify_track,
                "apple_music_track": None,
                "status": "error",
                "error_message": str(e)
            }
    
    async def get_sync_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a sync operation"""
        return self.sync_tasks.get(task_id)
    
    async def get_sync_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get sync history for a user"""
        # In production, this would query a database by user_id
        # For now, return all history items
        all_history = []
        for user_history in self.sync_history.values():
            for item in user_history:
                all_history.append({
                    "task_id": item.task_id,
                    "spotify_playlist_name": item.spotify_playlist_name,
                    "apple_music_playlist_name": item.apple_music_playlist_name,
                    "status": item.status,
                    "total_tracks": item.total_tracks,
                    "synced_tracks": item.synced_tracks,
                    "failed_tracks": item.failed_tracks,
                    "created_at": item.created_at,
                    "completed_at": item.completed_at
                })
        
        # Sort by created_at descending
        all_history.sort(key=lambda x: x["created_at"], reverse=True)
        return all_history[:50]  # Return last 50 items
    
    async def _add_to_history(self, task_data: Dict[str, Any]):
        """Add completed sync to history"""
        # In production, save to database with proper user association
        user_id = "default_user"  # Placeholder
        
        history_item = SyncHistoryItem(
            task_id=task_data["task_id"],
            spotify_playlist_name=task_data["spotify_playlist"]["name"],
            apple_music_playlist_name=task_data.get("apple_music_playlist", {}).get("name"),
            status=task_data["status"],
            total_tracks=task_data["total_tracks"],
            synced_tracks=task_data["synced_tracks"],
            failed_tracks=task_data["failed_tracks"],
            created_at=task_data["created_at"],
            completed_at=task_data["completed_at"]
        )
        
        if user_id not in self.sync_history:
            self.sync_history[user_id] = []
        
        self.sync_history[user_id].append(history_item)
        
        # Keep only last 100 items per user
        if len(self.sync_history[user_id]) > 100:
            self.sync_history[user_id] = self.sync_history[user_id][-100:]