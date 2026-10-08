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
      <Link to="/" className="top-bar-title">
        <span className="top-bar-logo">CP</span>
        <span>CPCMS</span>
      </Link>
      {user && (
        <div className="top-bar-right">
          <div className="user-pill">
            <span>{user.name}</span>
            <span className={`user-role-badge ${user.role.toLowerCase()}`}>
              {user.role}
            </span>
          </div>

          <Link to="/notifications" className="notif-btn">
            <span>Notifications</span>
            {unreadCount > 0 && <span className="notif-badge">{unreadCount}</span>}
          </Link>

          <button type="button" className="logout-btn" onClick={handleLogout}>
            Log out
          </button>
        </div>
      )}
    </header>
  );
};
