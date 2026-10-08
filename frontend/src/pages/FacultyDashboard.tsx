import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiRequest, SchemaProjectOut } from '../api/client';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { StatusBadge } from '../components/StatusBadge';

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

  const totalProjects = projects?.length || 0;
  const activeProjects = projects?.filter((p) => p.status === 'active').length || 0;

  return (
    <div>
      <Breadcrumbs items={[{ label: 'Dashboard' }]} />
      <h1>Faculty Dashboard</h1>

      {/* Modern KPI Metrics Grid */}
      <div className="metrics-grid">
        <div className="metric-card success">
          <span className="metric-label">Active Projects</span>
          <span className="metric-value">{activeProjects}</span>
          <span style={{ fontSize: '12px', color: 'var(--muted-text)' }}>Out of {totalProjects} total</span>
        </div>

        <div className={`metric-card ${pendingProposals > 0 ? 'warning' : ''}`}>
          <span className="metric-label">Proposals Pending</span>
          <span className="metric-value" style={{ color: pendingProposals > 0 ? 'var(--warning-color)' : 'inherit' }}>
            {pendingProposals}
          </span>
          <span style={{ fontSize: '12px', color: 'var(--muted-text)' }}>Awaiting faculty review</span>
        </div>

        <div className={`metric-card ${pendingChanges > 0 ? 'warning' : ''}`}>
          <span className="metric-label">Change Requests</span>
          <span className="metric-value" style={{ color: pendingChanges > 0 ? 'var(--warning-color)' : 'inherit' }}>
            {pendingChanges}
          </span>
          <span style={{ fontSize: '12px', color: 'var(--muted-text)' }}>CCB review required</span>
        </div>

        <div className={`metric-card ${delayedTeams > 0 ? 'danger' : 'success'}`}>
          <span className="metric-label">Delayed Teams</span>
          <span className="metric-value" style={{ color: delayedTeams > 0 ? 'var(--danger-color)' : 'var(--success-color)' }}>
            {delayedTeams}
          </span>
          <span style={{ fontSize: '12px', color: 'var(--muted-text)' }}>
            {delayedTeams > 0 ? 'Exceeded milestone due dates' : 'All teams on track'}
          </span>
        </div>
      </div>

      {/* Needs Attention List */}
      <div className="panel">
        <div className="panel-header">
          <h2>Needs Attention</h2>
        </div>

        {pendingProposals === 0 && pendingChanges === 0 && upcomingReviews === 0 && delayedTeams === 0 ? (
          <p style={{ color: 'var(--success-color)', fontWeight: 500, margin: 0 }}>
            Everything is up to date. No pending tasks requiring immediate action.
          </p>
        ) : (
          <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {pendingProposals > 0 && (
              <li>
                <Link to="/projects">
                  <strong>{pendingProposals} proposal revision{pendingProposals > 1 ? 's' : ''}</strong> waiting for your review and approval
                </Link>
              </li>
            )}
            {pendingChanges > 0 && (
              <li>
                <Link to="/projects">
                  <strong>{pendingChanges} change request{pendingChanges > 1 ? 's' : ''}</strong> awaiting Change Control Board decision
                </Link>
              </li>
            )}
            {upcomingReviews > 0 && (
              <li>
                <Link to="/projects">
                  <strong>{upcomingReviews} scheduled review{upcomingReviews > 1 ? 's' : ''}</strong> coming up
                </Link>
              </li>
            )}
            {delayedTeams > 0 && (
              <li style={{ color: 'var(--danger-color)' }}>
                <Link to="/projects" style={{ color: 'var(--danger-color)', fontWeight: 600 }}>
                  {delayedTeams} team{delayedTeams > 1 ? 's' : ''} flagged as delayed against deadlines
                </Link>
              </li>
            )}
          </ul>
        )}
      </div>

      {/* Projects Summary Table */}
      <div className="panel">
        <div className="panel-header">
          <h2>Course Projects</h2>
          <Link to="/projects/new" className="btn btn-primary">
            + Create Project
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
                    <Link to={`/projects/${proj.id}`} style={{ fontWeight: 600 }}>
                      {proj.name}
                    </Link>
                  </td>
                  <td>{proj.semester} {proj.academic_year}</td>
                  <td>
                    <span style={{ textTransform: 'capitalize' }}>{proj.team_formation_mode}</span>
                  </td>
                  <td><strong>{proj.total_marks}</strong> pts</td>
                  <td>
                    <StatusBadge status={proj.status} />
                  </td>
                  <td>
                    <Link to={`/projects/${proj.id}`} className="btn">
                      View Project
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
