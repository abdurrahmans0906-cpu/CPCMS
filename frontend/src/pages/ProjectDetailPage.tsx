import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  apiRequest,
  SchemaProjectOut,
  SchemaProjectStudentOut,
  SchemaTeamOut,
  SchemaAnalyticsOut,
} from '../api/client';
import { useAuth } from '../lib/AuthContext';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { StatusBadge } from '../components/StatusBadge';

export const ProjectDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { role } = useAuth();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<
    'overview' | 'students' | 'teams' | 'rules' | 'deadlines' | 'reviews' | 'criteria' | 'analytics'
  >('overview');

  // Bulk enrollment state
  const [bulkRegNumbers, setBulkRegNumbers] = useState('');
  const [enrollMsg, setEnrollMsg] = useState<string | null>(null);

  // New Deadline state
  const [newDlKind, setNewDlKind] = useState('review');
  const [newDlTitle, setNewDlTitle] = useState('');
  const [newDlDue, setNewDlDue] = useState('');

  // New Review state
  const [newRevTitle, setNewRevTitle] = useState('');
  const [newRevStart, setNewRevStart] = useState('');
  const [newRevMode, setNewRevMode] = useState<'online' | 'offline'>('online');
  const [newRevLink, setNewRevLink] = useState('');
  const [newRevVenue, setNewRevVenue] = useState('');
  const [newRevAgenda, setNewRevAgenda] = useState('');

  // New Criterion state
  const [newCritName, setNewCritName] = useState('');
  const [newCritMarks, setNewCritMarks] = useState(10);

  // Fetch Project
  const { data: project, isLoading: projLoading } = useQuery<SchemaProjectOut>({
    queryKey: ['project', id],
    queryFn: () => apiRequest(`/projects/${id}`),
    enabled: !!id,
  });

  // Fetch Students
  const { data: students, isLoading: studentsLoading } = useQuery<SchemaProjectStudentOut[]>({
    queryKey: ['project-students', id],
    queryFn: () => apiRequest(`/projects/${id}/students`),
    enabled: !!id && (activeTab === 'students' || activeTab === 'teams'),
  });

  // Fetch Teams
  const { data: teams, isLoading: teamsLoading } = useQuery<SchemaTeamOut[]>({
    queryKey: ['project-teams', id],
    queryFn: () => apiRequest(`/projects/${id}/teams`),
    enabled: !!id && activeTab === 'teams',
  });

  // Fetch Unassigned students
  const { data: unassigned, isLoading: unassignedLoading } = useQuery<SchemaProjectStudentOut[]>({
    queryKey: ['project-unassigned', id],
    queryFn: () => apiRequest(`/projects/${id}/unassigned`),
    enabled: !!id && role === 'FACULTY' && activeTab === 'teams',
  });

  // Fetch Analytics
  const { data: analytics, isLoading: analyticsLoading } = useQuery<SchemaAnalyticsOut>({
    queryKey: ['project-analytics', id],
    queryFn: () => apiRequest(`/projects/${id}/analytics`),
    enabled: !!id && role === 'FACULTY' && activeTab === 'analytics',
  });

  // Enroll mutation
  const enrollMutation = useMutation({
    mutationFn: (text: string) =>
      apiRequest(`/projects/${id}/students`, {
        method: 'POST',
        body: { register_numbers: text },
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(['project-students', id], data);
      setBulkRegNumbers('');
      setEnrollMsg('Students enrolled successfully.');
    },
    onError: (err: any) => setEnrollMsg(err.message || 'Failed to enroll students.'),
  });

  // Auto assign mutation
  const autoAssignMutation = useMutation({
    mutationFn: () => apiRequest(`/projects/${id}/auto-assign`, { method: 'POST' }),
    onSuccess: (res: any) => {
      queryClient.invalidateQueries({ queryKey: ['project-teams', id] });
      queryClient.invalidateQueries({ queryKey: ['project-unassigned', id] });
      queryClient.invalidateQueries({ queryKey: ['project-students', id] });
      alert(res.message || 'Auto-assignment completed.');
    },
    onError: (err: any) => alert(err.message || 'Auto-assign failed.'),
  });

  // Add deadline mutation
  const addDeadlineMutation = useMutation({
    mutationFn: (body: any) => apiRequest(`/projects/${id}/deadlines`, { method: 'POST', body }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', id] });
      setNewDlTitle('');
      setNewDlDue('');
    },
  });

  // Add review mutation
  const addReviewMutation = useMutation({
    mutationFn: (body: any) => apiRequest(`/projects/${id}/reviews`, { method: 'POST', body }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', id] });
      setNewRevTitle('');
      setNewRevStart('');
      setNewRevLink('');
      setNewRevVenue('');
      setNewRevAgenda('');
    },
  });

  // Add criterion mutation
  const addCriterionMutation = useMutation({
    mutationFn: (body: any) => apiRequest(`/projects/${id}/criteria`, { method: 'POST', body }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', id] });
      setNewCritName('');
      setNewCritMarks(10);
    },
  });

  if (projLoading) return <div>Loading...</div>;
  if (!project) return <div>Project not found.</div>;

  const totalCriteriaMarks = project.evaluation_criteria?.reduce((sum: number, c: any) => sum + c.max_marks, 0) || 0;

  return (
    <div>
      <Breadcrumbs
        items={[
          { label: 'Dashboard', to: '/' },
          { label: 'Projects', to: '/projects' },
          { label: project.name },
        ]}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div>
          <h1>{project.name}</h1>
          <p style={{ color: 'var(--muted-text)', fontSize: '13px' }}>
            Course: <strong>{project.course_code}</strong> ({project.course_name}) | Term: {project.semester}{' '}
            {project.academic_year}
          </p>
        </div>
        <StatusBadge status={project.status} />
      </div>

      {/* Tabs */}
      <div className="tabs-bar">
        <button
          type="button"
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'students' ? 'active' : ''}`}
          onClick={() => setActiveTab('students')}
        >
          Students ({students?.length || (project as any).enrolled_students?.length || 0})
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'teams' ? 'active' : ''}`}
          onClick={() => setActiveTab('teams')}
        >
          Teams
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'rules' ? 'active' : ''}`}
          onClick={() => setActiveTab('rules')}
        >
          Rules & Governance
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'deadlines' ? 'active' : ''}`}
          onClick={() => setActiveTab('deadlines')}
        >
          Deadlines ({project.deadlines?.length || 0})
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'reviews' ? 'active' : ''}`}
          onClick={() => setActiveTab('reviews')}
        >
          Reviews
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'criteria' ? 'active' : ''}`}
          onClick={() => setActiveTab('criteria')}
        >
          Evaluation Criteria
        </button>
        {role === 'FACULTY' && (
          <button
            type="button"
            className={`tab-btn ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            Analytics & Reports
          </button>
        )}
      </div>

      {/* 1. OVERVIEW TAB */}
      {activeTab === 'overview' && (
        <div>
          {project.description && (
            <div className="panel">
              <h2>Project Description</h2>
              <p style={{ whiteSpace: 'pre-line' }}>{project.description}</p>
            </div>
          )}

          {project.problem_statement && (
            <div className="panel">
              <h2>Problem Statement Guidelines</h2>
              <p style={{ whiteSpace: 'pre-line' }}>{project.problem_statement}</p>
            </div>
          )}

          {project.objectives && (
            <div className="panel">
              <h2>Objectives</h2>
              <p style={{ whiteSpace: 'pre-line' }}>{project.objectives}</p>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="panel">
              <h2>Project Themes</h2>
              {!project.themes || project.themes.length === 0 ? (
                <p style={{ color: 'var(--muted-text)' }}>No themes specified.</p>
              ) : (
                <ul style={{ paddingLeft: '18px' }}>
                  {project.themes.map((t: any) => (
                    <li key={t.id}>{t.name}</li>
                  ))}
                </ul>
              )}
            </div>

            <div className="panel">
              <h2>Expected Outcomes</h2>
              {!project.outcomes || project.outcomes.length === 0 ? (
                <p style={{ color: 'var(--muted-text)' }}>No outcomes specified.</p>
              ) : (
                <ol style={{ paddingLeft: '18px' }}>
                  {project.outcomes.map((o: any) => (
                    <li key={o.id}>{o.text}</li>
                  ))}
                </ol>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 2. STUDENTS TAB */}
      {activeTab === 'students' && (
        <div>
          {role === 'FACULTY' && (
            <div className="panel" style={{ maxWidth: '560px' }}>
              <h2>Enroll Students</h2>
              <p style={{ fontSize: '12px', color: 'var(--muted-text)', marginBottom: '8px' }}>
                Paste register numbers (one per line or comma-separated). Unregistered students will be linked automatically when they register.
              </p>
              {enrollMsg && (
                <div
                  className={`banner ${enrollMsg.includes('success') ? 'banner-success' : 'banner-error'}`}
                >
                  {enrollMsg}
                </div>
              )}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (bulkRegNumbers.trim()) enrollMutation.mutate(bulkRegNumbers.trim());
                }}
              >
                <div className="form-group">
                  <textarea
                    rows={4}
                    required
                    value={bulkRegNumbers}
                    onChange={(e) => setBulkRegNumbers(e.target.value)}
                    placeholder="23MIS0475&#10;23MIS0480&#10;23MIS0492"
                  />
                </div>
                <button type="submit" className="primary" disabled={enrollMutation.isPending}>
                  {enrollMutation.isPending ? 'Enrolling...' : 'Enroll Students'}
                </button>
              </form>
            </div>
          )}

          <div className="panel">
            <h2>Enrolled Students List</h2>
            {studentsLoading ? (
              <p>Loading...</p>
            ) : !students || students.length === 0 ? (
              <p style={{ color: 'var(--muted-text)' }}>No students enrolled in this project yet.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Register Number</th>
                    <th>Student Name</th>
                    <th>Email</th>
                    <th>Department</th>
                    <th>Registration Status</th>
                    <th>Team Assigned</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((s) => (
                    <tr key={s.id}>
                      <td><strong>{s.register_number}</strong></td>
                      <td>{s.student_name || <span style={{ color: 'var(--muted-text)' }}>Not registered yet</span>}</td>
                      <td>{s.student_email || '-'}</td>
                      <td>{s.department || '-'}</td>
                      <td>
                        {s.is_registered ? (
                          <span style={{ color: 'var(--success-color)' }}>REGISTERED</span>
                        ) : (
                          <span style={{ color: 'var(--warning-color)' }}>PENDING</span>
                        )}
                      </td>
                      <td>
                        {s.team_id ? (
                          <Link to={`/teams/${s.team_id}`}>Team {s.team_number}</Link>
                        ) : (
                          <span style={{ color: 'var(--muted-text)' }}>Unassigned</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* 3. TEAMS TAB */}
      {activeTab === 'teams' && (
        <div>
          {/* Unassigned Students Panel for Faculty */}
          {role === 'FACULTY' && unassigned && unassigned.length > 0 && (
            <div className="panel" style={{ borderColor: 'var(--warning-color)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2>Unassigned Students ({unassigned.length})</h2>
                <button
                  type="button"
                  className="primary"
                  onClick={() => autoAssignMutation.mutate()}
                  disabled={autoAssignMutation.isPending}
                >
                  {autoAssignMutation.isPending ? 'Auto-assigning...' : 'Auto-assign Students'}
                </button>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--muted-text)', margin: '4px 0 10px 0' }}>
                These students are enrolled but have not joined or formed a team. Auto-assign will fill open teams first, then generate new teams within size rules.
              </p>
              <table>
                <thead>
                  <tr>
                    <th>Register Number</th>
                    <th>Name</th>
                    <th>Account Status</th>
                  </tr>
                </thead>
                <tbody>
                  {unassigned.map((u) => (
                    <tr key={u.id}>
                      <td><strong>{u.register_number}</strong></td>
                      <td>{u.student_name || 'Not registered yet'}</td>
                      <td>{u.is_registered ? 'Registered' : 'Not registered yet'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Student create team prompt if not in a team */}
          {role === 'STUDENT' && !project.user_team_id && project.team_formation_mode !== 'faculty' && (
            <div className="panel" style={{ maxWidth: '480px' }}>
              <h2>Form a New Team</h2>
              <p style={{ fontSize: '13px', color: 'var(--muted-text)', marginBottom: '8px' }}>
                You are not in a team yet. Create a team and invite enrolled classmates. Team size must be {project.min_team_size} to {project.max_team_size} members.
              </p>
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  const target = e.currentTarget;
                  const titleInput = (target.elements.namedItem('team_title') as HTMLInputElement).value;
                  try {
                    await apiRequest(`/projects/${project.id}/teams`, {
                      method: 'POST',
                      body: { title: titleInput.trim() },
                    });
                    queryClient.invalidateQueries({ queryKey: ['project', id] });
                    queryClient.invalidateQueries({ queryKey: ['project-teams', id] });
                  } catch (err: any) {
                    alert(err.message || 'Failed to create team.');
                  }
                }}
              >
                <div className="form-group">
                  <label htmlFor="team-title-input">Team Title</label>
                  <input id="team-title-input" name="team_title" type="text" required placeholder="e.g. SCM Automation Group" />
                </div>
                <button type="submit" className="primary">Create Team</button>
              </form>
            </div>
          )}

          <div className="panel">
            <h2>Project Teams</h2>
            {teamsLoading ? (
              <p>Loading...</p>
            ) : !teams || teams.length === 0 ? (
              <p style={{ color: 'var(--muted-text)' }}>No teams formed yet for this project.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Team #</th>
                    <th>Title</th>
                    <th>Members</th>
                    <th>Status</th>
                    <th>Progress</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {teams.map((t) => (
                    <tr key={t.id}>
                      <td><strong>Team {t.number}</strong></td>
                      <td>{t.title}</td>
                      <td>
                        {t.members.map((m: any) => (
                          <div key={m.id} style={{ fontSize: '12px' }}>
                            {m.student_name} ({m.student_register_number}) {m.role === 'leader' && '<strong>[Leader]</strong>'}
                          </div>
                        ))}
                      </td>
                      <td>
                        <StatusBadge status={t.status} />
                        {t.is_delayed && (
                          <span style={{ display: 'block', color: 'var(--danger-color)', fontSize: '11px', fontWeight: 'bold' }}>
                            DELAYED
                          </span>
                        )}
                      </td>
                      <td>
                        <div style={{ width: '100px' }}>
                          <progress value={t.overall_progress || 0} max={100} />
                          <span style={{ fontSize: '11px', color: 'var(--muted-text)' }}>{Math.round(t.overall_progress || 0)}%</span>
                        </div>
                      </td>
                      <td>
                        <Link to={`/teams/${t.id}`}>Open Team SCM</Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* 4. RULES TAB */}
      {activeTab === 'rules' && (
        <div className="panel" style={{ maxWidth: '640px' }}>
          <h2>Project Configuration & Governance Rules</h2>
          <div className="desc-list">
            <span className="desc-label">Team Formation Mode:</span>
            <span className="desc-value">{project.team_formation_mode}</span>

            <span className="desc-label">Team Size Constraints:</span>
            <span className="desc-value">{project.min_team_size} min - {project.max_team_size} max</span>

            <span className="desc-label">Formation Deadline:</span>
            <span className="desc-value">
              {project.team_formation_deadline ? new Date(project.team_formation_deadline).toLocaleString() : 'None'}
            </span>

            <span className="desc-label">Allowed File Types:</span>
            <span className="desc-value">{project.allowed_file_exts?.join(', ')}</span>

            <span className="desc-label">Max File Size:</span>
            <span className="desc-value">{project.max_file_mb} MB</span>

            <span className="desc-label">Late Policy:</span>
            <span className="desc-value">
              {project.late_policy === 'reject' && 'Reject late submissions strictly'}
              {project.late_policy === 'allow_flagged' && 'Allow and mark as late'}
              {project.late_policy === 'allow_penalty' && `Allow with ${project.late_penalty_percent}% grade penalty`}
            </span>

            <span className="desc-label">Branching Policy:</span>
            <span className="desc-value">{project.branching_policy === 'gitflow_lite' ? 'GitFlow Lite (main, develop, feature/*, release/*, hotfix/*)' : 'None'}</span>

            <span className="desc-label">Artifact Versioning:</span>
            <span className="desc-value">{project.versioning_required ? 'Required (major/minor bumps)' : 'Optional'}</span>

            <span className="desc-label">Git Integration:</span>
            <span className="desc-value">{project.git_required ? 'Mandatory repo link and commit SHAs' : 'Optional'}</span>

            <span className="desc-label">Change Control (CR):</span>
            <span className="desc-value">{project.change_request_required ? 'Mandatory for modifying locked CIs' : 'Disabled'}</span>
          </div>
        </div>
      )}

      {/* 5. DEADLINES TAB */}
      {activeTab === 'deadlines' && (
        <div>
          {role === 'FACULTY' && (
            <div className="panel" style={{ maxWidth: '560px' }}>
              <h2>Add Project Deadline</h2>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (newDlTitle && newDlDue) {
                    addDeadlineMutation.mutate({
                      kind: newDlKind,
                      title: newDlTitle.trim(),
                      due_at: new Date(newDlDue).toISOString(),
                    });
                  }
                }}
              >
                <div className="form-row">
                  <div className="form-group" style={{ flex: '1' }}>
                    <label htmlFor="dl-kind-select">Kind</label>
                    <select id="dl-kind-select" value={newDlKind} onChange={(e) => setNewDlKind(e.target.value)}>
                      <option value="team_formation">Team Formation</option>
                      <option value="proposal">Proposal Submission</option>
                      <option value="srs">SRS Submission</option>
                      <option value="review">Review Evaluation</option>
                      <option value="final">Final Submission</option>
                      <option value="other">Other Milestone</option>
                    </select>
                  </div>
                  <div className="form-group" style={{ flex: '2' }}>
                    <label htmlFor="dl-due-input">Due Date & Time</label>
                    <input
                      id="dl-due-input"
                      type="datetime-local"
                      required
                      value={newDlDue}
                      onChange={(e) => setNewDlDue(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="dl-title-input">Deadline Title</label>
                  <input
                    id="dl-title-input"
                    type="text"
                    required
                    value={newDlTitle}
                    onChange={(e) => setNewDlTitle(e.target.value)}
                    placeholder="e.g. SRS Document Submission"
                  />
                </div>

                <button type="submit" className="primary" disabled={addDeadlineMutation.isPending}>
                  Add Deadline
                </button>
              </form>
            </div>
          )}

          <div className="panel">
            <h2>Project Deadlines Schedule</h2>
            {!project.deadlines || project.deadlines.length === 0 ? (
              <p style={{ color: 'var(--muted-text)' }}>No deadlines configured.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Milestone</th>
                    <th>Kind</th>
                    <th>Due Date</th>
                  </tr>
                </thead>
                <tbody>
                  {project.deadlines.map((d: any) => (
                    <tr key={d.id}>
                      <td><strong>{d.title}</strong></td>
                      <td>{d.kind}</td>
                      <td>{new Date(d.due_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* 6. REVIEWS TAB */}
      {activeTab === 'reviews' && (
        <div>
          {role === 'FACULTY' && (
            <div className="panel" style={{ maxWidth: '560px' }}>
              <h2>Schedule a Review Milestone</h2>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (newRevTitle && newRevStart) {
                    addReviewMutation.mutate({
                      title: newRevTitle.trim(),
                      start_at: new Date(newRevStart).toISOString(),
                      mode: newRevMode,
                      meeting_link: newRevLink.trim() || undefined,
                      venue: newRevVenue.trim() || undefined,
                      agenda: newRevAgenda.trim() || undefined,
                    });
                  }
                }}
              >
                <div className="form-group">
                  <label htmlFor="rev-title-input">Review Title</label>
                  <input
                    id="rev-title-input"
                    type="text"
                    required
                    value={newRevTitle}
                    onChange={(e) => setNewRevTitle(e.target.value)}
                    placeholder="e.g. Review 1 - Architecture & Design"
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="rev-start-input">Scheduled Date & Time</label>
                    <input
                      id="rev-start-input"
                      type="datetime-local"
                      required
                      value={newRevStart}
                      onChange={(e) => setNewRevStart(e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="rev-mode-select">Mode</label>
                    <select id="rev-mode-select" value={newRevMode} onChange={(e) => setNewRevMode(e.target.value as any)}>
                      <option value="online">Online</option>
                      <option value="offline">Offline / In-person</option>
                    </select>
                  </div>
                </div>

                {newRevMode === 'online' ? (
                  <div className="form-group">
                    <label htmlFor="rev-link-input">Meeting Link</label>
                    <input
                      id="rev-link-input"
                      type="text"
                      value={newRevLink}
                      onChange={(e) => setNewRevLink(e.target.value)}
                      placeholder="e.g. https://meet.google.com/xyz-abc"
                    />
                  </div>
                ) : (
                  <div className="form-group">
                    <label htmlFor="rev-venue-input">Venue / Room</label>
                    <input
                      id="rev-venue-input"
                      type="text"
                      value={newRevVenue}
                      onChange={(e) => setNewRevVenue(e.target.value)}
                      placeholder="e.g. Lab 304, Tech Tower"
                    />
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="rev-agenda-input">Agenda / Instructions</label>
                  <textarea
                    id="rev-agenda-input"
                    rows={2}
                    value={newRevAgenda}
                    onChange={(e) => setNewRevAgenda(e.target.value)}
                  />
                </div>

                <button type="submit" className="primary" disabled={addReviewMutation.isPending}>
                  Schedule Review
                </button>
              </form>
            </div>
          )}

          <div className="panel">
            <h2>Scheduled Reviews</h2>
            {!(project as any).reviews || (project as any).reviews.length === 0 ? (
              <p style={{ color: 'var(--muted-text)' }}>No review sessions scheduled yet.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Review Title</th>
                    <th>Date & Time</th>
                    <th>Mode</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {(project as any).reviews.map((r: any) => (
                    <tr key={r.id}>
                      <td><strong>{r.title}</strong></td>
                      <td>{new Date(r.start_at).toLocaleString()}</td>
                      <td>{r.mode.toUpperCase()}</td>
                      <td>
                        {r.mode === 'online' ? (
                          r.meeting_link ? <a href={r.meeting_link} target="_blank" rel="noreferrer">Meeting Link</a> : 'Online'
                        ) : (
                          r.venue || 'In-person'
                        )}
                        {r.agenda && <div style={{ fontSize: '12px', color: 'var(--muted-text)' }}>Agenda: {r.agenda}</div>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* 7. EVALUATION CRITERIA TAB */}
      {activeTab === 'criteria' && (
        <div>
          <div className="panel" style={{ maxWidth: '560px' }}>
            <h2>Evaluation Criteria & Weights</h2>
            <p style={{ fontSize: '13px', marginBottom: '8px' }}>
              Criteria Marks Sum:{' '}
              <strong style={{ color: totalCriteriaMarks === project.total_marks ? 'var(--success-color)' : 'var(--danger-color)' }}>
                {totalCriteriaMarks} / {project.total_marks} marks
              </strong>
            </p>

            {totalCriteriaMarks !== project.total_marks && (
              <div className="banner banner-error">
                The sum of criteria ({totalCriteriaMarks}) must equal total marks ({project.total_marks}) before any evaluation can be saved.
              </div>
            )}

            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Criterion Name</th>
                  <th>Max Marks</th>
                </tr>
              </thead>
              <tbody>
                {project.evaluation_criteria?.map((crit: any, idx: number) => (
                  <tr key={crit.id}>
                    <td>{idx + 1}</td>
                    <td>{crit.name}</td>
                    <td>{crit.max_marks}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {role === 'FACULTY' && (
              <form
                style={{ marginTop: '16px' }}
                onSubmit={(e) => {
                  e.preventDefault();
                  if (newCritName) {
                    addCriterionMutation.mutate({
                      name: newCritName.trim(),
                      max_marks: Number(newCritMarks),
                      position: (project.evaluation_criteria?.length || 0) + 1,
                    });
                  }
                }}
              >
                <h3>Add Criterion</h3>
                <div className="form-row">
                  <div className="form-group" style={{ flex: '2' }}>
                    <label htmlFor="crit-name-input">Criterion</label>
                    <input
                      id="crit-name-input"
                      type="text"
                      required
                      value={newCritName}
                      onChange={(e) => setNewCritName(e.target.value)}
                      placeholder="e.g. Testing & Verification"
                    />
                  </div>
                  <div className="form-group" style={{ flex: '1' }}>
                    <label htmlFor="crit-marks-input">Max Marks</label>
                    <input
                      id="crit-marks-input"
                      type="number"
                      min={1}
                      required
                      value={newCritMarks}
                      onChange={(e) => setNewCritMarks(Number(e.target.value))}
                    />
                  </div>
                </div>
                <button type="submit" className="primary" disabled={addCriterionMutation.isPending}>
                  Add Criterion
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      {/* 8. ANALYTICS & REPORTS TAB (Faculty) */}
      {activeTab === 'analytics' && role === 'FACULTY' && (
        <div>
          {analyticsLoading ? (
            <p>Loading analytics...</p>
          ) : !analytics ? (
            <p>No analytics data available.</p>
          ) : (
            <div>
              <div className="panel">
                <h2>Project Analytics Overview</h2>
                <div className="desc-list">
                  <span className="desc-label">Total Students Enrolled:</span>
                  <span className="desc-value">{analytics.total_students}</span>

                  <span className="desc-label">Total Teams Formed:</span>
                  <span className="desc-value">{analytics.total_teams}</span>

                  <span className="desc-label">Active / Completed Teams:</span>
                  <span className="desc-value">{analytics.active_teams} active / {analytics.completed_teams} completed</span>

                  <span className="desc-label">Pending Proposals:</span>
                  <span className="desc-value">{analytics.pending_proposals}</span>

                  <span className="desc-label">Pending Change Requests:</span>
                  <span className="desc-value">{analytics.pending_changes}</span>

                  <span className="desc-label">Average Evaluation Score:</span>
                  <span className="desc-value">{analytics.average_score !== null ? `${analytics.average_score} / ${project.total_marks}` : 'No evaluations yet'}</span>
                </div>
              </div>

              {analytics.delayed_teams.length > 0 && (
                <div className="panel" style={{ borderColor: 'var(--danger-color)' }}>
                  <h2 style={{ color: 'var(--danger-color)' }}>Delayed Teams ({analytics.delayed_teams.length})</h2>
                  <p style={{ fontSize: '13px', color: 'var(--muted-text)' }}>
                    These teams have passed an active project deadline without making a required submission.
                  </p>
                  <ul>
                    {analytics.delayed_teams.map((dt: any) => (
                      <li key={dt.team_id}>
                        <Link to={`/teams/${dt.team_id}`}>Team {dt.number}: {dt.title}</Link> ({dt.status})
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {analytics.inactive_teams.length > 0 && (
                <div className="panel">
                  <h2>Inactive Teams (No activity in 14 days)</h2>
                  <ul>
                    {analytics.inactive_teams.map((it: any) => (
                      <li key={it.team_id}>
                        <Link to={`/teams/${it.team_id}`}>Team {it.number}: {it.title}</Link> - Last active: {it.last_active ? new Date(it.last_active).toLocaleDateString() : 'Never'}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
