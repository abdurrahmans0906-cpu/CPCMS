import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiRequest, SchemaCourseOut } from '../api/client';
import { useAuth } from '../lib/AuthContext';
import { Breadcrumbs } from '../components/Breadcrumbs';

export const CoursesPage: React.FC = () => {
  const { role } = useAuth();
  const queryClient = useQueryClient();

  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [department, setDepartment] = useState('Computer Science and Engineering');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const { data: courses, isLoading } = useQuery<SchemaCourseOut[]>({
    queryKey: ['courses'],
    queryFn: () => apiRequest('/courses'),
  });

  const createMutation = useMutation({
    mutationFn: (newCourse: { code: string; name: string; department: string }) =>
      apiRequest('/courses', { method: 'POST', body: newCourse }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courses'] });
      setCode('');
      setName('');
      setSuccess('Course created successfully.');
      setError(null);
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to create course.');
      setSuccess(null);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim() || !name.trim()) return;
    createMutation.mutate({ code: code.trim(), name: name.trim(), department: department.trim() });
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <Breadcrumbs items={[{ label: 'Dashboard', to: '/' }, { label: 'Courses' }]} />
      <h1>Courses</h1>

      {error && <div className="banner banner-error">{error}</div>}
      {success && <div className="banner banner-success">{success}</div>}

      {role === 'FACULTY' && (
        <div className="panel" style={{ maxWidth: '560px', marginBottom: '20px' }}>
          <h2>Add New Course</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group" style={{ flex: '1' }}>
                <label htmlFor="course-code">Course Code</label>
                <input
                  id="course-code"
                  type="text"
                  required
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="e.g. CSE3001"
                />
              </div>

              <div className="form-group" style={{ flex: '2' }}>
                <label htmlFor="course-dept">Department</label>
                <input
                  id="course-dept"
                  type="text"
                  required
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="course-name">Course Name</label>
              <input
                id="course-name"
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Software Engineering"
              />
            </div>

            <button type="submit" className="primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Loading...' : 'Create Course'}
            </button>
          </form>
        </div>
      )}

      <div className="panel">
        <h2>Registered Courses</h2>
        {!courses || courses.length === 0 ? (
          <p style={{ color: 'var(--muted-text)', margin: 0 }}>No courses found.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Course Name</th>
                <th>Department</th>
                <th>Created Date</th>
              </tr>
            </thead>
            <tbody>
              {courses.map((c) => (
                <tr key={c.id}>
                  <td><strong>{c.code}</strong></td>
                  <td>{c.name}</td>
                  <td>{c.department}</td>
                  <td>{new Date(c.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
