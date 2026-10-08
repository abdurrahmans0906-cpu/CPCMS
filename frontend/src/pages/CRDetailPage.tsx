import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  apiRequest,
  SchemaChangeRequestOut,
  SchemaCRImpactOut,
} from '../api/client';
import { useAuth } from '../lib/AuthContext';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { StatusBadge } from '../components/StatusBadge';

export const CRDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user, role } = useAuth();
  const queryClient = useQueryClient();

  const [transitionComment, setTransitionComment] = useState('');
  const [implementedSha, setImplementedSha] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editReason, setEditReason] = useState('');
  const [editPriority, setEditPriority] = useState('medium');
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const { data: cr, isLoading, error } = useQuery<SchemaChangeRequestOut>({
    queryKey: ['change-request', id],
    queryFn: () => apiRequest<SchemaChangeRequestOut>(`/change-requests/${id}`),
    enabled: !!id,
  });

  const { data: impact } = useQuery<SchemaCRImpactOut>({
    queryKey: ['cr-impact', id],
    queryFn: () => apiRequest<SchemaCRImpactOut>(`/change-requests/${id}/impact`),
    enabled: !!id,
  });

  const transitionMutation = useMutation({
    mutationFn: (payload: { to_status: string; comment?: string; implemented_commit_sha?: string }) =>
      apiRequest<SchemaChangeRequestOut>(`/change-requests/${id}/transition`, {
        method: 'POST',
        body: payload,
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['change-request', id] });
      queryClient.invalidateQueries({ queryKey: ['cr-impact', id] });
      setFeedbackMsg({ type: 'success', text: `Status changed to ${data.status.toUpperCase()}.` });
      setTransitionComment('');
      setImplementedSha('');
    },
    onError: (err: any) => {
      setFeedbackMsg({ type: 'error', text: err.message || 'Transition failed.' });
    },
  });

  const updateMutation = useMutation({
    mutationFn: (payload: { title?: string; description?: string; reason?: string; priority?: string }) =>
      apiRequest<SchemaChangeRequestOut>(`/change-requests/${id}`, {
        method: 'PATCH',
        body: payload,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['change-request', id] });
      setIsEditing(false);
      setFeedbackMsg({ type: 'success', text: 'Change request updated.' });
    },
    onError: (err: any) => {
      setFeedbackMsg({ type: 'error', text: err.message || 'Update failed.' });
    },
  });

  if (isLoading) return <div>Loading...</div>;
  if (error || !cr) {
    return <div className="banner banner-error">Change Request not found or error loading details.</div>;
  }

  const isFaculty = role === 'FACULTY';
  const isAuthorOrTeam = role === 'STUDENT' || isFaculty;

  const handleStartEdit = () => {
    setEditTitle(cr.title);
    setEditDescription(cr.description);
    setEditReason(cr.reason);
    setEditPriority(cr.priority);
    setIsEditing(true);
  };

  const handleSaveEdit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate({
      title: editTitle,
      description: editDescription,
      reason: editReason,
      priority: editPriority,
    });
  };

  const handleTransition = (toStatus: string) => {
    if (toStatus === 'rejected' && !transitionComment.trim()) {
      alert('A comment is required when rejecting a change request.');
      return;
    }
    if (
      toStatus === 'implemented' &&
      !implementedSha.trim() &&
      !cr.implemented_commit_sha &&
      !cr.implemented_version_id
    ) {
      alert('Please enter the Git commit SHA or version reference before marking implemented.');
      return;
    }
    transitionMutation.mutate({
      to_status: toStatus,
      comment: transitionComment.trim() || undefined,
      implemented_commit_sha: implementedSha.trim() || undefined,
    });
  };

  return (
    <div>
      <Breadcrumbs
        items={[
          { label: 'Dashboard', to: '/' },
          { label: 'Team Space', to: `/teams/${cr.team_id}` },
          { label: `Change Request ${cr.cr_code}` },
        ]}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
        <div>
          <h1 style={{ margin: '0 0 8px 0' }}>
            {cr.cr_code}: {cr.title}
          </h1>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <StatusBadge status={cr.status} />
            <span style={{ fontSize: '12px', border: '1px solid #c9c9c2', padding: '1px 6px', fontWeight: 600 }}>
              PRIORITY: {cr.priority.toUpperCase()}
            </span>
            <span className="muted" style={{ fontSize: '13px' }}>
              Created by {cr.created_by_name || 'Team member'} on {new Date(cr.created_at).toLocaleString()}
            </span>
          </div>
        </div>

        <div>
          {['draft', 'submitted'].includes(cr.status) && !isEditing && (
            <button onClick={handleStartEdit}>Edit Details</button>
          )}
        </div>
      </div>

      {feedbackMsg && (
        <div
          className={feedbackMsg.type === 'success' ? 'banner banner-success' : 'banner banner-error'}
          style={{ marginBottom: '16px' }}
        >
          {feedbackMsg.text}
        </div>
      )}

      {isEditing ? (
        <form onSubmit={handleSaveEdit} className="panel" style={{ marginBottom: '20px' }}>
          <h2>Edit Change Request</h2>
          <div className="form-group">
            <label htmlFor="cr-title">Title</label>
            <input
              id="cr-title"
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="cr-priority">Priority</label>
            <select
              id="cr-priority"
              value={editPriority}
              onChange={(e) => setEditPriority(e.target.value)}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="cr-desc">Description</label>
            <textarea
              id="cr-desc"
              rows={4}
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="cr-reason">Reason / Justification</label>
            <textarea
              id="cr-reason"
              rows={3}
              value={editReason}
              onChange={(e) => setEditReason(e.target.value)}
              required
            />
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button type="submit" className="primary" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
            </button>
            <button type="button" onClick={() => setIsEditing(false)}>
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '16px', marginBottom: '24px' }}>
          <div className="panel">
            <h2>Description & Justification</h2>
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--color-text-muted)' }}>Description</div>
              <p style={{ whiteSpace: 'pre-wrap', margin: '4px 0' }}>{cr.description}</p>
            </div>
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--color-text-muted)' }}>Reason / Justification</div>
              <p style={{ whiteSpace: 'pre-wrap', margin: '4px 0' }}>{cr.reason}</p>
            </div>
            {cr.components && cr.components.length > 0 && (
              <div>
                <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--color-text-muted)' }}>Impacted Components</div>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '4px' }}>
                  {cr.components.map((c: string) => (
                    <span key={c} style={{ border: '1px solid var(--color-border)', padding: '2px 6px', fontSize: '12px' }}>
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {cr.implemented_commit_sha && (
              <div style={{ marginTop: '16px' }}>
                <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--color-text-muted)' }}>Implemented Commit SHA</div>
                <code>{cr.implemented_commit_sha}</code>
              </div>
            )}
          </div>

          <div className="panel">
            <h2>Workflow Actions</h2>
            <p className="muted" style={{ fontSize: '13px', margin: '0 0 12px 0' }}>
              Current Status: <strong>{cr.status.toUpperCase()}</strong>
            </p>

            <div className="form-group">
              <label htmlFor="cr-trans-comment">Reviewer / Transition Comment</label>
              <textarea
                id="cr-trans-comment"
                rows={2}
                placeholder="Add feedback or justification..."
                value={transitionComment}
                onChange={(e) => setTransitionComment(e.target.value)}
              />
            </div>

            {cr.status === 'approved' && (
              <div className="form-group">
                <label htmlFor="cr-impl-sha">Commit SHA / Version Ref</label>
                <input
                  id="cr-impl-sha"
                  type="text"
                  placeholder="e.g. 7f3a8b9"
                  value={implementedSha}
                  onChange={(e) => setImplementedSha(e.target.value)}
                />
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {/* Draft -> Submitted */}
              {cr.status === 'draft' && isAuthorOrTeam && (
                <button
                  type="button"
                  className="primary"
                  onClick={() => handleTransition('submitted')}
                  disabled={transitionMutation.isPending}
                >
                  Submit for Faculty Review
                </button>
              )}

              {/* Submitted -> Under Review */}
              {cr.status === 'submitted' && isFaculty && (
                <button
                  type="button"
                  className="primary"
                  onClick={() => handleTransition('under_review')}
                  disabled={transitionMutation.isPending}
                >
                  Mark Under Review
                </button>
              )}

              {/* Under Review -> Approved / Rejected */}
              {cr.status === 'under_review' && isFaculty && (
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    className="primary"
                    style={{ flex: 1 }}
                    onClick={() => handleTransition('approved')}
                    disabled={transitionMutation.isPending}
                  >
                    Approve CR
                  </button>
                  <button
                    type="button"
                    className="danger"
                    style={{ flex: 1 }}
                    onClick={() => handleTransition('rejected')}
                    disabled={transitionMutation.isPending}
                  >
                    Reject CR
                  </button>
                </div>
              )}

              {/* Approved -> Implemented */}
              {cr.status === 'approved' && (
                <button
                  type="button"
                  className="primary"
                  onClick={() => handleTransition('implemented')}
                  disabled={transitionMutation.isPending}
                >
                  Mark as Implemented
                </button>
              )}

              {/* Implemented -> Verified */}
              {cr.status === 'implemented' && isFaculty && (
                <button
                  type="button"
                  className="primary"
                  onClick={() => handleTransition('verified')}
                  disabled={transitionMutation.isPending}
                >
                  Verify Implementation
                </button>
              )}

              {/* Verified -> Closed */}
              {cr.status === 'verified' && isFaculty && (
                <button
                  type="button"
                  className="primary"
                  onClick={() => handleTransition('closed')}
                  disabled={transitionMutation.isPending}
                >
                  Close Change Request
                </button>
              )}

              {cr.status === 'closed' && (
                <div className="banner banner-success" style={{ margin: 0, padding: '6px 8px', fontSize: '13px' }}>
                  This change request is closed.
                </div>
              )}
              {cr.status === 'rejected' && (
                <div className="banner banner-error" style={{ margin: 0, padding: '6px 8px', fontSize: '13px' }}>
                  This change request was rejected.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Impact Analysis */}
      <div className="panel" style={{ marginBottom: '24px' }}>
        <h2>SCM Impact Analysis</h2>
        {impact ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <h3>Directly Affected CIs ({impact.directly_affected_cis?.length || 0})</h3>
              {!impact.directly_affected_cis || impact.directly_affected_cis.length === 0 ? (
                <p className="muted">No direct CIs specified.</p>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Code</th>
                      <th>Name</th>
                      <th>Locked?</th>
                    </tr>
                  </thead>
                  <tbody>
                    {impact.directly_affected_cis.map((ci: any) => (
                      <tr key={ci.id}>
                        <td>
                          <strong>{ci.ci_code}</strong>
                        </td>
                        <td>{ci.name}</td>
                        <td>
                          {ci.is_locked ? (
                            <span style={{ color: 'var(--color-danger)', fontWeight: 600 }}>LOCKED</span>
                          ) : (
                            'No'
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              <h3 style={{ marginTop: '16px' }}>
                Indirectly Affected CIs (via dependency graph) ({impact.indirectly_affected_cis?.length || 0})
              </h3>
              {!impact.indirectly_affected_cis || impact.indirectly_affected_cis.length === 0 ? (
                <p className="muted">No downstream CIs affected.</p>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Code</th>
                      <th>Name</th>
                      <th>Locked?</th>
                    </tr>
                  </thead>
                  <tbody>
                    {impact.indirectly_affected_cis.map((ci: any) => (
                      <tr key={ci.id}>
                        <td>
                          <strong>{ci.ci_code}</strong>
                        </td>
                        <td>{ci.name}</td>
                        <td>
                          {ci.is_locked ? (
                            <span style={{ color: 'var(--color-danger)', fontWeight: 600 }}>LOCKED</span>
                          ) : (
                            'No'
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div>
              <h3>Locked Configuration Items ({impact.locked_cis?.length || 0})</h3>
              {!impact.locked_cis || impact.locked_cis.length === 0 ? (
                <p className="muted">None of the affected CIs are currently locked in baselines.</p>
              ) : (
                <div
                  style={{
                    border: '1px solid var(--color-border)',
                    padding: '8px',
                    background: '#fff9f0',
                    marginBottom: '16px',
                  }}
                >
                  <p style={{ margin: '0 0 6px 0', fontSize: '13px', color: 'var(--color-warning)', fontWeight: 600 }}>
                    Notice: The following CIs are locked under active baselines. Direct edits are prohibited without
                    approved CR:
                  </p>
                  <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px' }}>
                    {impact.locked_cis.map((ci: any) => (
                      <li key={ci.id}>
                        <strong>{ci.ci_code}</strong> - {ci.name}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <h3>Affected Baselines ({impact.affected_baselines?.length || 0})</h3>
              {!impact.affected_baselines || impact.affected_baselines.length === 0 ? (
                <p className="muted">No baselines contain versions of the affected CIs.</p>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Baseline Code</th>
                      <th>Name</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {impact.affected_baselines.map((b: any) => (
                      <tr key={b.id}>
                        <td>
                          <strong>{b.code}</strong>
                        </td>
                        <td>{b.name}</td>
                        <td>
                          <StatusBadge status={b.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        ) : (
          <div>Loading impact analysis...</div>
        )}
      </div>

      {/* Transition History Table */}
      <div className="panel">
        <h2>Lifecycle Transition History</h2>
        {!cr.transitions || cr.transitions.length === 0 ? (
          <p className="muted">No transitions recorded.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>From</th>
                <th>To</th>
                <th>Actor</th>
                <th>Comment</th>
                <th>Date & Time</th>
              </tr>
            </thead>
            <tbody>
              {cr.transitions.map((t: any) => (
                <tr key={t.id}>
                  <td>
                    <StatusBadge status={t.from_status} />
                  </td>
                  <td>
                    <StatusBadge status={t.to_status} />
                  </td>
                  <td>{t.actor_name || 'System'}</td>
                  <td>{t.comment || '-'}</td>
                  <td>{new Date(t.at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default CRDetailPage;
