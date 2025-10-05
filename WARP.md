# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

A secure microservice for syncing Spotify playlists to Apple Music, featuring both a FastAPI backend and native iOS/macOS apps. The system emphasizes security (TLS 1.3 only), rate limiting, and comprehensive error handling for production deployment.

## Architecture

- **Backend**: FastAPI microservice with Redis for caching/rate limiting
- **Frontend**: Native iOS/macOS SwiftUI applications
- **Deployment**: Docker containerized with production-ready configuration
- **Security**: TLS 1.3 enforcement, JWT authentication, comprehensive OPSEC compliance

## Common Development Commands

### Backend Development

```bash
# Setup virtual environment and dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run development server (with hot reload)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run with SSL certificates for production-like testing
uvicorn src.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile config/key.pem --ssl-certfile config/cert.pem
```

### Docker Development

```bash
# Start all services (API + Redis)
docker-compose up -d

# View logs for debugging
docker-compose logs -f playlist-sync-api
docker-compose logs -f redis

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Testing

```bash
# Run complete test suite
pytest tests/ -v

# Run with coverage reporting
pytest tests/ --cov=src --cov-report=html

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests  
pytest tests/integration/ -v

# Run specific test file
pytest tests/unit/test_spotify_service.py -v
```

### Code Quality

```bash
# Format code with Black
black src/ tests/

# Lint with pylint
pylint src/

# Type checking with mypy
mypy src/

# Security scanning with bandit
bandit -r src/
```

### iOS/macOS Development

```bash
# Open iOS project in Xcode
cd iOS-App
open PlaylistSyncApp.xcodeproj

# Build for iOS Simulator
xcodebuild -project PlaylistSyncApp.xcodeproj -scheme PlaylistSyncApp -destination 'platform=iOS Simulator,name=iPhone 15,OS=latest' build

# Build for macOS
xcodebuild -project PlaylistSyncApp.xcodeproj -scheme PlaylistSyncApp -destination 'platform=macOS' build
```

## Code Structure and Key Components

### Backend Service Architecture

The FastAPI backend follows a modular service-oriented architecture:

- **`src/main.py`**: Application entry point with FastAPI app, middleware, and route definitions
- **`src/core/`**: Core configuration and security utilities
  - `config.py`: Pydantic settings with environment variable management and TLS 1.3 configuration
  - `security.py`: JWT token handling and authentication utilities
- **`src/services/`**: Business logic services
  - `spotify_service.py`: Spotify Web API integration with rate limiting and error handling
  - `apple_music_service.py`: Apple Music API integration  
  - `playlist_sync_service.py`: Core synchronization logic and background task management
- **`src/models/`**: Pydantic data models for API requests/responses

### Rate Limiting Implementation

Both Spotify and Apple Music services implement custom rate limiters:
- **SpotifyRateLimiter**: Sliding window rate limiting with automatic retry on 429 responses
- Rate limits are configurable via environment variables (`SPOTIFY_RATE_LIMIT`, `APPLE_MUSIC_RATE_LIMIT`)
- Redis is used for distributed rate limiting across multiple instances

### Security Architecture

- **TLS 1.3 Enforcement**: All network connections must use TLS 1.3 (configured in `TLS_CONFIG`)
- **JWT Authentication**: Custom JWT implementation with audience/issuer validation
- **Certificate Pinning**: SSL certificate validation for enhanced security
- **Input Validation**: All API inputs validated using Pydantic models
- **OPSEC Compliance**: No secrets in logs, commit messages, or error responses

### iOS/macOS App Architecture

SwiftUI-based native apps with:
- **Environment Objects**: `AuthenticationService` and `PlaylistSyncService` for state management
- **Security Configuration**: TLS 1.3 enforcement in `configureSecurity()`
- **Reactive UI**: Async/await pattern for API calls with proper error handling
- **Cross-platform**: Single codebase supporting both iOS and macOS with conditional compilation

## Environment Configuration

### Required Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Spotify API credentials (from Spotify Developer Dashboard)
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Apple Music API credentials (from Apple Developer Portal)
APPLE_MUSIC_KEY_ID=your_apple_music_key_id
APPLE_MUSIC_TEAM_ID=your_apple_music_team_id
APPLE_MUSIC_PRIVATE_KEY=your_apple_music_private_key

# Security configuration
SECRET_KEY=$(openssl rand -hex 32)
REDIS_PASSWORD=$(openssl rand -hex 16)

# Environment settings
ENVIRONMENT=development
LOG_LEVEL=debug
```

