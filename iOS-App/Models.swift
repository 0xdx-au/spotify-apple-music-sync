import Foundation
import SwiftUI

// MARK: - Playlist Models

struct PlaylistModel: Codable, Identifiable {
    let id: String
    let name: String
    let description: String
    let trackCount: Int
    let owner: String
    let isPublic: Bool
    let isCollaborative: Bool
    let externalUrls: [String: String]
    let images: [PlaylistImage]
    
    var imageURL: URL? {
        guard let firstImage = images.first, 
              let url = URL(string: firstImage.url) else {
            return nil
        }
        return url
    }
    
    enum CodingKeys: String, CodingKey {
        case id, name, description, owner, images
        case trackCount = "track_count"
        case isPublic = "public"
        case isCollaborative = "collaborative"
        case externalUrls = "external_urls"
    }
}

struct PlaylistImage: Codable {
    let url: String
    let height: Int?
    let width: Int?
}

// MARK: - Track Models

struct TrackModel: Codable, Identifiable {
    let id: String
    let name: String
    let artist: String
    let album: String
    let durationMs: Int
    let isrc: String?
    let previewUrl: String?
    let externalUrls: [String: String]
    
    var duration: TimeInterval {
        return TimeInterval(durationMs) / 1000.0
    }
    
    var formattedDuration: String {
        let minutes = Int(duration) / 60
        let seconds = Int(duration) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
    
    enum CodingKeys: String, CodingKey {
        case id, name, artist, album, isrc
        case durationMs = "duration_ms"
        case previewUrl = "preview_url"
        case externalUrls = "external_urls"
    }
}

// MARK: - Sync Models

enum SyncStatus: String, Codable, CaseIterable {
    case pending = "pending"
    case inProgress = "in_progress"
    case completed = "completed"
    case failed = "failed"
    case partial = "partial"
    
    var displayName: String {
        switch self {
        case .pending:
            return "Pending"
        case .inProgress:
            return "In Progress"
        case .completed:
            return "Completed"
        case .failed:
            return "Failed"
        case .partial:
            return "Partial"
        }
    }
    
    var color: Color {
        switch self {
        case .pending:
            return .orange
        case .inProgress:
            return .blue
        case .completed:
            return .green
        case .failed:
            return .red
        case .partial:
            return .yellow
        }
    }
    
    var systemImage: String {
        switch self {
        case .pending:
            return "clock"
        case .inProgress:
            return "arrow.clockwise"
        case .completed:
            return "checkmark.circle"
        case .failed:
            return "xmark.circle"
        case .partial:
            return "exclamationmark.triangle"
        }
    }
}

struct SyncRequest: Codable {
    let spotifyPlaylistId: String
    let createNewPlaylist: Bool
    let appleMusicPlaylistName: String?
    let includeUnavailableTracks: Bool
    
    enum CodingKeys: String, CodingKey {
        case spotifyPlaylistId = "spotify_playlist_id"
        case createNewPlaylist = "create_new_playlist"
        case appleMusicPlaylistName = "apple_music_playlist_name"
        case includeUnavailableTracks = "include_unavailable_tracks"
    }
}

struct SyncResponse: Codable {
    let taskId: String
    let status: SyncStatus
    let message: String
    let createdAt: Date
    
    enum CodingKeys: String, CodingKey {
        case taskId = "task_id"
        case status, message
        case createdAt = "created_at"
    }
}

struct SyncHistoryItem: Codable, Identifiable {
    let taskId: String
    let spotifyPlaylistName: String
    let appleMusicPlaylistName: String?
    let status: SyncStatus
    let totalTracks: Int
    let syncedTracks: Int
    let failedTracks: Int
    let createdAt: Date
    let completedAt: Date?
    
    var id: String { taskId }
    
    var progress: Double {
        guard totalTracks > 0 else { return 0 }
        return Double(syncedTracks) / Double(totalTracks)
    }
    
