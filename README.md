# Spotify to Apple Music Playlist Sync

A secure, high-performance microservice that enables seamless syncing of playlists from Spotify to Apple Music, with comprehensive error handling for tracks not available on Apple Music. Features both a Docker-based backend API and native iOS/macOS applications.

## 🎯 Features

### Core Functionality
- **Playlist Migration**: Transfer complete playlists from Spotify to Apple Music
- **Smart Track Matching**: Multi-strategy track matching using ISRC codes, artist/title matching, and fuzzy matching algorithms
- **Error Handling**: Comprehensive reporting of tracks that couldn't be synced with detailed error messages
- **Real-time Progress**: Live sync status updates with detailed progress tracking
- **Batch Processing**: Efficient handling of large playlists with automatic batching

### Security & Performance
- **TLS 1.3 Only**: All connections use the latest TLS 1.3 protocol for maximum security
- **Rate Limiting**: Intelligent rate limiting for both Spotify and Apple Music APIs
- **JWT Authentication**: Secure token-based authentication with encryption
- **OPSEC Compliant**: No secrets exposed in logs or commit history
- **Dockerized**: Secure, isolated containerized deployment

### Platform Support
- **Docker Microservice**: RESTful API for integration with any client
- **iOS App**: Native Swift application with modern SwiftUI interface
- **macOS App**: Full-featured desktop application
- **Cross-Platform**: Unified codebase supporting both mobile and desktop

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   iOS/macOS     │    │     Docker      │    │    External     │
│     Apps        │◄──►│   Microservice  │◄──►│      APIs       │
│                 │    │                 │    │                 │
│ • SwiftUI       │    │ • FastAPI       │    │ • Spotify Web   │
│ • Native Auth   │    │ • Rate Limiting │    │ • Apple Music   │
│ • TLS 1.3       │    │ • Error Handling│    │ • Authentication│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Spotify Developer Account
- Apple Developer Account (for Apple Music API access)
- Xcode (for iOS/macOS apps)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd spotify-apple-music-sync

# Copy environment template
cp .env.example .env

# Edit .env with your API credentials
nano .env
```

### 2. Configure API Credentials

#### Spotify API Setup
1. Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Create a new application
3. Note your Client ID and Client Secret
4. Add `http://localhost:8000/auth/spotify/callback` to redirect URIs

