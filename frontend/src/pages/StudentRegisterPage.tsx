import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiRequest } from '../api/client';

export const StudentRegisterPage: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    register_number: '',
    department: 'Computer Science and Engineering',
    password: '',
    confirm_password: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (formData.password !== formData.confirm_password) {
      setError('Password and confirmation password do not match.');
      return;
    }

    setLoading(true);
    try {
      await apiRequest('/auth/register/student', {
        method: 'POST',
        body: formData,
      });
      setSuccess('Registration successful. You may now sign in.');
      setTimeout(() => navigate('/login'), 1500);
    } catch (err: any) {
      setError(err.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '480px', margin: '40px auto', padding: '0 16px' }}>
      <h1>Student Registration</h1>
      <p style={{ color: 'var(--muted-text)', fontSize: '13px', marginBottom: '16px' }}>
        Create your student account to access enrolled course projects.
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
              placeholder="e.g. Rahul Sharma"
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">College Email</label>
            <input
              id="email"
              name="email"
              type="email"
              required
              value={formData.email}
              onChange={handleChange}
              placeholder="e.g. rahul.sharma@univ.edu"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="register_number">Register Number</label>
              <input
                id="register_number"
                name="register_number"
                type="text"
                required
                value={formData.register_number}
                onChange={handleChange}
                placeholder="e.g. 23MIS0475"
              />
              <div className="form-help">Format: 2 digits, 3 letters, 4 digits.</div>
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

          <div className="form-row">
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

            <div className="form-group">
              <label htmlFor="confirm_password">Confirm Password</label>
              <input
                id="confirm_password"
                name="confirm_password"
                type="password"
                required
                minLength={8}
                value={formData.confirm_password}
                onChange={handleChange}
              />
            </div>
          </div>

          <div style={{ marginTop: '16px' }}>
            <button type="submit" className="primary" disabled={loading} style={{ width: '100%' }}>
              {loading ? 'Loading...' : 'Register'}
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
