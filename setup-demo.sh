#!/bin/bash

echo "🎵 Spotify-Apple Music Sync - Quick Demo Setup"
echo "============================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🔧 CONFIGURATION NEEDED:"
echo "------------------------"

# Check if Spotify credentials are set
if grep -q "your_spotify_client_id" .env; then
    echo "❌ Spotify OAuth not configured"
    echo ""
    echo "🎯 TO GET WORKING DEMO:"
    echo "1. Go to: https://developer.spotify.com/dashboard"
    echo "2. Create new app with these settings:"
    echo "   - Redirect URI: http://localhost:8000/auth/spotify/callback"
    echo "   - Web API enabled"
    echo "3. Copy Client ID and Client Secret to .env file"
    echo ""
    echo "📝 Edit .env file and replace:"
    echo "   SPOTIFY_CLIENT_ID=your_spotify_client_id"
    echo "   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret"
    echo ""
else
    echo "✅ Spotify credentials configured"
fi

# Generate secure secret key if needed
if grep -q "your-secret-key-change-in-production" .env; then
    SECRET_KEY=$(openssl rand -hex 32)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/SECRET_KEY=your-secret-key-change-in-production/SECRET_KEY=$SECRET_KEY/" .env
    else
        # Linux
        sed -i "s/SECRET_KEY=your-secret-key-change-in-production/SECRET_KEY=$SECRET_KEY/" .env
    fi
    echo "✅ Generated secure SECRET_KEY"
fi

echo ""
echo "🚀 STARTUP COMMANDS:"
echo "-------------------"
echo "1. Backend (Terminal 1):"
echo "   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. Frontend (Terminal 2):"
echo "   cd web-frontend && npm start"
echo ""
echo "3. Open browser to: http://localhost:3000"

echo ""
echo "📋 MULTI-USER TESTING:"
echo "----------------------"
echo "• Share http://YOUR_IP:3000 with others on your network"
echo "• Each person can sign in with their own Spotify account"
echo "• Use 'ifconfig' or 'ip addr' to find your IP address"

echo ""
echo "⚠️  APPLE MUSIC NOTE:"
echo "--------------------"
echo "Apple Music requires paid Apple Developer account ($99/year)"
echo "For demo purposes, focus on Spotify integration first"

echo ""
echo "🔗 NEXT STEPS FOR PRODUCTION:"
echo "-----------------------------"
echo "See OAUTH_SETUP.md for full deployment guide"
echo ""

# Check if services are running
echo "🔍 CHECKING CURRENT STATUS:"
echo "--------------------------"

# Check backend
if lsof -ti:8000 > /dev/null; then
    echo "✅ Backend running on port 8000"
else
    echo "❌ Backend not running on port 8000"
fi

# Check frontend  
if lsof -ti:3000 > /dev/null; then
    echo "✅ Frontend running on port 3000"
else
    echo "❌ Frontend not running on port 3000"
fi

echo ""
echo "🎉 Ready to demo! Follow the startup commands above."