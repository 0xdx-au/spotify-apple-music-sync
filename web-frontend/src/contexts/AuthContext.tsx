import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '../services/api';

interface User {
  id: string;
  displayName: string;
  email?: string;
  spotifyConnected: boolean;
  appleMusicConnected: boolean;
  avatar?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (provider: 'spotify' | 'apple-music') => Promise<void>;
  logout: () => void;
  refreshAuth: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    if (storedToken) {
      setToken(storedToken);
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
      loadUserProfile();
    } else {
      setLoading(false);
    }
  }, []);

  const loadUserProfile = async () => {
    try {
      const response = await apiClient.get('/api/user/profile');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to load user profile:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (provider: 'spotify' | 'apple-music') => {
    try {
      setLoading(true);
      
      // Redirect to OAuth provider
      const authUrl = `${process.env.REACT_APP_API_URL}/api/auth/${provider}`;
      
      // Open popup window for OAuth
      const popup = window.open(
        authUrl,
        'oauth',
        'width=600,height=700,scrollbars=yes,resizable=yes'
      );

      // Listen for OAuth completion
      return new Promise<void>((resolve, reject) => {
        const checkClosed = setInterval(() => {
          if (popup?.closed) {
            clearInterval(checkClosed);
            
            // Check if we received an auth token
            const authToken = localStorage.getItem('temp_auth_token');
            if (authToken) {
              localStorage.removeItem('temp_auth_token');
              localStorage.setItem('auth_token', authToken);
              setToken(authToken);
              apiClient.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
              loadUserProfile().then(() => resolve());
            } else {
              setLoading(false);
              reject(new Error('Authentication cancelled'));
            }
          }
        }, 1000);

        // Handle messages from popup
        const messageHandler = (event: MessageEvent) => {
          if (event.origin !== window.location.origin) return;
          
          if (event.data.type === 'AUTH_SUCCESS') {
            clearInterval(checkClosed);
            popup?.close();
            
            const { token: authToken } = event.data;
            localStorage.setItem('auth_token', authToken);
            setToken(authToken);
            apiClient.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
            loadUserProfile().then(() => resolve());
          } else if (event.data.type === 'AUTH_ERROR') {
            clearInterval(checkClosed);
            popup?.close();
            setLoading(false);
            reject(new Error(event.data.error));
          }
        };

        window.addEventListener('message', messageHandler);
        
        // Cleanup on timeout
        setTimeout(() => {
          clearInterval(checkClosed);
          window.removeEventListener('message', messageHandler);
          if (!popup?.closed) {
            popup?.close();
            setLoading(false);
            reject(new Error('Authentication timeout'));
          }
        }, 300000); // 5 minute timeout
      });
    } catch (error) {
      setLoading(false);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('temp_auth_token');
    setToken(null);
    setUser(null);
    delete apiClient.defaults.headers.common['Authorization'];
  };

  const refreshAuth = async () => {
    if (!token) return;
    await loadUserProfile();
  };

  const isAuthenticated = !!(user && token);

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated,
    loading,
    login,
    logout,
    refreshAuth,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}