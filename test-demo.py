#!/usr/bin/env python3
"""
Test the demo mode functionality
"""
import requests
import json

API_BASE = "http://localhost:8000"

def test_demo_login():
    """Test demo login"""
    print("🧪 Testing Demo Login")
    print("=" * 20)
    
    response = requests.post(f"{API_BASE}/api/demo/login")
    if response.ok:
        data = response.json()
        print(f"✅ Demo login successful")
        print(f"   Token: {data['token'][:20]}...")
        print(f"   User: {data['user']['displayName']}")
        return data['token']
    else:
        print(f"❌ Demo login failed: {response.text}")
        return None

def test_demo_playlists(token):
    """Test demo playlists"""
    print("\n🎵 Testing Demo Playlists")
    print("=" * 25)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/api/demo/playlists", headers=headers)
    
    if response.ok:
        playlists = response.json()
        print(f"✅ Found {len(playlists)} demo playlists")
        for playlist in playlists[:3]:
            print(f"   • {playlist['name']} ({playlist['track_count']} tracks)")
        return True
    else:
        print(f"❌ Demo playlists failed: {response.text}")
        return False

def test_demo_sync(token):
    """Test demo sync"""
    print("\n🔄 Testing Demo Sync")
    print("=" * 18)
    
    headers = {"Authorization": f"Bearer {token}"}
    sync_data = {
        "spotify_playlist_id": "demo_playlist_1",
        "create_new_playlist": True,
        "apple_music_playlist_name": "Test Sync",
        "include_unavailable_tracks": False
    }
    
    response = requests.post(f"{API_BASE}/api/demo/sync", headers=headers, json=sync_data)
    
    if response.ok:
        result = response.json()
        print(f"✅ Demo sync started")
        print(f"   Task ID: {result['task_id']}")
        return result['task_id']
    else:
        print(f"❌ Demo sync failed: {response.text}")
        return None

if __name__ == "__main__":
    print("🎯 Demo Mode Test Suite")
    print("=" * 30)
    
    # Test demo login
    token = test_demo_login()
    if not token:
        exit(1)
    
    # Test demo playlists
    if not test_demo_playlists(token):
        exit(1)
    
    # Test demo sync
    task_id = test_demo_sync(token)
    if not task_id:
        exit(1)
    
    print("\n🎉 All demo tests passed!")
    print("   → Your backend demo mode is working")
    print("   → You can test the frontend at http://localhost:3000")
    print("   → Click 'Demo Mode' to test without OAuth")