import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Container,
  Stack,
  useTheme,
  Divider,
} from '@mui/material';
import { MusicNote } from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';

const LoginPage: React.FC = () => {
  const theme = useTheme();
  const { login, loading } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [currentProvider, setCurrentProvider] = useState<'spotify' | 'apple-music' | null>(null);

  const handleLogin = async (provider: 'spotify' | 'apple-music') => {
    try {
      setError(null);
      setCurrentProvider(provider);
      await login(provider);
    } catch (err: any) {
      setError(err.message || `Failed to authenticate with ${provider}`);
      setCurrentProvider(null);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '80vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <Card
          sx={{
            width: '100%',
            maxWidth: 500,
            p: 4,
            textAlign: 'center',
          }}
        >
          <CardContent>
            <Box sx={{ mb: 4 }}>
              <MusicNote sx={{ fontSize: 64, color: theme.palette.primary.main, mb: 2 }} />
              <Typography variant="h3" component="h1" gutterBottom fontWeight={700}>
                PlaylistSync
              </Typography>
              <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
                Seamlessly sync your playlists between Spotify and Apple Music
              </Typography>
            </Box>

            <Stack spacing={3}>
              <Box>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                  Connect your accounts to start syncing playlists
                </Typography>
              </Box>

              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}

              <Stack spacing={2}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={() => handleLogin('spotify')}
                  disabled={loading}
                  startIcon={
                    loading && currentProvider === 'spotify' ? (
                      <CircularProgress size={20} color="inherit" />
                    ) : null
                  }
                  sx={{
                    bgcolor: '#1db954',
                    color: 'white',
                    py: 1.5,
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    '&:hover': {
                      bgcolor: '#1ed760',
                    },
                    '&:disabled': {
                      bgcolor: 'rgba(29, 185, 84, 0.5)',
                    },
                  }}
                >
                  {loading && currentProvider === 'spotify' 
                    ? 'Connecting to Spotify...' 
                    : 'Connect with Spotify'
                  }
                </Button>

                <Divider sx={{ my: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    OR
                  </Typography>
                </Divider>

                <Button
                  variant="contained"
                  size="large"
                  onClick={() => handleLogin('apple-music')}
                  disabled={loading}
                  startIcon={
                    loading && currentProvider === 'apple-music' ? (
                      <CircularProgress size={20} color="inherit" />
                    ) : null
                  }
                  sx={{
                    bgcolor: '#ff6b6b',
                    color: 'white',
                    py: 1.5,
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    '&:hover': {
                      bgcolor: '#ff8a80',
                    },
                    '&:disabled': {
                      bgcolor: 'rgba(255, 107, 107, 0.5)',
                    },
                  }}
                >
                  {loading && currentProvider === 'apple-music' 
                    ? 'Connecting to Apple Music...' 
                    : 'Connect with Apple Music'
                  }
                </Button>
              </Stack>

              <Box sx={{ mt: 4, pt: 3, borderTop: 1, borderColor: 'divider' }}>
                <Typography variant="body2" color="text.secondary">
                  You can connect to either service first, then link the other service later.
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Secure • Private • TLS 1.3 Encrypted
          </Typography>
        </Box>
      </Box>
    </Container>
  );
};

export default LoginPage;