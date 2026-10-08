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

  return (
    <div>
      <Breadcrumbs items={[{ label: 'Dashboard' }]} />
      <h1>Student Dashboard</h1>

      {/* Pending Invitations Alert if any */}
      {invitations && invitations.length > 0 && (
        <div className="banner banner-warning">
          You have {invitations.length} pending team invitation{invitations.length > 1 ? 's' : ''}.{' '}
          <Link to="/invitations">Review invitations</Link>
        </div>
      )}

      {/* Upcoming Deadlines */}
      <div className="panel">
        <h2>Upcoming Deadlines</h2>
        {allDeadlines.length === 0 ? (
          <p style={{ color: 'var(--muted-text)', margin: 0 }}>No upcoming deadlines scheduled.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Project</th>
                <th>Deadline Title</th>
                <th>Due Date</th>
                <th>Time Remaining</th>
              </tr>
            </thead>
            <tbody>
              {allDeadlines.map((dl, idx) => (
                <tr key={idx}>
                  <td>
                    <Link to={`/projects/${dl.projectId}`}>{dl.projectName}</Link>
                  </td>
                  <td>{dl.title}</td>
                  <td>{new Date(dl.dueAt).toLocaleString()}</td>
                  <td>
                    {dl.daysRemaining === 0 ? (
                      <span style={{ color: 'var(--danger-color)', fontWeight: 'bold' }}>Due today</span>
                    ) : (
                      <span>{dl.daysRemaining} day{dl.daysRemaining > 1 ? 's' : ''} remaining</span>
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
        <h2>My Enrolled Projects</h2>
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
                    <Link to={`/projects/${proj.id}`}>{proj.name}</Link>
                  </td>
                  <td>
                    {proj.user_team_id ? (
                      <Link to={`/teams/${proj.user_team_id}`}>
                        Team {proj.user_team_number}
                      </Link>
                    ) : (
                      <span style={{ color: 'var(--muted-text)' }}>Not formed yet</span>
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
                    <Link to={`/projects/${proj.id}`}>Open Workspace</Link>
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
