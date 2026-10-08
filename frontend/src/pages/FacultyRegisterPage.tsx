import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiRequest } from '../api/client';

export const FacultyRegisterPage: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    faculty_code: '',
    department: 'Computer Science and Engineering',
    password: '',
    invite_code: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      await apiRequest('/auth/register/faculty', {
        method: 'POST',
        body: formData,
      });
      setSuccess('Faculty account registered successfully. You may now sign in.');
      setTimeout(() => navigate('/login'), 1500);
    } catch (err: any) {
      setError(err.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '480px', margin: '40px auto', padding: '0 16px' }}>
      <h1>Faculty Registration</h1>
      <p style={{ color: 'var(--muted-text)', fontSize: '13px', marginBottom: '16px' }}>
        Create an instructor account with your faculty invite code.
      </p>

      {error && <div className="banner banner-error">{error}</div>}
      {success && <div className="banner banner-success">{success}</div>}

      <div className="panel">
        <form onSubmit={handleSubmit} style={{ width: '100%' }}>
          <div className="form-group">
            <label htmlFor="name">Full Name</label>
            <input
              id="name"
              name="name"
              type="text"
              required
              value={formData.name}
              onChange={handleChange}
              placeholder="e.g. Dr. K. Meenakshi"
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Official Email</label>
            <input
              id="email"
              name="email"
              type="email"
              required
              value={formData.email}
              onChange={handleChange}
              placeholder="e.g. meenakshi.k@univ.edu"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="faculty_code">Faculty Code / ID</label>
              <input
                id="faculty_code"
                name="faculty_code"
                type="text"
                required
                value={formData.faculty_code}
                onChange={handleChange}
                placeholder="e.g. FAC1042"
              />
            </div>

            <div className="form-group">
              <label htmlFor="department">Department</label>
              <input
                id="department"
                name="department"
                type="text"
                required
                value={formData.department}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="invite_code">Faculty Invite Code</label>
            <input
              id="invite_code"
              name="invite_code"
              type="password"
              required
              value={formData.invite_code}
              onChange={handleChange}
              placeholder="Enter institutional invite code"
            />
            <div className="form-help">Default demo invite code: FACULTY2026</div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              required
              minLength={8}
              value={formData.password}
              onChange={handleChange}
            />
            <div className="form-help">Minimum 8 characters.</div>
          </div>

          <div style={{ marginTop: '16px' }}>
            <button type="submit" className="primary" disabled={loading} style={{ width: '100%' }}>
              {loading ? 'Loading...' : 'Register Faculty'}
            </button>
          </div>
        </form>
      </div>

      <p style={{ marginTop: '16px', fontSize: '13px' }}>
        Already registered? <Link to="/login">Sign in here</Link>
      </p>
    </div>
  );
};
