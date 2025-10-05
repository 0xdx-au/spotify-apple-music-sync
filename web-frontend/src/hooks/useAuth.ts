import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';

// Import the type definition
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

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Export the context for direct access if needed
export { AuthContext } from '../contexts/AuthContext';