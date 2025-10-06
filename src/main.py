"""
Spotify to Apple Music Playlist Sync Service
Main FastAPI application entry point
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import logging
import os
from datetime import datetime

from .services.spotify_service import SpotifyService
from .services.apple_music_service import AppleMusicService
from .services.playlist_sync_service import PlaylistSyncService
from .services.auth_service import AuthService
from .services.demo_service import DemoService
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
    docs_url="/api/docs",  # Enable docs for testing
    redoc_url="/api/redoc",  # Enable redoc for testing
)

# Security middleware
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Initialize services
spotify_service = SpotifyService()
apple_music_service = AppleMusicService()
playlist_sync_service = PlaylistSyncService(spotify_service, apple_music_service)
auth_service = AuthService()
demo_service = DemoService()

# Mount static files for React frontend
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Spotify-Apple Music Playlist Sync",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/api/docs",
        "health": "/health"
    }

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

# OAuth Authentication Endpoints
@app.get("/api/auth/{provider}")
async def auth_redirect(provider: str, request: Request):
    """Redirect to OAuth provider"""
    try:
        if provider not in ['spotify', 'apple-music']:
            raise HTTPException(status_code=400, detail="Unsupported provider")
        
        # Use the request's origin as base for redirect URI
        redirect_uri = f"{request.base_url}api/auth/{provider}/callback"
        
        oauth_data = auth_service.generate_oauth_url(provider, str(redirect_uri))
        
        return RedirectResponse(url=oauth_data["auth_url"])
    except Exception as e:
        logger.error(f"OAuth redirect failed for {provider}: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth")

@app.get("/api/auth/{provider}/callback")
async def auth_callback(provider: str, code: str = None, state: str = None, error: str = None):
    """Handle OAuth callback"""
    try:
        if error:
            logger.error(f"OAuth error for {provider}: {error}")
            return HTMLResponse(
                content=f"""
                <html>
                    <body>
                        <script>
                            window.opener.postMessage({{ 
                                type: 'AUTH_ERROR', 
                                error: '{error}' 
                            }}, window.location.origin);
                            window.close();
                        </script>
                        <p>Authentication failed: {error}</p>
                    </body>
                </html>
                """
            )
        
        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        auth_result = await auth_service.handle_oauth_callback(provider, code, state)
        
        # Return HTML that posts message to parent window
        return HTMLResponse(
            content=f"""
            <html>
                <body>
                    <script>
                        window.opener.postMessage({{ 
                            type: 'AUTH_SUCCESS', 
                            token: '{auth_result["token"]}',
                            user: {auth_result["user"]} 
                        }}, window.location.origin);
                        window.close();
                    </script>
                    <p>Authentication successful! You can close this window.</p>
                </body>
            </html>
            """
        )
    except Exception as e:
        logger.error(f"OAuth callback failed for {provider}: {e}")
        return HTMLResponse(
            content=f"""
            <html>
                <body>
                    <script>
                        window.opener.postMessage({{ 
                            type: 'AUTH_ERROR', 
                            error: 'Authentication failed' 
                        }}, window.location.origin);
                        window.close();
                    </script>
                    <p>Authentication failed: {str(e)}</p>
                </body>
            </html>
            """
        )

@app.get("/api/user/profile")
async def get_user_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current user profile"""
    try:
        token = verify_token(credentials.credentials)
        user_id = token["user_id"]
        
        # Check if demo mode
        if token.get("demo_mode"):
            profile = demo_service.get_demo_user_profile(user_id)
        else:
            profile = auth_service.get_user_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        return profile
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user profile")

# Demo Mode Endpoints
@app.post("/api/demo/login")
async def demo_login():
    """Create a demo user session for testing"""
    try:
        demo_auth = demo_service.create_demo_user()
        return demo_auth
    except Exception as e:
        logger.error(f"Demo login failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create demo session")

