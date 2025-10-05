import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Avatar,
  Stack,
  Alert,
  LinearProgress,
  Divider,
} from '@mui/material';
import Grid from '@mui/material/Unstable_Grid2';
import {
  PlaylistPlay,
  History,
  CloudSync,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import { playlistApi, SyncTask } from '../services/api';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [recentSyncs, setRecentSyncs] = useState<SyncTask[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRecentSyncs();
  }, []);

  const loadRecentSyncs = async () => {
    try {
      const history = await playlistApi.getSyncHistory();
      setRecentSyncs(history.slice(0, 3)); // Show last 3 syncs
    } catch (error) {
      console.error('Failed to load sync history:', error);
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
        return <CloudSync color="primary" />;
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

  if (!user) return null;

  const canSync = user.spotifyConnected && user.appleMusicConnected;

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom fontWeight={700}>
        Welcome back, {user.displayName}!
      </Typography>
      
      <Grid container spacing={3} sx={{ mt: 2 }}>
        {/* Account Status */}
        <Grid xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Account Status
              </Typography>
              
              <Stack spacing={3}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Avatar sx={{ bgcolor: '#1db954' }}>S</Avatar>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="body1">Spotify</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Music streaming service
                    </Typography>
                  </Box>
                  <Chip
                    label={user.spotifyConnected ? 'Connected' : 'Not Connected'}
                    color={user.spotifyConnected ? 'success' : 'error'}
                    variant={user.spotifyConnected ? 'filled' : 'outlined'}
                  />
                </Box>

                <Divider />

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Avatar sx={{ bgcolor: '#ff6b6b' }}>A</Avatar>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="body1">Apple Music</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Apple's music service
                    </Typography>
                  </Box>
                  <Chip
                    label={user.appleMusicConnected ? 'Connected' : 'Not Connected'}
                    color={user.appleMusicConnected ? 'success' : 'error'}
                    variant={user.appleMusicConnected ? 'filled' : 'outlined'}
                  />
                </Box>

                {!canSync && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    Connect both services to start syncing playlists between them.
                  </Alert>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              
              <Stack spacing={2}>
                <Button
                  variant="contained"
                  startIcon={<PlaylistPlay />}
                  onClick={() => navigate('/playlists')}
                  disabled={!canSync}
                  size="large"
                  fullWidth
                >
                  Browse & Sync Playlists
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<History />}
                  onClick={() => navigate('/history')}
                  size="large"
                  fullWidth
                >
                  View Sync History
                </Button>

                {!user.spotifyConnected && (
                  <Button
                    variant="outlined"
                    onClick={() => {/* Handle connect Spotify */}}
                    size="medium"
                    sx={{ color: '#1db954', borderColor: '#1db954' }}
                  >
                    Connect Spotify
                  </Button>
                )}

                {!user.appleMusicConnected && (
                  <Button
                    variant="outlined"
                    onClick={() => {/* Handle connect Apple Music */}}
                    size="medium"
                    sx={{ color: '#ff6b6b', borderColor: '#ff6b6b' }}
                  >
                    Connect Apple Music
                  </Button>
                )}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Sync Activity */}
        <Grid xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">
                  Recent Sync Activity
                </Typography>
                <Button
                  variant="text"
                  onClick={() => navigate('/history')}
                  size="small"
                >
                  View All
                </Button>
              </Box>

              {loading ? (
                <LinearProgress />
              ) : recentSyncs.length === 0 ? (
                <Alert severity="info">
                  No sync activity yet. Start by syncing a playlist!
                </Alert>
              ) : (
                <Stack spacing={2}>
                  {recentSyncs.map((sync) => (
                    <Box
                      key={sync.task_id}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 2,
                        p: 2,
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 2,
                      }}
                    >
                      {getStatusIcon(sync.status)}
                      
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="body1" fontWeight={600}>
                          {sync.spotify_playlist.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {sync.synced_tracks}/{sync.total_tracks} tracks synced
                        </Typography>
                      </Box>

                      <Box sx={{ textAlign: 'right' }}>
                        <Chip
                          label={sync.status.replace('_', ' ')}
                          color={getStatusColor(sync.status) as any}
                          size="small"
                          variant="outlined"
                        />
                        <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 0.5 }}>
                          {new Date(sync.created_at).toLocaleDateString()}
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage;