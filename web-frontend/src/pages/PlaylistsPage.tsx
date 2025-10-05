import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardMedia,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';
import { CloudSync, PlaylistPlay, MusicNote } from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import { playlistApi, Playlist, SyncRequest } from '../services/api';

const PlaylistsPage: React.FC = () => {
  const { user } = useAuth();
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [syncDialog, setSyncDialog] = useState<{
    open: boolean;
    playlist: Playlist | null;
  }>({ open: false, playlist: null });
  const [syncOptions, setSyncOptions] = useState({
    createNewPlaylist: true,
    appleMusicPlaylistName: '',
    includeUnavailableTracks: false,
  });

  useEffect(() => {
    loadPlaylists();
  }, []);

  const loadPlaylists = async () => {
    try {
      setError(null);
      const data = await playlistApi.getSpotifyPlaylists();
      setPlaylists(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load playlists');
    } finally {
      setLoading(false);
    }
  };

  const handleSyncClick = (playlist: Playlist) => {
    setSyncOptions({
      createNewPlaylist: true,
      appleMusicPlaylistName: `${playlist.name} (from Spotify)`,
      includeUnavailableTracks: false,
    });
    setSyncDialog({ open: true, playlist });
  };

  const handleSyncConfirm = async () => {
    if (!syncDialog.playlist) return;

    try {
      setSyncing(syncDialog.playlist.id);
      
      const syncRequest: SyncRequest = {
        spotify_playlist_id: syncDialog.playlist.id,
        create_new_playlist: syncOptions.createNewPlaylist,
        apple_music_playlist_name: syncOptions.appleMusicPlaylistName || undefined,
        include_unavailable_tracks: syncOptions.includeUnavailableTracks,
      };

      const response = await playlistApi.syncPlaylist(syncRequest);
      
      // Close dialog and show success
      setSyncDialog({ open: false, playlist: null });
      
      // TODO: Show sync progress dialog or redirect to history
      alert(`Sync started! Task ID: ${response.task_id}`);
      
    } catch (err: any) {
      setError(err.message || 'Failed to start sync');
    } finally {
      setSyncing(null);
    }
  };

  const canSync = user?.spotifyConnected && user?.appleMusicConnected;

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress size={48} />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4" component="h1" fontWeight={700}>
          Your Spotify Playlists
        </Typography>
        <Button
          variant="outlined"
          onClick={loadPlaylists}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={16} /> : undefined}
        >
          Refresh
        </Button>
      </Box>

      {!canSync && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          You need to connect both Spotify and Apple Music to sync playlists.
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: {
          xs: '1fr',
          sm: 'repeat(2, 1fr)',
          md: 'repeat(3, 1fr)',
          lg: 'repeat(4, 1fr)'
        },
        gap: 3
      }}>
        {playlists.map((playlist) => (
          <Box key={playlist.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardMedia
                sx={{
                  height: 200,
                  bgcolor: 'grey.800',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {playlist.images && playlist.images.length > 0 ? (
                  <img
                    src={playlist.images[0].url}
                    alt={playlist.name}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                    }}
                  />
                ) : (
                  <MusicNote sx={{ fontSize: 64, color: 'grey.500' }} />
                )}
              </CardMedia>
              
              <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                <Typography variant="h6" component="h2" gutterBottom noWrap>
                  {playlist.name}
                </Typography>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2, flexGrow: 1 }}>
                  {playlist.description || 'No description'}
                </Typography>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Chip
                    label={`${playlist.track_count} tracks`}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={playlist.public ? 'Public' : 'Private'}
                    size="small"
                    variant="outlined"
                    color={playlist.public ? 'success' : 'default'}
                  />
                </Box>
                
                <Typography variant="caption" color="text.secondary" sx={{ mb: 2 }}>
                  By {playlist.owner}
                </Typography>

                <Button
                  variant="contained"
                  fullWidth
                  startIcon={syncing === playlist.id ? <CircularProgress size={16} /> : <CloudSync />}
                  onClick={() => handleSyncClick(playlist)}
                  disabled={!canSync || syncing === playlist.id}
                >
                  {syncing === playlist.id ? 'Syncing...' : 'Sync to Apple Music'}
                </Button>
              </CardContent>
            </Card>
          </Box>
        ))}
      </Box>

      {playlists.length === 0 && !loading && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <PlaylistPlay sx={{ fontSize: 64, color: 'grey.500', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No playlists found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Make sure you have playlists in your Spotify account
          </Typography>
        </Box>
      )}

      {/* Sync Dialog */}
      <Dialog open={syncDialog.open} onClose={() => setSyncDialog({ open: false, playlist: null })} maxWidth="sm" fullWidth>
        <DialogTitle>
          Sync Playlist: {syncDialog.playlist?.name}
        </DialogTitle>
        
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={syncOptions.createNewPlaylist}
                  onChange={(e) => setSyncOptions(prev => ({ 
                    ...prev, 
                    createNewPlaylist: e.target.checked 
                  }))}
                />
              }
              label="Create new Apple Music playlist"
            />
          </Box>

          <TextField
            fullWidth
            label="Apple Music playlist name"
            value={syncOptions.appleMusicPlaylistName}
            onChange={(e) => setSyncOptions(prev => ({ 
              ...prev, 
              appleMusicPlaylistName: e.target.value 
            }))}
            margin="normal"
            helperText="Leave empty to use the original name"
          />

          <Box sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={syncOptions.includeUnavailableTracks}
                  onChange={(e) => setSyncOptions(prev => ({ 
                    ...prev, 
                    includeUnavailableTracks: e.target.checked 
                  }))}
                />
              }
              label="Include unavailable tracks in sync report"
            />
          </Box>

          <Alert severity="info" sx={{ mt: 2 }}>
            Some tracks may not be available on Apple Music and will be skipped during sync.
          </Alert>
        </DialogContent>

        <DialogActions>
          <Button 
            onClick={() => setSyncDialog({ open: false, playlist: null })}
            disabled={syncing !== null}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleSyncConfirm}
            variant="contained"
            disabled={syncing !== null}
            startIcon={syncing ? <CircularProgress size={16} /> : <CloudSync />}
          >
            {syncing ? 'Starting Sync...' : 'Start Sync'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PlaylistsPage;