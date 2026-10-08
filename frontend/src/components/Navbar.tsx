import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/AuthContext';
import { useQuery } from '@tanstack/react-query';
import { apiRequest } from '../api/client';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const { data: notifData } = useQuery<{ unread_count: number; items: any[] }>({
    queryKey: ['notifications'],
    queryFn: () => apiRequest('/notifications'),
    refetchInterval: 30000,
    enabled: !!user,
  });

  const unreadCount = notifData?.unread_count ?? 0;

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="top-bar">
      <Link to="/" className="top-bar-title">CPCMS</Link>
      {user && (
        <div className="top-bar-right">
          <span>{user.name} ({user.role})</span>
          <Link to="/notifications" style={{ textDecoration: 'none', color: 'inherit' }}>
            Notifications ({unreadCount})
          </Link>
          <button type="button" onClick={handleLogout}>Log out</button>
        </div>
      )}
    </header>
  );
};