### SSL Certificate Setup

```bash
# Generate self-signed certificates for development
mkdir -p config
openssl req -x509 -newkey rsa:4096 -keyout config/key.pem -out config/cert.pem -days 365 -nodes

# For production, use Let's Encrypt or proper CA certificates
```

## Development Workflows

### Adding New API Endpoints

1. **Define Pydantic models** in `src/models/` for request/response validation
2. **Implement business logic** in appropriate service class
3. **Add route handler** in `src/main.py` with proper authentication and error handling
4. **Add comprehensive tests** covering success and error scenarios
5. **Update API documentation** (FastAPI auto-generates OpenAPI docs at `/api/docs`)

### Service Integration Pattern

Services follow a consistent pattern:
- **Rate limiting** using custom rate limiter classes
- **TLS 1.3 enforcement** via `aiohttp.TCPConnector` with `TLS_CONFIG`
- **Comprehensive error handling** with logging and user-friendly error messages
- **Async/await** for all I/O operations
- **Retry logic** for transient failures (rate limits, network issues)

### Background Task Management

Playlist synchronization runs as background tasks:
- **Task tracking** via unique task IDs stored in Redis
- **Progress reporting** with real-time status updates
- **Error aggregation** for failed track synchronizations
- **Cleanup procedures** for completed/failed tasks

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Service-level functionality testing
- Rate limiter behavior validation
- Error handling and edge cases
- Security function testing

### Integration Tests (`tests/integration/`)
- End-to-end sync workflow testing
- API rate limiting scenarios
- Network error resilience
- Large playlist performance testing

### Manual Testing
- API endpoints via curl/Postman with JWT tokens
- iOS/macOS app functionality across different devices
- Docker container deployment validation

## Debugging and Troubleshooting

### Common Issues

**Authentication Failures**:
```bash
# Verify API credentials
cat .env | grep -E "(SPOTIFY|APPLE_MUSIC)"

# Test JWT token validation
curl -H "Authorization: Bearer YOUR_TOKEN" https://localhost:8000/api/spotify/playlists
```

**Rate Limiting**:
```bash
# Monitor rate limit logs
docker-compose logs playlist-sync-api | grep "rate"

# Check Redis rate limit keys
docker exec -it spotify-apple-music-sync_redis_1 redis-cli
> KEYS "*rate*"
```

**SSL/TLS Issues**:
```bash
# Verify TLS 1.3 configuration
openssl s_client -connect localhost:8000 -tls1_3

# Validate certificate
openssl x509 -in config/cert.pem -text -noout
```

### Debug Mode

Enable detailed logging:
```bash
# Set in .env
LOG_LEVEL=debug

# Restart services
docker-compose restart
```

## Security Considerations

### OPSEC Requirements
- **Commit messages**: Must be empty or contain only timestamps and "4CH41B01"
- **No secrets in code**: All sensitive data via environment variables
- **TLS 1.3 only**: Enforced at application and infrastructure level
- **Certificate validation**: Required for all HTTPS connections
- **Input sanitization**: Comprehensive validation on all API inputs

### Production Security Hardening
- Generate strong secrets using `openssl rand`
- Use proper CA-signed certificates
- Configure firewall rules for Docker containers
- Implement log rotation and secure log storage
- Regular security scanning with bandit/safety

## Performance Optimization

### Rate Limiting Strategy
- Spotify: 100 requests/minute (configurable)
- Apple Music: 333 requests/minute (20k/hour limit)
- Redis-backed distributed rate limiting for horizontal scaling

### Caching Strategy
- Playlist metadata cached in Redis with TTL
- Track search results cached to reduce API calls
- User authentication tokens cached with proper expiration

### Scalability Considerations
- Horizontal scaling via multiple Docker instances
- Redis cluster for high availability
- Background job queuing for heavy sync operations
- Database connection pooling for production deployments