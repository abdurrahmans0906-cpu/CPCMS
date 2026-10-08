import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../lib/AuthContext';

export const Sidebar: React.FC = () => {
  const { role } = useAuth();

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
          Dashboard
        </NavLink>

        {role === 'FACULTY' && (
          <>
            <NavLink to="/courses" className={({ isActive }) => (isActive ? 'active' : '')}>
              Courses
            </NavLink>
            <NavLink to="/projects" className={({ isActive }) => (isActive ? 'active' : '')}>
              Projects
            </NavLink>
            <NavLink to="/projects/new" className={({ isActive }) => (isActive ? 'active' : '')}>
              Create Project
            </NavLink>
          </>
        )}

        {role === 'STUDENT' && (
          <>
            <NavLink to="/projects" className={({ isActive }) => (isActive ? 'active' : '')}>
              My Projects
            </NavLink>
            <NavLink to="/invitations" className={({ isActive }) => (isActive ? 'active' : '')}>
              Invitations
            </NavLink>
          </>
        )}

        <NavLink to="/notifications" className={({ isActive }) => (isActive ? 'active' : '')}>
          Notifications
        </NavLink>
      </nav>
    </aside>
  );
};
