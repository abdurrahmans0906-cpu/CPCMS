import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiRequest, SchemaProjectOut } from '../api/client';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { StatusBadge } from '../components/StatusBadge';

export const StudentDashboard: React.FC = () => {
  const { data: projects, isLoading } = useQuery<SchemaProjectOut[]>({
    queryKey: ['projects'],
    queryFn: () => apiRequest('/projects'),
  });

  const { data: invitations } = useQuery<any[]>({
    queryKey: ['invitations'],
    queryFn: () => apiRequest('/invitations'),
  });

  if (isLoading) {
    return <div>Loading...</div>;
  }

  // Calculate upcoming deadlines across enrolled projects
  const allDeadlines: { projectId: string; projectName: string; title: string; dueAt: string; daysRemaining: number }[] = [];
  const now = new Date();

  projects?.forEach((p) => {
    p.deadlines?.forEach((d: any) => {
      const dueDate = new Date(d.due_at);
      const diffTime = dueDate.getTime() - now.getTime();
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      if (diffDays >= 0) {
        allDeadlines.push({
          projectId: p.id,
          projectName: p.name,
          title: d.title,
          dueAt: d.due_at,
          daysRemaining: diffDays,
        });
      }
    });
  });

  allDeadlines.sort((a, b) => a.daysRemaining - b.daysRemaining);

  const totalProjects = projects?.length || 0;
  const assignedTeams = projects?.filter((p) => !!p.user_team_id).length || 0;
  const pendingInvs = invitations?.length || 0;

  return (
    <div>
      <Breadcrumbs items={[{ label: 'Dashboard' }]} />
      <h1>Student Dashboard</h1>

      {/* KPI Metric Cards */}
      <div className="metrics-grid">
        <div className="metric-card success">
          <span className="metric-label">Enrolled Projects</span>
          <span className="metric-value">{totalProjects}</span>
          <span style={{ fontSize: '12px', color: 'var(--muted-text)' }}>Active semester coursework</span>
        </div>

        <div className={`metric-card ${assignedTeams > 0 ? 'success' : 'warning'}`}>
          <span className="metric-label">Team Memberships</span>
          <span className="metric-value">{assignedTeams}</span>
          <span style={{ fontSize: '12px', color: 'var(--muted-text)' }}>
            {assignedTeams === totalProjects ? 'All teams joined' : `${totalProjects - assignedTeams} unassigned`}
          </span>
        </div>

        <div className={`metric-card ${pendingInvs > 0 ? 'warning' : ''}`}>
          <span className="metric-label">Pending Invitations</span>
          <span className="metric-value" style={{ color: pendingInvs > 0 ? 'var(--warning-color)' : 'inherit' }}>
            {pendingInvs}
          </span>
          <span style={{ fontSize: '12px', color: 'var(--muted-text)' }}>
            {pendingInvs > 0 ? <Link to="/invitations">Review invitations</Link> : 'No action needed'}
          </span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Upcoming Deadlines</span>
          <span className="metric-value">{allDeadlines.length}</span>
          <span style={{ fontSize: '12px', color: 'var(--muted-text)' }}>
            {allDeadlines.length > 0 ? `Next in ${allDeadlines[0].daysRemaining}d` : 'None scheduled'}
          </span>
        </div>
      </div>

      {/* Pending Invitations Alert if any */}
      {invitations && invitations.length > 0 && (
        <div className="banner banner-warning">
          <span>You have <strong>{invitations.length} pending team invitation{invitations.length > 1 ? 's' : ''}</strong> waiting for your response.</span>
          <Link to="/invitations" className="btn btn-primary" style={{ marginLeft: 'auto' }}>
            View Invitations
          </Link>
        </div>
      )}

      {/* Upcoming Deadlines */}
      <div className="panel">
        <div className="panel-header">
          <h2>Upcoming Deadlines</h2>
        </div>
        {allDeadlines.length === 0 ? (
          <p style={{ color: 'var(--muted-text)', margin: 0 }}>No upcoming deadlines scheduled.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Project</th>
                <th>Deadline Title</th>
                <th>Due Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {allDeadlines.map((dl, idx) => (
                <tr key={idx}>
                  <td>
                    <Link to={`/projects/${dl.projectId}`} style={{ fontWeight: 600 }}>
                      {dl.projectName}
                    </Link>
                  </td>
                  <td>{dl.title}</td>
                  <td>{new Date(dl.dueAt).toLocaleString()}</td>
                  <td>
                    {dl.daysRemaining <= 1 ? (
                      <span className="status-badge delayed">
                        <span className="status-dot" />
                        {dl.daysRemaining === 0 ? 'DUE TODAY' : 'DUE TOMORROW'}
                      </span>
                    ) : (
                      <span className="status-badge in_progress">
                        <span className="status-dot" />
                        {dl.daysRemaining} DAYS REMAINING
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Enrolled Projects */}
      <div className="panel">
        <div className="panel-header">
          <h2>My Enrolled Projects</h2>
        </div>
        {!projects || projects.length === 0 ? (
          <p style={{ color: 'var(--muted-text)', margin: 0 }}>You are not enrolled in any course projects yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Course</th>
                <th>Project Name</th>
                <th>My Team</th>
                <th>Lifecycle Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((proj) => (
                <tr key={proj.id}>
                  <td><strong>{proj.course_code}</strong></td>
                  <td>
                    <Link to={`/projects/${proj.id}`} style={{ fontWeight: 600 }}>
                      {proj.name}
                    </Link>
                  </td>
                  <td>
                    {proj.user_team_id ? (
                      <Link to={`/teams/${proj.user_team_id}`} style={{ fontWeight: 600 }}>
                        Team {proj.user_team_number}
                      </Link>
                    ) : (
                      <span style={{ color: 'var(--warning-color)', fontWeight: 500 }}>Not formed yet</span>
                    )}
                  </td>
                  <td>
                    {proj.user_team_status ? (
                      <StatusBadge status={proj.user_team_status} />
                    ) : (
                      <span style={{ color: 'var(--muted-text)' }}>-</span>
                    )}
                  </td>
                  <td>
                    <Link to={`/projects/${proj.id}`} className="btn">
                      Open Workspace
                    </Link>
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