@app.get("/api/demo/playlists")
async def get_demo_playlists(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get demo Spotify playlists"""
    try:
        token = verify_token(credentials.credentials)
        if not token.get("demo_mode"):
            raise HTTPException(status_code=403, detail="Demo mode required")
        
        playlists = demo_service.get_demo_playlists()
        return playlists
    except Exception as e:
        logger.error(f"Failed to get demo playlists: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve demo playlists")

@app.post("/api/demo/sync")
async def demo_sync_playlist(
    sync_request: SyncRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Simulate playlist sync in demo mode"""
    try:
        token = verify_token(credentials.credentials)
        if not token.get("demo_mode"):
            raise HTTPException(status_code=403, detail="Demo mode required")
        
        result = demo_service.simulate_sync(sync_request.spotify_playlist_id)
        return result
    except Exception as e:
        logger.error(f"Demo sync failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to simulate sync")

@app.get("/api/demo/history")
async def get_demo_sync_history(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get demo sync history"""
    try:
        token = verify_token(credentials.credentials)
        if not token.get("demo_mode"):
            raise HTTPException(status_code=403, detail="Demo mode required")
        
        history = demo_service.get_demo_sync_history()
        return history
    except Exception as e:
        logger.error(f"Failed to get demo history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve demo history")

# Catch-all route to serve React app (must be last)
@app.get("/{path:path}")
async def serve_frontend(path: str):
    """Serve React frontend for all non-API routes"""
    # Don't serve frontend for API routes
    if path.startswith("api/") or path == "health" or path == "docs" or path == "redoc" or path == "openapi.json":
        raise HTTPException(status_code=404, detail="Not Found")
    
    # Serve index.html for React routing
    index_file = os.path.join(static_dir, 'index.html')
    logger.info(f"Looking for static files in: {static_dir}")
    logger.info(f"Index file path: {index_file}")
    logger.info(f"Index file exists: {os.path.exists(index_file)}")
    
    if os.path.exists(index_file):
        return FileResponse(index_file)
    else:
        # Fallback if no frontend is built - serve a helpful page
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Spotify-Apple Music Playlist Sync</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 40px; background: #121212; color: #fff; }}
                        .container {{ max-width: 800px; margin: 0 auto; text-align: center; }}
                        .header {{ color: #1db954; margin-bottom: 40px; }}
                        .card {{ background: #1e1e1e; padding: 30px; border-radius: 12px; margin: 20px 0; }}
                        .button {{ display: inline-block; background: #1db954; color: white; padding: 12px 24px; 
                                text-decoration: none; border-radius: 6px; margin: 10px; font-weight: 600; }}
                        .button:hover {{ background: #1ed760; }}
                        .debug {{ background: #333; padding: 15px; border-radius: 8px; margin-top: 30px; 
                                font-family: monospace; font-size: 12px; text-align: left; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1 class="header">🎵 Spotify-Apple Music Playlist Sync</h1>
                        
                        <div class="card">
                            <h2>Service is Running!</h2>
                            <p>The API backend is operational, but the frontend interface is still being deployed.</p>
                            
                            <a href="/api/docs" class="button">📚 View API Documentation</a>
                            <a href="/health" class="button">💚 Check Health Status</a>
                        </div>
                        
                        <div class="card">
                            <h3>What's This Service?</h3>
                            <p>A modern web application for syncing playlists between Spotify and Apple Music with:</p>
                            <ul style="text-align: left; max-width: 500px; margin: 0 auto;">
                                <li>🔐 Secure user authentication</li>
                                <li>💳 Token-based subscription tiers</li>
                                <li>📊 Playlist analytics and statistics</li>
                                <li>⚡ Fast automated sync</li>
                                <li>📱 Responsive web interface</li>
                            </ul>
                        </div>
                        
                        <div class="debug">
                            <strong>Debug Info:</strong><br>
                            Static Directory: {static_dir}<br>
                            Index File: {index_file}<br>
                            Directory Exists: {os.path.exists(static_dir)}<br>
                            Index File Exists: {os.path.exists(index_file)}<br>
                            Working Directory: {os.getcwd()}<br>
                            Files in static dir: {os.listdir(static_dir) if os.path.exists(static_dir) else 'Directory not found'}
                        </div>
                    </div>
                </body>
            </html>
            """,
            media_type="text/html"
        )

# No direct uvicorn execution - use Procfile for deployment
