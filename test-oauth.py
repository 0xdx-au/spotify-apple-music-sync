#!/usr/bin/env python3
"""
OAuth Configuration Test Script
Verifies that Spotify OAuth is properly configured
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_spotify_oauth():
    """Test Spotify OAuth configuration"""
    print("🎵 Testing Spotify OAuth Configuration")
    print("=" * 40)
    
    # Check environment variables
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8000/auth/spotify/callback')
    
    if not client_id or client_id == 'your_spotify_client_id':
        print("❌ SPOTIFY_CLIENT_ID not configured")
        print("   → Set this in your .env file")
        return False
    
    if not client_secret or client_secret == 'your_spotify_client_secret':
        print("❌ SPOTIFY_CLIENT_SECRET not configured")
        print("   → Set this in your .env file")
        return False
    
    print(f"✅ Client ID: {client_id[:10]}...")
    print(f"✅ Client Secret: {client_secret[:10]}...")
    print(f"✅ Redirect URI: {redirect_uri}")
    
    # Test OAuth URL generation
    scopes = [
        'user-read-private',
        'user-read-email',
        'playlist-read-private',
        'playlist-read-collaborative'
    ]
    
    auth_url = (
        f"https://accounts.spotify.com/authorize?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"redirect_uri={redirect_uri}&"
        f"scope={'+'.join(scopes)}&"
        f"state=test_state&"
        f"show_dialog=true"
    )
    
    print("\n🔗 OAuth URL Generated Successfully:")
    print(f"   {auth_url[:100]}...")
    
    return True

def test_backend_connection():
    """Test if backend is running and accessible"""
    print("\n🔧 Testing Backend Connection")
    print("=" * 30)
    
    try:
        response = requests.get('https://localhost:8000/health', timeout=5, verify=False)
        if response.status_code == 200:
            print("✅ Backend is running on port 8000")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend not running on port 8000")
        print("   → Start with: uvicorn src.main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Error connecting to backend: {e}")
        return False

def test_frontend_connection():
    """Test if frontend is running and accessible"""
    print("\n🌐 Testing Frontend Connection")
    print("=" * 30)
    
    try:
        response = requests.get('http://localhost:3000', timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running on port 3000")
            return True
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Frontend not running on port 3000")
        print("   → Start with: cd web-frontend && npm start")
        return False
    except Exception as e:
        print(f"❌ Error connecting to frontend: {e}")
        return False

def main():
    """Run all OAuth tests"""
    print("🧪 Spotify-Apple Music Sync - OAuth Test Suite")
    print("=" * 50)
    
    # Test OAuth configuration
    oauth_ok = test_spotify_oauth()
    
    # Test service connections
    backend_ok = test_backend_connection()
    frontend_ok = test_frontend_connection()
    
    # Summary
    print("\n📋 TEST SUMMARY")
    print("=" * 15)
    print(f"OAuth Config: {'✅ PASS' if oauth_ok else '❌ FAIL'}")
    print(f"Backend:      {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"Frontend:     {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    
    if all([oauth_ok, backend_ok, frontend_ok]):
        print("\n🎉 ALL TESTS PASSED!")
        print("   → Your service is ready for multi-user testing")
        print("   → Share http://YOUR_IP:3000 with others to test")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("   → Check the errors above and fix configuration")
        print("   → Re-run this script after fixes")
    
    return all([oauth_ok, backend_ok, frontend_ok])

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)