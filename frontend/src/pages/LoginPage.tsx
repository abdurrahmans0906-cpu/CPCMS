import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiRequest } from '../api/client';
import { useAuth } from '../lib/AuthContext';

export const LoginPage: React.FC = () => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await apiRequest<{ access_token: string; user: any }>('/auth/login', {
        method: 'POST',
        body: { identifier: identifier.trim(), password },
      });
      login(data.access_token, data.user);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '60px auto', padding: '0 16px' }}>
      <h1 style={{ textAlign: 'left', marginBottom: '4px' }}>CPCMS</h1>
      <p style={{ color: 'var(--muted-text)', fontSize: '13px', marginBottom: '20px' }}>
        Course Project Configuration and Management System
      </p>

      {error && <div className="banner banner-error">{error}</div>}

      <div className="panel">
        <form onSubmit={handleSubmit} style={{ width: '100%' }}>
          <div className="form-group">
            <label htmlFor="identifier">Identifier</label>
            <input
              id="identifier"
              type="text"
              required
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="Register Number, Faculty ID, or Email"
            />
            <div className="form-help">
              Students: use register number (e.g. 23MIS0475). Faculty: use faculty code or email.
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div style={{ marginTop: '16px' }}>
            <button type="submit" className="primary" disabled={loading} style={{ width: '100%' }}>
              {loading ? 'Loading...' : 'Sign In'}
            </button>
          </div>
        </form>
      </div>

      <div style={{ marginTop: '16px', fontSize: '13px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <div>
          New student? <Link to="/register/student">Register student account</Link>
        </div>
        <div>
          Faculty registration: <Link to="/register/faculty">Register faculty account</Link>
        </div>
      </div>
    </div>
  );
};
