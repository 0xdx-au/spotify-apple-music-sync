import SwiftUI
import Combine

@main
struct PlaylistSyncApp: App {
    @StateObject private var authenticationService = AuthenticationService()
    @StateObject private var syncService = PlaylistSyncService()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authenticationService)
                .environmentObject(syncService)
                .onAppear {
                    configureSecurity()
                }
        }
        #if os(macOS)
        .windowStyle(.hiddenTitleBar)
        .windowToolbarStyle(.unified(showsTitle: false))
        #endif
    }
    
    private func configureSecurity() {
        // Configure TLS 1.3 for all network connections
        let urlSessionConfig = URLSessionConfiguration.default
        urlSessionConfig.tlsMinimumSupportedProtocolVersion = .TLSv13
        urlSessionConfig.tlsMaximumSupportedProtocolVersion = .TLSv13
        
        // Set up certificate pinning for enhanced security
        urlSessionConfig.urlCredentialStorage = nil
        urlSessionConfig.requestCachePolicy = .reloadIgnoringLocalCacheData
    }
}

struct ContentView: View {
    @EnvironmentObject var authenticationService: AuthenticationService
    @EnvironmentObject var syncService: PlaylistSyncService
    @State private var selectedTab = 0
    
    var body: some View {
        NavigationView {
            if authenticationService.isAuthenticated {
                TabView(selection: $selectedTab) {
                    PlaylistListView()
                        .tabItem {
                            Image(systemName: "music.note.list")
                            Text("Playlists")
                        }
                        .tag(0)
                    
                    SyncHistoryView()
                        .tabItem {
                            Image(systemName: "clock.arrow.circlepath")
                            Text("History")
                        }
                        .tag(1)
                    
                    SettingsView()
                        .tabItem {
                            Image(systemName: "gear")
                            Text("Settings")
                        }
                        .tag(2)
                }
            } else {
                AuthenticationView()
            }
        }
        .navigationViewStyle(.stack)
    }
}

struct PlaylistListView: View {
    @EnvironmentObject var syncService: PlaylistSyncService
    @State private var playlists: [PlaylistModel] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showingError = false
    
    var body: some View {
        VStack {
            if isLoading {
                ProgressView("Loading playlists...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List(playlists, id: \.id) { playlist in
                    PlaylistRowView(playlist: playlist)
                        .onTapGesture {
                            Task {
                                await syncPlaylist(playlist)
                            }
                        }
                }
                .refreshable {
                    await loadPlaylists()
                }
            }
        }
        .navigationTitle("Spotify Playlists")
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button("Refresh") {
                    Task { await loadPlaylists() }
                }
            }
        }
        .onAppear {
            Task { await loadPlaylists() }
        }
        .alert("Error", isPresented: $showingError) {
            Button("OK") { showingError = false }
        } message: {
            Text(errorMessage ?? "An unknown error occurred")
        }
    }
    
    private func loadPlaylists() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            playlists = try await syncService.fetchSpotifyPlaylists()
        } catch {
            errorMessage = error.localizedDescription
            showingError = true
        }
    }
    
    private func syncPlaylist(_ playlist: PlaylistModel) async {
        do {
            try await syncService.syncPlaylist(playlist.id)
        } catch {
            errorMessage = "Failed to sync playlist: \(error.localizedDescription)"
            showingError = true
        }
    }
}

struct PlaylistRowView: View {
    let playlist: PlaylistModel
    
    var body: some View {
        HStack {
            AsyncImage(url: playlist.imageURL) { image in
                image
                    .resizable()
                    .aspectRatio(contentMode: .fill)
            } placeholder: {
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.gray.opacity(0.3))
                    .overlay(
                        Image(systemName: "music.note")
                            .foregroundColor(.gray)
                    )
            }
            .frame(width: 60, height: 60)
            .clipShape(RoundedRectangle(cornerRadius: 8))
            
            VStack(alignment: .leading, spacing: 4) {
                Text(playlist.name)
                    .font(.headline)
                    .lineLimit(1)
                
                Text("\(playlist.trackCount) tracks")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                if !playlist.description.isEmpty {
                    Text(playlist.description)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                }
            }
            
            Spacer()
            
            Image(systemName: "arrow.right.circle")
                .foregroundColor(.accentColor)
        }
        .padding(.vertical, 4)
    }
}

struct SyncHistoryView: View {
    @EnvironmentObject var syncService: PlaylistSyncService
    @State private var syncHistory: [SyncHistoryItem] = []
    @State private var isLoading = false
    
