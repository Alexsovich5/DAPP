import React, { createContext, useState, useContext, useEffect, ReactNode, useMemo } from 'react';
import api from '../services/api';

// Type definitions
interface User {
  _id: string;
  email: string;
  firstName: string;
  lastName: string;
  profilePicture?: string;
  dateOfBirth: string;
  gender: string;
  isProfileComplete: boolean;
  bio?: string;
  interests?: string[];
  dietaryPreferences?: string[];
  locationPreferences?: {
    city?: string;
    maxDistance?: number;
    coordinates?: {
      latitude: number;
      longitude: number;
    };
  };
  matchPreferences?: {
    ageRange?: {
      min: number;
      max: number;
    };
    genders?: string[];
  };
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (userData: Partial<User>) => Promise<void>;
  clearError: () => void;
}

interface AuthProviderProps {
  children: ReactNode;
}

interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  gender: string;
  dietaryPreferences?: string[]; // Added dietaryPreferences
  cuisinePreferences?: string; // Added cuisinePreferences
  location?: string; // Added location
  lookingFor?: string; // Added lookingFor
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider component
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Check auth status on initial load
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const response = await api.get('/auth/me');
        
        if (response.data.success) {
          setUser(response.data.data.user);
          setIsAuthenticated(true);
        }
      } catch (err) {
        // Error handling is done by axios interceptor
        console.error('Auth check failed:', err);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await api.post('/auth/login', { email, password });
      
      if (response.data.success) {
        const { user } = response.data.data;
        setUser(user);
        setIsAuthenticated(true);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterData) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await api.post('/auth/register', userData);
      
      if (response.data.success) {
        const { user } = response.data.data;
        setUser(user);
        setIsAuthenticated(true);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      setIsLoading(true);
      await api.post('/auth/logout');
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
    }
  };

  const updateProfile = async (userData: Partial<User>) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await api.put('/profile', userData);
      
      if (response.data.success) {
        setUser(prev => prev ? { ...prev, ...response.data.data.user } : null);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Clear error function
  const clearError = () => {
    setError(null);
  };

  const contextValue = useMemo(() => ({
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    register,
    logout,
    updateProfile,
    clearError
  }), [user, isAuthenticated, isLoading, error]);

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook for using the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
export type { User };