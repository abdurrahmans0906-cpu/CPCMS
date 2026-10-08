import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './lib/AuthContext';
import { Layout } from './components/Layout';

import { LoginPage } from './pages/LoginPage';
import { StudentRegisterPage } from './pages/StudentRegisterPage';
import { FacultyRegisterPage } from './pages/FacultyRegisterPage';
import { FacultyDashboard } from './pages/FacultyDashboard';
import { StudentDashboard } from './pages/StudentDashboard';
import { CoursesPage } from './pages/CoursesPage';
import { ProjectsListPage } from './pages/ProjectsListPage';
import { CreateProjectPage } from './pages/CreateProjectPage';
import { ProjectDetailPage } from './pages/ProjectDetailPage';
import { TeamDetailPage } from './pages/TeamDetailPage';
import { CRDetailPage } from './pages/CRDetailPage';
import { CIComparePage } from './pages/CIComparePage';
import { InvitationsPage } from './pages/InvitationsPage';
import { NotificationsPage } from './pages/NotificationsPage';

const ProtectedRoute: React.FC<{ children: React.ReactNode; requiredRole?: 'STUDENT' | 'FACULTY' }> = ({
  children,
  requiredRole,
}) => {
  const { isAuthenticated, isLoading, role } = useAuth();

  if (isLoading) {
    return (
      <div style={{ padding: '24px', fontFamily: 'sans-serif' }}>
        <p>Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && role !== requiredRole) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

const DashboardRouter: React.FC = () => {
  const { role } = useAuth();
  if (role === 'FACULTY') {
    return <FacultyDashboard />;
  }
  return <StudentDashboard />;
};

export const App: React.FC = () => {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register/student" element={<StudentRegisterPage />} />
      <Route path="/register/faculty" element={<FacultyRegisterPage />} />

      {/* Authenticated routes inside Layout */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardRouter />} />

        {/* Courses (Faculty only) */}
        <Route
          path="courses"
          element={
            <ProtectedRoute requiredRole="FACULTY">
              <CoursesPage />
            </ProtectedRoute>
          }
        />

        {/* Projects */}
        <Route path="projects" element={<ProjectsListPage />} />
        <Route
          path="projects/new"
          element={
            <ProtectedRoute requiredRole="FACULTY">
              <CreateProjectPage />
            </ProtectedRoute>
          }
        />
        <Route path="projects/:id" element={<ProjectDetailPage />} />

        {/* Teams & SCM */}
        <Route path="teams/:id" element={<TeamDetailPage />} />

        {/* Change Request Detail */}
        <Route path="change-requests/:id" element={<CRDetailPage />} />

        {/* Version Comparison */}
        <Route path="cis/:ciId/compare" element={<CIComparePage />} />

        {/* Invitations (Student only) */}
        <Route
          path="invitations"
          element={
            <ProtectedRoute requiredRole="STUDENT">
              <InvitationsPage />
            </ProtectedRoute>
          }
        />

        {/* In-app Notifications */}
        <Route path="notifications" element={<NotificationsPage />} />
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
