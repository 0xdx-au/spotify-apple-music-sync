"""
Custom exception classes for playlist sync service
Provides structured error handling for different failure scenarios
"""

class PlaylistSyncException(Exception):
    """Base exception for playlist sync operations"""
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class APIException(PlaylistSyncException):
    """Exception for API-related errors"""
    
    def __init__(self, message: str, status_code: int = None, error_code: str = "API_ERROR"):
        self.status_code = status_code
        super().__init__(message, error_code)

class RateLimitException(APIException):
    """Exception for API rate limiting"""
    
    def __init__(self, message: str, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message, 429, "RATE_LIMITED")

class AuthenticationException(PlaylistSyncException):
    """Exception for authentication failures"""
    
    def __init__(self, message: str):
        super().__init__(message, "AUTH_FAILED")

class TrackNotFoundError(PlaylistSyncException):
    """Exception for when a track cannot be found on the target platform"""
    
    def __init__(self, message: str, spotify_track_id: str = None):
        self.spotify_track_id = spotify_track_id
        super().__init__(message, "TRACK_NOT_FOUND")

class PlaylistCreationError(PlaylistSyncException):
    """Exception for playlist creation failures"""
    
    def __init__(self, message: str):
        super().__init__(message, "PLAYLIST_CREATION_FAILED")

class NetworkException(PlaylistSyncException):
    """Exception for network-related errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "NETWORK_ERROR")

class ConfigurationException(PlaylistSyncException):
    """Exception for configuration-related errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "CONFIG_ERROR")

class ValidationException(PlaylistSyncException):
    """Exception for data validation errors"""
    
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")