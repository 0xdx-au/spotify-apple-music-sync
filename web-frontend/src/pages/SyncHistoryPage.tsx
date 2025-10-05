import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  IconButton,
  Alert,
  CircularProgress,
  Stack,
  Divider,
} from '@mui/material';
import {
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  CloudSync,
  Refresh,
  PlaylistPlay,
} from '@mui/icons-material';
import { playlistApi, SyncTask } from '../services/api';

const SyncHistoryPage: React.FC = () => {
  const [syncHistory, setSyncHistory] = useState<SyncTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSyncHistory();
    
    // Auto-refresh every 10 seconds for active syncs
    const interval = setInterval(() => {
      const hasActiveSyncs = syncHistory.some(sync => 
        sync.status === 'pending' || sync.status === 'in_progress'
      );
      
      if (hasActiveSyncs) {
        loadSyncHistory();
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [syncHistory]);

  const loadSyncHistory = async () => {
    try {
      setError(null);
      const data = await playlistApi.getSyncHistory();
      setSyncHistory(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load sync history');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'partial':
        return <Warning color="warning" />;
      case 'in_progress':
        return <CloudSync color="primary" sx={{ animation: 'rotation 2s infinite linear' }} />;
      default:
        return <CloudSync color="disabled" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'partial':
        return 'warning';
      case 'in_progress':
        return 'primary';
      default:
        return 'default';
    }
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const durationMs = end.getTime() - start.getTime();
    const durationSec = Math.floor(durationMs / 1000);
    
    if (durationSec < 60) {
      return `${durationSec}s`;
    } else if (durationSec < 3600) {
      return `${Math.floor(durationSec / 60)}m ${durationSec % 60}s`;
    } else {
      const hours = Math.floor(durationSec / 3600);
      const minutes = Math.floor((durationSec % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  };

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
          Sync History
        </Typography>
        <IconButton
          onClick={loadSyncHistory}
          disabled={loading}
          sx={{ ml: 2 }}
        >
          <Refresh />
        </IconButton>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <style>
        {`
          @keyframes rotation {
            from {
              transform: rotate(0deg);
            }
            to {
              transform: rotate(359deg);
            }
          }
        `}
      </style>

      <Stack spacing={3}>
        {syncHistory.length === 0 ? (
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <PlaylistPlay sx={{ fontSize: 64, color: 'grey.500', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No sync history yet
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Start syncing playlists to see them here
              </Typography>
            </CardContent>
          </Card>
        ) : (
          syncHistory.map((sync) => (
            <Card key={sync.task_id}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 3 }}>
                  <Box sx={{ mt: 0.5 }}>
                    {getStatusIcon(sync.status)}
                  </Box>
                  
                  <Box sx={{ flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Typography variant="h6" component="h2">
                        {sync.spotify_playlist.name}
                      </Typography>
                      <Chip
                        label={sync.status.replace('_', ' ')}
                        color={getStatusColor(sync.status) as any}
                        size="small"
                        variant="outlined"
                      />
                    </Box>

                    <Box sx={{ 
                      display: 'grid', 
                      gridTemplateColumns: {
                        xs: 'repeat(2, 1fr)',
                        sm: 'repeat(4, 1fr)'
                      },
                      gap: 2,
                      mb: 2
                    }}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Total Tracks
                        </Typography>
                        <Typography variant="body1" fontWeight={600}>
                          {sync.total_tracks}
                        </Typography>
                      </Box>
                      
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Synced
                        </Typography>
                        <Typography variant="body1" fontWeight={600} color="success.main">
                          {sync.synced_tracks}
                        </Typography>
                      </Box>
                      
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Failed
                        </Typography>
                        <Typography variant="body1" fontWeight={600} color="error.main">
                          {sync.failed_tracks}
                        </Typography>
                      </Box>
                      
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Success Rate
                        </Typography>
                        <Typography variant="body1" fontWeight={600}>
                          {sync.total_tracks > 0 
                            ? Math.round((sync.synced_tracks / sync.total_tracks) * 100)
                            : 0
                          }%
                        </Typography>
                      </Box>
                    </Box>

                    {sync.status === 'in_progress' && (
                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            Progress
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {sync.progress}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={sync.progress} 
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                      </Box>
                    )}

                    <Divider sx={{ my: 2 }} />

                    <Box sx={{ 
                      display: 'grid', 
                      gridTemplateColumns: {
                        xs: '1fr',
                        sm: 'repeat(2, 1fr)'
                      },
                      gap: 2
                    }}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Started
                        </Typography>
                        <Typography variant="body2">
                          {new Date(sync.created_at).toLocaleString()}
                        </Typography>
                      </Box>
                      
                      {sync.completed_at && (
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Completed
                          </Typography>
                          <Typography variant="body2">
                            {new Date(sync.completed_at).toLocaleString()}
                          </Typography>
                        </Box>
                      )}
                      
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Duration
                        </Typography>
                        <Typography variant="body2">
                          {formatDuration(sync.created_at, sync.completed_at)}
                        </Typography>
                      </Box>
                      
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Task ID
                        </Typography>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                          {sync.task_id}
                        </Typography>
                      </Box>
                    </Box>

                    {sync.apple_music_playlist && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          Apple Music Playlist
                        </Typography>
                        <Typography variant="body2">
                          {sync.apple_music_playlist.name}
                        </Typography>
                      </Box>
                    )}

                    {sync.error_message && (
                      <Alert severity="error" sx={{ mt: 2 }}>
                        {sync.error_message}
                      </Alert>
                    )}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          ))
        )}
      </Stack>
    </Box>
  );
};

export default SyncHistoryPage;