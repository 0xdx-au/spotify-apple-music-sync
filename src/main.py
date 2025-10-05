"""
Spotify to Apple Music Playlist Sync Service
Main FastAPI application entry point
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime

from .services.spotify_service import SpotifyService
from .services.apple_music_service import AppleMusicService
from .services.playlist_sync_service import PlaylistSyncService
from .models.playlist import PlaylistResponse, SyncRequest, SyncResponse
from .core.config import settings
from .core.security import verify_token

# Configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper()))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Spotify-Apple Music Playlist Sync",
    description="Microservice for syncing playlists between Spotify and Apple Music",
    version="1.0.0",
    docs_url="/api/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Security middleware
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Initialize services
spotify_service = SpotifyService()
apple_music_service = AppleMusicService()
playlist_sync_service = PlaylistSyncService(spotify_service, apple_music_service)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "playlist-sync",
        "version": "1.0.0"
    }

@app.get("/api/spotify/playlists")
async def get_spotify_playlists(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> List[PlaylistResponse]:
    """Get user's Spotify playlists"""
    try:
        token = verify_token(credentials.credentials)
        playlists = await spotify_service.get_user_playlists(token["spotify_token"])
        return [PlaylistResponse(**playlist) for playlist in playlists]
    except Exception as e:
        logger.error(f"Failed to get Spotify playlists: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Spotify playlists")

@app.post("/api/sync/playlist")
async def sync_playlist(
    sync_request: SyncRequest,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> SyncResponse:
    """Sync a Spotify playlist to Apple Music"""
    try:
        token = verify_token(credentials.credentials)
        
        # Start background sync process
        task_id = await playlist_sync_service.start_sync(
            spotify_playlist_id=sync_request.spotify_playlist_id,
            apple_music_token=token["apple_music_token"],
            spotify_token=token["spotify_token"],
            create_new=sync_request.create_new_playlist
        )
        
        return SyncResponse(
            task_id=task_id,
            status="started",
            message="Playlist sync initiated successfully"
        )
    except Exception as e:
        logger.error(f"Failed to sync playlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to start playlist sync")

@app.get("/api/sync/status/{task_id}")
async def get_sync_status(
    task_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get the status of a playlist sync operation"""
    try:
        token = verify_token(credentials.credentials)
        status = await playlist_sync_service.get_sync_status(task_id)
        return status
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sync status")

@app.get("/api/sync/history")
async def get_sync_history(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get user's sync history"""
    try:
        token = verify_token(credentials.credentials)
        history = await playlist_sync_service.get_sync_history(token["user_id"])
        return history
    except Exception as e:
        logger.error(f"Failed to get sync history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sync history")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="config/key.pem",
        ssl_certfile="config/cert.pem",
        log_level=settings.LOG_LEVEL.lower()
    )