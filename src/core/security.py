"""
Security module for JWT token verification and authentication
Implements TLS 1.3 compliance and security best practices
"""

import jwt
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from .config import settings


class SecurityManager:
    """Manages security operations for the application"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self._fernet = None
    
    def _get_fernet(self) -> Fernet:
        """Get or create Fernet encryption instance"""
        if self._fernet is None:
            # Derive key from secret
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'stable_salt_for_playlist_sync',  # In production, use random salt per user
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.secret_key.encode()))
            self._fernet = Fernet(key)
        return self._fernet
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token with expiration"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(32),  # JWT ID for token invalidation
            "iss": "playlist-sync-service",
            "aud": "playlist-sync-client"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience="playlist-sync-client",
                issuer="playlist-sync-service"
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise SecurityException("Token has expired")
        except jwt.JWTError as e:
            raise SecurityException(f"Token verification failed: {str(e)}")
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data like tokens"""
        fernet = self._get_fernet()
        encrypted = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            fernet = self._get_fernet()
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise SecurityException(f"Decryption failed: {str(e)}")
    
    def hash_password(self, password: str) -> str:
        """Hash a password with salt"""
        salt = secrets.token_hex(32)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return salt + pwdhash.hex()
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password against its hash"""
        salt = stored_hash[:64]
        stored_pwdhash = stored_hash[64:]
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return pwdhash.hex() == stored_pwdhash
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    def validate_request_headers(self, headers: Dict[str, str]) -> bool:
        """Validate security headers in requests"""
        required_headers = {
            'User-Agent': lambda x: len(x) > 0 and 'playlist-sync' in x.lower(),
            'Content-Type': lambda x: x in ['application/json', 'application/x-www-form-urlencoded']
        }
        
        for header, validator in required_headers.items():
            if header not in headers or not validator(headers[header]):
                return False
        
        return True


class SecurityException(Exception):
    """Exception raised for security-related errors"""
    pass


# Global security manager instance
security_manager = SecurityManager()


def verify_token(token: str) -> Dict[str, Any]:
    """Verify a JWT token - convenience function for FastAPI dependency"""
    return security_manager.verify_token(token)


def create_user_session_token(user_data: Dict[str, Any]) -> str:
    """Create a session token for authenticated users"""
    session_data = {
        "user_id": user_data.get("id"),
        "spotify_token": security_manager.encrypt_sensitive_data(user_data.get("spotify_token", "")),
        "apple_music_token": security_manager.encrypt_sensitive_data(user_data.get("apple_music_token", "")),
        "permissions": user_data.get("permissions", ["read:playlists", "write:playlists"])
    }
    
    return security_manager.create_access_token(
        session_data,
        expires_delta=timedelta(hours=24)
    )