#### Apple Music API Setup
1. Visit [Apple Developer Portal](https://developer.apple.com/)
2. Create a MusicKit identifier
3. Generate a private key for MusicKit
4. Note your Key ID and Team ID

#### Update `.env` file:
```bash
# Spotify API Configuration
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Apple Music API Configuration
APPLE_MUSIC_KEY_ID=your_apple_music_key_id
APPLE_MUSIC_TEAM_ID=your_apple_music_team_id
APPLE_MUSIC_PRIVATE_KEY=your_apple_music_private_key

# Security Configuration
SECRET_KEY=your_secure_secret_key
REDIS_PASSWORD=your_redis_password
```

### 3. Start the Services

```bash
# Build and start Docker containers
docker-compose up -d

# Check service health
curl -k https://localhost:8000/health
```

### 4. Build iOS/macOS Apps

```bash
# Open the iOS project
cd iOS-App
open PlaylistSyncApp.xcodeproj

# Build and run in Xcode
# Select target (iOS Simulator/macOS) and run
```

## 📖 API Documentation

### Authentication Endpoints

#### Spotify Authentication
```http
GET /auth/spotify
```
Redirects to Spotify OAuth flow.

#### Apple Music Authentication  
```http
GET /auth/apple-music
```
Redirects to Apple Music OAuth flow.

### Playlist Endpoints

#### Get Spotify Playlists
```http
GET /api/spotify/playlists
Authorization: Bearer {jwt_token}
```

#### Sync Playlist
```http
POST /api/sync/playlist
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "spotify_playlist_id": "playlist_id",
  "create_new_playlist": true,
  "apple_music_playlist_name": "Custom Name (optional)",
  "include_unavailable_tracks": false
}
```

#### Get Sync Status
```http
GET /api/sync/status/{task_id}
Authorization: Bearer {jwt_token}
```

#### Get Sync History
```http
GET /api/sync/history
Authorization: Bearer {jwt_token}
```

### Error Responses

All API errors follow this format:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": "Additional error details",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SPOTIFY_CLIENT_ID` | Spotify application client ID | ✅ | - |
| `SPOTIFY_CLIENT_SECRET` | Spotify application client secret | ✅ | - |
| `APPLE_MUSIC_KEY_ID` | Apple Music API key ID | ✅ | - |
| `APPLE_MUSIC_TEAM_ID` | Apple Developer team ID | ✅ | - |
| `APPLE_MUSIC_PRIVATE_KEY` | Apple Music API private key | ✅ | - |
| `SECRET_KEY` | JWT signing secret | ✅ | - |
| `REDIS_PASSWORD` | Redis authentication password | ✅ | - |
| `ENVIRONMENT` | Application environment | ❌ | `development` |
| `LOG_LEVEL` | Logging level | ❌ | `info` |
| `RATE_LIMIT_REQUESTS` | Rate limit per window | ❌ | `100` |
| `RATE_LIMIT_WINDOW` | Rate limit window (seconds) | ❌ | `60` |

### Security Configuration

The application enforces strict security measures:

- **TLS 1.3 Only**: All HTTPS connections use TLS 1.3
- **Certificate Pinning**: SSL certificates are validated against known values
- **JWT Security**: Tokens include audience, issuer, and expiration validation
- **Data Encryption**: Sensitive data encrypted using Fernet (AES 128)
- **Rate Limiting**: Both application-level and API-level rate limiting
- **Input Validation**: All inputs validated using Pydantic models
- **CORS Protection**: Configurable allowed origins
- **Security Headers**: Comprehensive security headers on all responses

## 🧪 Testing

### Run All Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run the complete test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/ -v          # Unit tests only
pytest tests/integration/ -v   # Integration tests only
```

### Test Categories

1. **Unit Tests** (`tests/unit/`)
   - Spotify service functionality
   - Apple Music service functionality
   - Error handling and edge cases
   - Rate limiting behavior
   - Security functions

2. **Integration Tests** (`tests/integration/`)
   - Complete sync workflow
   - API rate limiting scenarios
   - Network error resilience
   - Large playlist performance

3. **Manual Testing**
   - API endpoints via Postman/curl
   - iOS/macOS app functionality
   - Docker container deployment

## 🚀 Deployment

### Production Deployment

1. **Security Hardening**
   ```bash
   # Generate strong secrets
   openssl rand -hex 32  # For SECRET_KEY
   openssl rand -hex 16  # For REDIS_PASSWORD
   
   # Update production environment
   cp .env.example .env.production
   # Edit with production values
   ```

2. **SSL Certificates**
   ```bash
   # Generate self-signed certificates for development
   openssl req -x509 -newkey rsa:4096 -keyout config/key.pem -out config/cert.pem -days 365 -nodes
   
   # For production, use Let's Encrypt or your certificate authority
   ```

3. **Docker Production**
   ```bash
   # Build production image
   docker build -t playlist-sync-prod .
   
   # Deploy with production compose file
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Health Monitoring**
   ```bash
   # Check service health
   curl -k https://your-domain.com/health
   
   # Monitor logs
   docker-compose logs -f playlist-sync-api
   ```

### Scaling Considerations

- **Redis Cluster**: For high availability and horizontal scaling
- **Load Balancer**: Multiple API instances behind a load balancer
- **Database**: PostgreSQL for production instead of SQLite
- **Monitoring**: Prometheus + Grafana for metrics and alerting
- **Log Aggregation**: ELK stack for centralized logging

## 🛠️ Development

### Local Development Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Code Style and Quality

```bash
# Format code
black src/ tests/

# Lint code
pylint src/

# Type checking
mypy src/

# Security scanning
bandit -r src/
```

### Adding New Features

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-feature-name
   ```

2. **Follow Development Workflow**
   - Write tests first (TDD approach)
   - Implement functionality
   - Update documentation
   - Test thoroughly

3. **Security Review**
   - No secrets in code or logs
   - Input validation on all endpoints
   - Proper error handling
   - Rate limiting considerations

4. **Commit and Push**
   ```bash
   # Following OPSEC requirements: no commit messages
   git add .
   git commit --allow-empty-message -m ''
   git push origin feature/new-feature-name
   ```

## 🔍 Troubleshooting

### Common Issues

#### API Authentication Errors
```bash
# Check API credentials in .env
cat .env | grep -E "(SPOTIFY|APPLE_MUSIC)"

# Verify JWT token format
curl -H "Authorization: Bearer YOUR_TOKEN" https://localhost:8000/api/spotify/playlists
```

#### Rate Limiting Issues
```bash
# Check rate limit settings
docker-compose logs playlist-sync-api | grep "rate"

# Monitor Redis for rate limit data
docker exec -it spotify-apple-music-sync_redis_1 redis-cli
> KEYS "*rate*"
```

#### SSL/TLS Issues
```bash
# Verify TLS 1.3 configuration
openssl s_client -connect localhost:8000 -tls1_3

# Check certificate validity
openssl x509 -in config/cert.pem -text -noout
```

#### Performance Issues
```bash
# Check container resource usage
docker stats

# Monitor API response times
curl -w "@curl-format.txt" https://localhost:8000/health
```

### Debugging

#### Enable Debug Logging
```bash
# Set in .env
LOG_LEVEL=debug

# Restart services
docker-compose restart
```

#### Access Container Logs
```bash
# View all services
docker-compose logs

# View specific service
docker-compose logs playlist-sync-api

# Follow logs in real-time
docker-compose logs -f playlist-sync-api
```

## 🤝 Contributing

### Guidelines
1. Follow security-first development practices
2. Maintain comprehensive test coverage (>90%)
3. Follow OPSEC requirements for commits
4. Update documentation for all changes
5. Ensure TLS 1.3 compliance for all network operations

### License
MIT License - See LICENSE file for details

## 📞 Support

### Access Locations
- **API Documentation**: `https://localhost:8000/api/docs`
- **Health Endpoint**: `https://localhost:8000/health`
- **Logs**: `docker-compose logs playlist-sync-api`
- **Configuration**: `.env` file in project root

### Security Reporting
For security issues, please create an encrypted report following responsible disclosure practices.

---

**CH41B01** - Secure playlist synchronization with enterprise-grade security standards.