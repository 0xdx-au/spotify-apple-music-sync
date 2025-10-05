import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface Playlist {
  id: string;
  name: string;
  description?: string;
  track_count: number;
  owner: string;
  public: boolean;
  collaborative: boolean;
  external_urls: Record<string, string>;
  images: Array<{
    url: string;
    height?: number;
    width?: number;
  }>;
}

export interface SyncTask {
  task_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'partial';
  progress: number;
  total_tracks: number;
  synced_tracks: number;
  failed_tracks: number;
  spotify_playlist: Playlist;
  apple_music_playlist?: Playlist;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface SyncRequest {
  spotify_playlist_id: string;
  create_new_playlist: boolean;
  apple_music_playlist_name?: string;
  include_unavailable_tracks: boolean;
}

export interface SyncResponse {
  task_id: string;
  status: string;
  message: string;
  created_at: string;
}

// Helper function to check if user is in demo mode
const isDemoMode = (): boolean => {
  const token = localStorage.getItem('auth_token');
  if (!token) return false;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.demo_mode || false;
  } catch {
    return false;
  }
};

export const playlistApi = {
  getSpotifyPlaylists: (): Promise<Playlist[]> => {
    const endpoint = isDemoMode() ? '/api/demo/playlists' : '/api/spotify/playlists';
    return apiClient.get(endpoint).then(response => response.data);
  },
    
  syncPlaylist: (request: SyncRequest): Promise<SyncResponse> => {
    const endpoint = isDemoMode() ? '/api/demo/sync' : '/api/sync/playlist';
    return apiClient.post(endpoint, request).then(response => response.data);
  },
    
  getSyncStatus: (taskId: string): Promise<SyncTask> =>
    apiClient.get(`/api/sync/status/${taskId}`).then(response => response.data),
    
  getSyncHistory: (): Promise<SyncTask[]> => {
    const endpoint = isDemoMode() ? '/api/demo/history' : '/api/sync/history';
    return apiClient.get(endpoint).then(response => response.data);
  },
};

export const authApi = {
  getUserProfile: () =>
    apiClient.get('/api/user/profile').then(response => response.data),
    
  connectService: (provider: 'spotify' | 'apple-music') =>
    apiClient.post(`/api/auth/connect/${provider}`).then(response => response.data),
    
  disconnectService: (provider: 'spotify' | 'apple-music') =>
    apiClient.delete(`/api/auth/disconnect/${provider}`).then(response => response.data),
};