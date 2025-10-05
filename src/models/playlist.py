"""
Pydantic models for playlist data structures
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SyncStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class TrackResponse(BaseModel):
    """Track information response model"""
    id: str
    name: str
    artist: str
    album: str
    duration_ms: int
    isrc: Optional[str] = None
    preview_url: Optional[str] = None
    external_urls: Dict[str, str] = {}

class PlaylistResponse(BaseModel):
    """Playlist information response model"""
    id: str
    name: str
    description: Optional[str] = None
    track_count: int
    owner: str
    public: bool = False
    collaborative: bool = False
    external_urls: Dict[str, str] = {}
    images: List[Dict[str, Any]] = []

class SyncRequest(BaseModel):
    """Request model for playlist sync operation"""
    spotify_playlist_id: str = Field(..., description="Spotify playlist ID to sync")
    create_new_playlist: bool = Field(default=True, description="Create new playlist or update existing")
    apple_music_playlist_name: Optional[str] = Field(None, description="Custom name for Apple Music playlist")
    include_unavailable_tracks: bool = Field(default=False, description="Include tracks not available on Apple Music in sync report")

class SyncResponse(BaseModel):
    """Response model for playlist sync operation"""
    task_id: str
    status: SyncStatus
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TrackSyncResult(BaseModel):
    """Result of syncing a single track"""
    spotify_track: TrackResponse
    apple_music_track: Optional[TrackResponse] = None
    status: str  # "success", "not_found", "error"
    error_message: Optional[str] = None

class SyncStatusResponse(BaseModel):
    """Detailed sync status response"""
    task_id: str
    status: SyncStatus
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    total_tracks: int
    synced_tracks: int
    failed_tracks: int
    spotify_playlist: PlaylistResponse
    apple_music_playlist: Optional[PlaylistResponse] = None
    track_results: List[TrackSyncResult] = []
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class SyncHistoryItem(BaseModel):
    """Sync history item"""
    task_id: str
    spotify_playlist_name: str
    apple_music_playlist_name: Optional[str]
    status: SyncStatus
    total_tracks: int
    synced_tracks: int
    failed_tracks: int
    created_at: datetime
    completed_at: Optional[datetime] = None