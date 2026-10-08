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

  const handleQuickFill = (id: string, pass: string) => {
    setIdentifier(id);
    setPassword(pass);
  };

  return (
    <div style={{ maxWidth: '440px', margin: '60px auto', padding: '0 16px' }}>
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '48px',
          height: '48px',
          background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
          color: '#ffffff',
          fontSize: '20px',
          fontWeight: 800,
          borderRadius: '12px',
          marginBottom: '12px',
          boxShadow: '0 4px 10px rgba(37, 99, 235, 0.3)'
        }}>
          CP
        </div>
        <h1 style={{ fontSize: '26px', marginBottom: '4px' }}>CPCMS Portal</h1>
        <p style={{ color: 'var(--muted-text)', fontSize: '13px' }}>
          Course Project Configuration and Management System
        </p>
      </div>

      {error && <div className="banner banner-error">{error}</div>}

      <div className="panel" style={{ padding: '24px' }}>
        <form onSubmit={handleSubmit} style={{ width: '100%' }}>
          <div className="form-group">
            <label htmlFor="identifier">Identifier / Login ID</label>
            <input
              id="identifier"
              type="text"
              required
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="e.g. 23MIS0480 or meenakshi.k@univ.edu"
            />
            <div className="form-help">
              Use your Student Register Number, Faculty Code, or Official Email.
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
              placeholder="••••••••"
            />
          </div>

          <div style={{ marginTop: '20px' }}>
            <button type="submit" className="primary" disabled={loading} style={{ width: '100%', padding: '10px' }}>
              {loading ? 'Signing in...' : 'Sign In to Portal'}
            </button>
          </div>
        </form>

        {/* Quick fill chips for testing */}
        <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border-color)' }}>
          <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--muted-text)', textTransform: 'uppercase' }}>
            Quick Demo Logins:
          </span>
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap' }}>
            <button
              type="button"
              style={{ fontSize: '11px', padding: '4px 8px' }}
              onClick={() => handleQuickFill('meenakshi.k@univ.edu', 'Password123!')}
            >
              Faculty (Meenakshi)
            </button>
            <button
              type="button"
              style={{ fontSize: '11px', padding: '4px 8px' }}
              onClick={() => handleQuickFill('23MIS0480', 'Password123!')}
            >
              Student (Ananya)
            </button>
            <button
              type="button"
              style={{ fontSize: '11px', padding: '4px 8px' }}
              onClick={() => handleQuickFill('23MIS0490', 'Password123!')}
            >
              Student (Karthik)
            </button>
          </div>
        </div>
      </div>

      <div style={{ marginTop: '16px', fontSize: '13px', display: 'flex', justifyContent: 'space-between' }}>
        <Link to="/register/student">Register Student</Link>
        <Link to="/register/faculty">Register Faculty</Link>
      </div>
    </div>
  );
};
