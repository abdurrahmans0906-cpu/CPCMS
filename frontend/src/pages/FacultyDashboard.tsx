import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiRequest, SchemaProjectOut } from '../api/client';
import { Breadcrumbs } from '../components/Breadcrumbs';

export const FacultyDashboard: React.FC = () => {
  const { data: projects, isLoading: projectsLoading } = useQuery<SchemaProjectOut[]>({
    queryKey: ['projects'],
    queryFn: () => apiRequest('/projects'),
  });

  // Aggregate project statistics and attention items
  const { data: summaries, isLoading: summariesLoading } = useQuery<any[]>({
    queryKey: ['projects-summaries', projects?.map((p) => p.id)],
    queryFn: async () => {
      if (!projects || projects.length === 0) return [];
      const res = await Promise.all(
        projects.map((p) => apiRequest(`/projects/${p.id}/analytics`).catch(() => null))
      );
      return res.filter(Boolean);
    },
    enabled: !!projects && projects.length > 0,
  });

  if (projectsLoading || summariesLoading) {
    return <div>Loading...</div>;
  }

  // Calculate attention counts
  let pendingProposals = 0;
  let pendingChanges = 0;
  let upcomingReviews = 0;
  let delayedTeams = 0;

  summaries?.forEach((s) => {
    pendingProposals += s.pending_proposals || 0;
    pendingChanges += s.pending_changes || 0;
    upcomingReviews += s.upcoming_reviews || 0;
    delayedTeams += s.delayed_teams?.length || 0;
  });

  return (
    <div>
      <Breadcrumbs items={[{ label: 'Dashboard' }]} />
      <h1>Faculty Dashboard</h1>

      {/* Needs Attention List */}
      <div className="panel">
        <h2>Needs attention</h2>
        {pendingProposals === 0 && pendingChanges === 0 && upcomingReviews === 0 && delayedTeams === 0 ? (
          <p style={{ color: 'var(--muted-text)', margin: 0 }}>No pending tasks requiring immediate action.</p>
        ) : (
          <ul style={{ paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {pendingProposals > 0 && (
              <li>
                <Link to="/projects">
                  {pendingProposals} proposal revision{pendingProposals > 1 ? 's' : ''} waiting for review
                </Link>
              </li>
            )}
            {pendingChanges > 0 && (
              <li>
                <Link to="/projects">
                  {pendingChanges} change request{pendingChanges > 1 ? 's' : ''} awaiting review
                </Link>
              </li>
            )}
            {upcomingReviews > 0 && (
              <li>
                <Link to="/projects">
                  {upcomingReviews} scheduled review{upcomingReviews > 1 ? 's' : ''} upcoming
                </Link>
              </li>
            )}
            {delayedTeams > 0 && (
              <li style={{ color: 'var(--danger-color)' }}>
                <Link to="/projects" style={{ color: 'var(--danger-color)' }}>
                  {delayedTeams} team{delayedTeams > 1 ? 's' : ''} flagged as delayed on deadlines
                </Link>
              </li>
            )}
          </ul>
        )}
      </div>

      {/* Projects Summary Table */}
      <div className="panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>Course Projects</h2>
          <Link to="/projects/new" className="btn btn-primary" style={{ textDecoration: 'none' }}>
            Create Project
          </Link>
        </div>

        {!projects || projects.length === 0 ? (
          <p style={{ color: 'var(--muted-text)', margin: '8px 0' }}>No active projects created yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Course</th>
                <th>Project Name</th>
                <th>Semester</th>
                <th>Formation Mode</th>
                <th>Total Marks</th>
                <th>Status</th>
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
                  <td>{proj.semester} {proj.academic_year}</td>
                  <td>{proj.team_formation_mode}</td>
                  <td>{proj.total_marks}</td>
                  <td>
                    <span className={`status-badge ${proj.status}`}>{proj.status.toUpperCase()}</span>
                  </td>
                  <td>
                    <Link to={`/projects/${proj.id}`}>View Project</Link>
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
