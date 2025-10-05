import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Box,
  Chip,
  useTheme,
} from '@mui/material';
import {
  MusicNote,
  Dashboard,
  PlaylistPlay,
  History,
  AccountCircle,
  ExitToApp,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';

const Header: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleUserMenuClose();
    logout();
    navigate('/login');
  };

  const navigationItems = [
    { path: '/dashboard', label: 'Dashboard', icon: Dashboard },
    { path: '/playlists', label: 'Playlists', icon: PlaylistPlay },
    { path: '/history', label: 'History', icon: History },
  ];

  return (
    <AppBar position="static" elevation={0} sx={{ bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', mr: 4 }}>
          <MusicNote sx={{ mr: 1, color: theme.palette.primary.main }} />
          <Typography
            variant="h6"
            component="div"
            sx={{
              fontWeight: 700,
              color: 'text.primary',
              cursor: 'pointer',
            }}
            onClick={() => navigate('/')}
          >
            PlaylistSync
          </Typography>
        </Box>

        {isAuthenticated && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexGrow: 1 }}>
            {navigationItems.map(({ path, label, icon: Icon }) => (
              <Button
                key={path}
                startIcon={<Icon />}
                onClick={() => navigate(path)}
                variant={location.pathname === path ? 'contained' : 'text'}
                size="medium"
                sx={{
                  minWidth: 100,
                  ...(location.pathname === path && {
                    bgcolor: theme.palette.primary.main,
                    color: 'white',
                    '&:hover': {
                      bgcolor: theme.palette.primary.dark,
                    },
                  }),
                }}
              >
                {label}
              </Button>
            ))}
          </Box>
        )}

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, ml: 'auto' }}>
          {isAuthenticated && user && (
            <>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Chip
                  label="Spotify"
                  variant={user.spotifyConnected ? 'filled' : 'outlined'}
                  color={user.spotifyConnected ? 'primary' : 'default'}
                  size="small"
                />
                <Chip
                  label="Apple Music"
                  variant={user.appleMusicConnected ? 'filled' : 'outlined'}
                  color={user.appleMusicConnected ? 'secondary' : 'default'}
                  size="small"
                />
              </Box>
              
              <IconButton
                onClick={handleUserMenuOpen}
                size="small"
                sx={{ ml: 2 }}
                aria-controls={Boolean(anchorEl) ? 'account-menu' : undefined}
                aria-haspopup="true"
                aria-expanded={Boolean(anchorEl) ? 'true' : undefined}
              >
                {user.avatar ? (
                  <Avatar src={user.avatar} sx={{ width: 32, height: 32 }} />
                ) : (
                  <AccountCircle sx={{ fontSize: 32, color: 'text.primary' }} />
                )}
              </IconButton>

              <Menu
                anchorEl={anchorEl}
                id="account-menu"
                open={Boolean(anchorEl)}
                onClose={handleUserMenuClose}
                onClick={handleUserMenuClose}
                PaperProps={{
                  elevation: 0,
                  sx: {
                    overflow: 'visible',
                    filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
                    mt: 1.5,
                    '& .MuiAvatar-root': {
                      width: 32,
                      height: 32,
                      ml: -0.5,
                      mr: 1,
                    },
                    '&:before': {
                      content: '""',
                      display: 'block',
                      position: 'absolute',
                      top: 0,
                      right: 14,
                      width: 10,
                      height: 10,
                      bgcolor: 'background.paper',
                      transform: 'translateY(-50%) rotate(45deg)',
                      zIndex: 0,
                    },
                  },
                }}
                transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
              >
                <MenuItem sx={{ minWidth: 200 }}>
                  <Box>
                    <Typography variant="subtitle2" fontWeight={600}>
                      {user.displayName}
                    </Typography>
                    {user.email && (
                      <Typography variant="caption" color="text.secondary">
                        {user.email}
                      </Typography>
                    )}
                  </Box>
                </MenuItem>
                <MenuItem onClick={handleLogout}>
                  <ExitToApp sx={{ mr: 1 }} />
                  Logout
                </MenuItem>
              </Menu>
            </>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;