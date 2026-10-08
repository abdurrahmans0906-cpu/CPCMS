import React, { createContext, useContext, useEffect, useState } from 'react';
import { apiRequest, setAccessToken, getAccessToken, SchemaUserOut } from '../api/client';

interface AuthContextType {
  user: SchemaUserOut | null;
  role: 'STUDENT' | 'FACULTY' | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, user: SchemaUserOut) => void;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  role: null,
  isAuthenticated: false,
  isLoading: true,
  login: () => {},
  logout: async () => {},
  refreshUser: async () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<SchemaUserOut | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    try {
      const data = await apiRequest<SchemaUserOut>('/auth/me');
      setUser(data);
    } catch {
      setUser(null);
      setAccessToken(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const token = getAccessToken();
    if (token) {
      refreshUser();
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = (token: string, userData: SchemaUserOut) => {
    setAccessToken(token);
    setUser(userData);
  };

  const logout = async () => {
    try {
      await apiRequest('/auth/logout', { method: 'POST' });
    } catch {
      // Ignore network error on logout
    }
    setAccessToken(null);
    setUser(null);
  };

  const role = user ? (user.role as 'STUDENT' | 'FACULTY') : null;

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
