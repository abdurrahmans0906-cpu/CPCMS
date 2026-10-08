import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiRequest, SchemaProjectOut } from '../api/client';
import { useAuth } from '../lib/AuthContext';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { StatusBadge } from '../components/StatusBadge';

export const ProjectsListPage: React.FC = () => {
  const { role } = useAuth();
  const { data: projects, isLoading } = useQuery<SchemaProjectOut[]>({
    queryKey: ['projects'],
    queryFn: () => apiRequest('/projects'),
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <Breadcrumbs items={[{ label: 'Dashboard', to: '/' }, { label: 'Projects' }]} />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h1>{role === 'FACULTY' ? 'Course Projects' : 'My Enrolled Projects'}</h1>
        {role === 'FACULTY' && (
          <Link to="/projects/new" className="btn btn-primary" style={{ textDecoration: 'none' }}>
            Create Project
          </Link>
        )}
      </div>

      <div className="panel">
        {!projects || projects.length === 0 ? (
          <p style={{ color: 'var(--muted-text)', margin: 0 }}>No projects found.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Course</th>
                <th>Project Name</th>
                <th>Semester</th>
                <th>Mode</th>
                <th>Team Limits</th>
                {role === 'STUDENT' && <th>My Team</th>}
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((p) => (
                <tr key={p.id}>
                  <td><strong>{p.course_code}</strong></td>
                  <td>
                    <Link to={`/projects/${p.id}`}>{p.name}</Link>
                  </td>
                  <td>{p.semester} {p.academic_year}</td>
                  <td>{p.team_formation_mode}</td>
                  <td>{p.min_team_size} - {p.max_team_size} members</td>
                  {role === 'STUDENT' && (
                    <td>
                      {p.user_team_id ? (
                        <Link to={`/teams/${p.user_team_id}`}>
                          Team {p.user_team_number}
                        </Link>
                      ) : (
                        <span style={{ color: 'var(--muted-text)' }}>Not formed</span>
                      )}
                    </td>
                  )}
                  <td>
                    <StatusBadge status={p.status} />
                  </td>
                  <td>
                    <Link to={`/projects/${p.id}`}>Open</Link>
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
