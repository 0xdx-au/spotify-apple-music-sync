#!/bin/bash

echo "🔒 Starting Spotify-Apple Music Sync with HTTPS"
echo "==============================================="

# Check if certificates exist
if [[ ! -f "config/localhost-cert.pem" || ! -f "config/localhost-key.pem" ]]; then
    echo "📜 Generating SSL certificates for localhost..."
    mkdir -p config
    openssl req -x509 -newkey rsa:4096 -keyout config/localhost-key.pem -out config/localhost-cert.pem -days 365 -nodes -subj "/C=US/ST=Dev/L=Dev/O=Dev/OU=Dev/CN=localhost"
    echo "✅ SSL certificates generated"
fi

echo ""
echo "🚀 HTTPS STARTUP COMMANDS:"
echo "-------------------------"
echo "1. Backend (Terminal 1):"
echo "   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --ssl-keyfile config/localhost-key.pem --ssl-certfile config/localhost-cert.pem"
echo ""
echo "2. Frontend (Terminal 2):"
echo "   cd web-frontend"
echo "   HTTPS=true SSL_CRT_FILE=../config/localhost-cert.pem SSL_KEY_FILE=../config/localhost-key.pem npm start"
echo ""
echo "📱 ACCESS URLS:"
echo "--------------"
echo "• Frontend: https://localhost:3000"
echo "• Backend API: https://localhost:8000"
echo "• You: https://localhost:3000"
echo "• Others on network: https://YOUR_IP:3000"
echo ""
echo "⚠️  BROWSER SECURITY WARNING:"
echo "-----------------------------"
echo "Your browser will show 'Not Secure' warnings for self-signed certificates."
echo "This is NORMAL for development. Click 'Advanced' → 'Proceed to localhost'"
echo ""
echo "🎵 SPOTIFY APP SETTINGS:"
echo "------------------------"
echo "Use this redirect URI in your Spotify app:"
echo "https://localhost:8000/auth/spotify/callback"
echo ""
echo "🔧 Current .env check:"
if grep -q "your_spotify_client_id" .env; then
    echo "❌ Still need to update SPOTIFY_CLIENT_ID in .env"
else
    echo "✅ Spotify credentials configured"
fi