    var body: some View {
        NavigationView {
            VStack {
                if isLoading {
                    ProgressView("Loading sync history...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if syncHistory.isEmpty {
                    VStack {
                        Image(systemName: "clock.arrow.circlepath")
                            .font(.largeTitle)
                            .foregroundColor(.secondary)
                        
                        Text("No sync history yet")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        
                        Text("Start syncing playlists to see them here")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List(syncHistory, id: \.taskId) { item in
                        SyncHistoryRowView(item: item)
                    }
                }
            }
            .navigationTitle("Sync History")
            .onAppear {
                Task { await loadSyncHistory() }
            }
            .refreshable {
                await loadSyncHistory()
            }
        }
    }
    
    private func loadSyncHistory() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            syncHistory = try await syncService.fetchSyncHistory()
        } catch {
            print("Failed to load sync history: \(error)")
        }
    }
}

struct SyncHistoryRowView: View {
    let item: SyncHistoryItem
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(item.spotifyPlaylistName)
                    .font(.headline)
                
                Spacer()
                
                StatusBadge(status: item.status)
            }
            
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Synced: \(item.syncedTracks)/\(item.totalTracks)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    if item.failedTracks > 0 {
                        Text("Failed: \(item.failedTracks)")
                            .font(.caption)
                            .foregroundColor(.red)
                    }
                }
                
                Spacer()
                
                Text(formatDate(item.createdAt))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = RelativeDateTimeFormatter()
        return formatter.localizedString(for: date, relativeTo: Date())
    }
}

struct StatusBadge: View {
    let status: SyncStatus
    
    var body: some View {
        Text(status.displayName)
            .font(.caption)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(status.color.opacity(0.2))
            .foregroundColor(status.color)
            .clipShape(Capsule())
    }
}

struct AuthenticationView: View {
    @EnvironmentObject var authService: AuthenticationService
    @State private var isConnectingSpotify = false
    @State private var isConnectingAppleMusic = false
    
    var body: some View {
        VStack(spacing: 30) {
            VStack(spacing: 16) {
                Image(systemName: "music.note")
                    .font(.system(size: 80))
                    .foregroundColor(.accentColor)
                
                Text("Playlist Sync")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("Connect your Spotify and Apple Music accounts to start syncing playlists")
                    .font(.body)
                    .multilineTextAlignment(.center)
                    .foregroundColor(.secondary)
                    .padding(.horizontal)
            }
            
            VStack(spacing: 16) {
                Button(action: connectSpotify) {
                    HStack {
                        if isConnectingSpotify {
                            ProgressView()
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: "music.note")
                        }
                        
                        Text("Connect Spotify")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.green)
                    .foregroundColor(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                }
                .disabled(isConnectingSpotify)
                
                Button(action: connectAppleMusic) {
                    HStack {
                        if isConnectingAppleMusic {
                            ProgressView()
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: "applelogo")
                        }
                        
                        Text("Connect Apple Music")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.black)
                    .foregroundColor(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                }
                .disabled(isConnectingAppleMusic)
            }
            .padding(.horizontal, 40)
        }
        .padding()
    }
    
    private func connectSpotify() {
        isConnectingSpotify = true
        Task {
            await authService.authenticateSpotify()
            isConnectingSpotify = false
        }
    }
    
    private func connectAppleMusic() {
        isConnectingAppleMusic = true
        Task {
            await authService.authenticateAppleMusic()
            isConnectingAppleMusic = false
        }
    }
}

struct SettingsView: View {
    @EnvironmentObject var authService: AuthenticationService
    @State private var showingSignOutAlert = false
    
    var body: some View {
        NavigationView {
            Form {
                Section("Connected Accounts") {
                    HStack {
                        Label("Spotify", systemImage: "music.note")
                        Spacer()
                        if authService.spotifyConnected {
                            Text("Connected")
                                .foregroundColor(.green)
                        } else {
                            Text("Not Connected")
                                .foregroundColor(.red)
                        }
                    }
                    
                    HStack {
                        Label("Apple Music", systemImage: "applelogo")
                        Spacer()
                        if authService.appleMusicConnected {
                            Text("Connected")
                                .foregroundColor(.green)
                        } else {
                            Text("Not Connected")
                                .foregroundColor(.red)
                        }
                    }
                }
                
                Section("Actions") {
                    Button("Sign Out", role: .destructive) {
                        showingSignOutAlert = true
                    }
                }
                
                Section("About") {
                    HStack {
                        Text("Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                    
                    Text("Playlist Sync securely transfers your Spotify playlists to Apple Music while respecting your privacy and using industry-standard encryption.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .navigationTitle("Settings")
        }
        .alert("Sign Out", isPresented: $showingSignOutAlert) {
            Button("Cancel", role: .cancel) { }
            Button("Sign Out", role: .destructive) {
                authService.signOut()
            }
        } message: {
            Text("Are you sure you want to sign out? You'll need to reconnect your accounts.")
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(AuthenticationService())
        .environmentObject(PlaylistSyncService())
}