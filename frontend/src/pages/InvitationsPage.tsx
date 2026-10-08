import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '../api/client';
import { Breadcrumbs } from '../components/Breadcrumbs';

export const InvitationsPage: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: invitations, isLoading } = useQuery<any[]>({
    queryKey: ['invitations'],
    queryFn: () => apiRequest('/invitations'),
  });

  const acceptMutation = useMutation({
    mutationFn: (id: string) => apiRequest(`/invitations/${id}/accept`, { method: 'POST' }),
    onSuccess: (res: any) => {
      alert(res.message || 'Invitation accepted.');
      queryClient.invalidateQueries({ queryKey: ['invitations'] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: (err: any) => alert(err.message || 'Failed to accept invitation.'),
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) => apiRequest(`/invitations/${id}/reject`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invitations'] });
    },
    onError: (err: any) => alert(err.message || 'Failed to reject invitation.'),
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <Breadcrumbs items={[{ label: 'Dashboard', to: '/' }, { label: 'Invitations' }]} />
      <h1>Team Invitations</h1>

      <div className="panel">
        {!invitations || invitations.length === 0 ? (
          <p style={{ color: 'var(--muted-text)', margin: 0 }}>No pending team invitations.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Project</th>
                <th>Team</th>
                <th>Invited By</th>
                <th>Invited Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invitations.map((inv) => (
                <tr key={inv.id}>
                  <td><strong>{inv.project_name}</strong></td>
                  <td>Team {inv.team_number}: {inv.team_title}</td>
                  <td>{inv.invited_by_name}</td>
                  <td>{new Date(inv.created_at).toLocaleString()}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        type="button"
                        className="primary"
                        disabled={acceptMutation.isPending}
                        onClick={() => acceptMutation.mutate(inv.id)}
                      >
                        Accept
                      </button>
                      <button
                        type="button"
                        className="danger"
                        disabled={rejectMutation.isPending}
                        onClick={() => rejectMutation.mutate(inv.id)}
                      >
                        Reject
                      </button>
                    </div>
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
