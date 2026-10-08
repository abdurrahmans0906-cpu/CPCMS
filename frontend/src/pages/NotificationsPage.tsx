import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '../api/client';
import { Breadcrumbs } from '../components/Breadcrumbs';

export interface NotificationItem {
  id: string;
  user_id: string;
  kind: string;
  message: string;
  link?: string | null;
  is_read: boolean;
  created_at: string;
}

export const NotificationsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const { data: notifications, isLoading, error } = useQuery<NotificationItem[]>({
    queryKey: ['notifications', filter],
    queryFn: () => apiRequest<NotificationItem[]>(`/notifications?unread_only=${filter === 'unread'}`),
  });

  const markReadMutation = useMutation({
    mutationFn: (notifId: string) =>
      apiRequest(`/notifications/${notifId}/read`, {
        method: 'POST',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-notifications-count'] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () =>
      apiRequest('/notifications/mark-all-read', {
        method: 'POST',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-notifications-count'] });
    },
  });

  if (isLoading) return <div>Loading...</div>;

  const unreadCount = notifications ? notifications.filter((n) => !n.is_read).length : 0;

  return (
    <div>
      <Breadcrumbs
        items={[
          { label: 'Dashboard', to: '/' },
          { label: 'Notifications' },
        ]}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h1 style={{ margin: 0 }}>Notifications</h1>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setFilter(filter === 'all' ? 'unread' : 'all')}
          >
            {filter === 'all' ? 'Show Unread Only' : 'Show All'}
          </button>
          {unreadCount > 0 && (
            <button
              className="primary"
              onClick={() => markAllReadMutation.mutate()}
              disabled={markAllReadMutation.isPending}
            >
              Mark All as Read
            </button>
          )}
        </div>
      </div>

      {error && <div className="banner banner-error">{(error as any).message || 'Failed to load notifications.'}</div>}

      <div className="panel">
        {!notifications || notifications.length === 0 ? (
          <p className="muted">No notifications found.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th style={{ width: '120px' }}>Category</th>
                <th>Message</th>
                <th style={{ width: '160px' }}>Date</th>
                <th style={{ width: '100px' }}>Status</th>
                <th style={{ width: '100px' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {notifications.map((n) => (
                <tr
                  key={n.id}
                  style={{
                    backgroundColor: n.is_read ? 'transparent' : '#fcfcfa',
                    fontWeight: n.is_read ? 400 : 600,
                  }}
                >
                  <td>
                    <span style={{ fontSize: '11px', border: '1px solid var(--color-border)', padding: '2px 4px' }}>
                      {n.kind.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    {n.link ? (
                      <Link to={n.link} style={{ color: 'inherit', textDecoration: 'none' }}>
                        {n.message}
                      </Link>
                    ) : (
                      n.message
                    )}
                  </td>
                  <td style={{ fontSize: '12px' }} className="muted">
                    {new Date(n.created_at).toLocaleString()}
                  </td>
                  <td>
                    {n.is_read ? (
                      <span className="muted" style={{ fontSize: '12px' }}>Read</span>
                    ) : (
                      <span style={{ color: 'var(--color-accent)', fontSize: '12px', fontWeight: 600 }}>Unread</span>
                    )}
                  </td>
                  <td>
                    {!n.is_read && (
                      <button
                        style={{ padding: '2px 6px', fontSize: '12px' }}
                        onClick={() => markReadMutation.mutate(n.id)}
                        disabled={markReadMutation.isPending}
                      >
                        Mark read
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default NotificationsPage;
