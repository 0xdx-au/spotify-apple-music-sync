"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
import os
import json

class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    # Spotify API
    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""
    SPOTIFY_REDIRECT_URI: str = "http://localhost:8000/auth/spotify/callback"
    
    # Dynamic URLs for multi-environment support
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    
    # Apple Music API
    APPLE_MUSIC_KEY_ID: str = ""
    APPLE_MUSIC_TEAM_ID: str = ""
    APPLE_MUSIC_PRIVATE_KEY: str = ""
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: str = ""
    
    # Database (for sync history and user data)
    DATABASE_URL: str = "sqlite:///./playlist_sync.db"
    
    # API Rate Limits
    SPOTIFY_RATE_LIMIT: int = 100  # requests per minute
    APPLE_MUSIC_RATE_LIMIT: int = 333  # requests per minute (20k per hour)
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse ALLOWED_ORIGINS from various input formats"""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Handle empty string
            if not v.strip():
                return ["http://localhost:3000"]
            # Handle comma-separated string
            if ',' in v:
                return [origin.strip() for origin in v.split(',') if origin.strip()]
            # Handle JSON string
            if v.strip().startswith('['):
                try:
                    parsed = json.loads(v)
                    return parsed if isinstance(parsed, list) else [str(parsed)]
                except json.JSONDecodeError:
                    return [v.strip()]
            # Single URL
            return [v.strip()]
        return ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# TLS 1.3 configuration for security compliance
TLS_CONFIG = {
    "ssl_version": "TLSv1_3",
    "ciphers": "TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256",
    "verify_mode": "CERT_REQUIRED",
    "check_hostname": True
}