    var progressPercentage: Int {
        return Int(progress * 100)
    }
    
    enum CodingKeys: String, CodingKey {
        case taskId = "task_id"
        case spotifyPlaylistName = "spotify_playlist_name"
        case appleMusicPlaylistName = "apple_music_playlist_name"
        case status
        case totalTracks = "total_tracks"
        case syncedTracks = "synced_tracks"
        case failedTracks = "failed_tracks"
        case createdAt = "created_at"
        case completedAt = "completed_at"
    }
}

struct TrackSyncResult: Codable {
    let spotifyTrack: TrackModel
    let appleMusicTrack: TrackModel?
    let status: String
    let errorMessage: String?
    
    var isSuccess: Bool {
        return status == "success"
    }
    
    var isFailed: Bool {
        return status == "error" || status == "not_found"
    }
    
    enum CodingKeys: String, CodingKey {
        case spotifyTrack = "spotify_track"
        case appleMusicTrack = "apple_music_track"
        case status
        case errorMessage = "error_message"
    }
}

struct SyncStatusResponse: Codable {
    let taskId: String
    let status: SyncStatus
    let progress: Int
    let totalTracks: Int
    let syncedTracks: Int
    let failedTracks: Int
    let spotifyPlaylist: PlaylistModel
    let appleMusicPlaylist: PlaylistModel?
    let trackResults: [TrackSyncResult]
    let createdAt: Date
    let updatedAt: Date
    let completedAt: Date?
    let errorMessage: String?
    
    enum CodingKeys: String, CodingKey {
        case taskId = "task_id"
        case status, progress
        case totalTracks = "total_tracks"
        case syncedTracks = "synced_tracks"
        case failedTracks = "failed_tracks"
        case spotifyPlaylist = "spotify_playlist"
        case appleMusicPlaylist = "apple_music_playlist"
        case trackResults = "track_results"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
        case completedAt = "completed_at"
        case errorMessage = "error_message"
    }
}

// MARK: - Authentication Models

struct AuthToken: Codable {
    let accessToken: String
    let refreshToken: String?
    let expiresIn: Int
    let tokenType: String
    let scope: String?
    let expiresAt: Date
    
    var isExpired: Bool {
        return Date() >= expiresAt
    }
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
        case tokenType = "token_type"
        case scope
        case expiresAt = "expires_at"
    }
}

struct UserProfile: Codable {
    let id: String
    let displayName: String?
    let email: String?
    let country: String?
    let product: String?
    let images: [PlaylistImage]
    
    var avatarURL: URL? {
        guard let firstImage = images.first,
              let url = URL(string: firstImage.url) else {
            return nil
        }
        return url
    }
    
    enum CodingKeys: String, CodingKey {
        case id, email, country, product, images
        case displayName = "display_name"
    }
}

// MARK: - API Response Models

struct APIError: Codable, Error, LocalizedError {
    let message: String
    let code: String?
    let statusCode: Int?
    
    var errorDescription: String? {
        return message
    }
    
    enum CodingKeys: String, CodingKey {
        case message, code
        case statusCode = "status_code"
    }
}

struct PaginatedResponse<T: Codable>: Codable {
    let items: [T]
    let total: Int
    let limit: Int
    let offset: Int
    let next: String?
    let previous: String?
    
    var hasMore: Bool {
        return next != nil
    }
}

// MARK: - Configuration Models

struct AppConfiguration {
    static let microserviceBaseURL = "https://localhost:8000"
    static let spotifyAuthURL = "https://accounts.spotify.com/authorize"
    static let appleMusicAuthURL = "https://beta.music.apple.com/authorize"
    
    // Security settings
    static let tlsMinVersion = "1.3"
    static let certificatePinningEnabled = true
    static let requestTimeoutInterval: TimeInterval = 30.0
    
    // Rate limiting
    static let maxConcurrentRequests = 5
    static let requestRetryCount = 3
    static let requestRetryDelay: TimeInterval = 1.0
}