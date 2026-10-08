import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  apiRequest,
  SchemaTeamOut,
  SchemaProposalOut,
  SchemaCIOut,
  SchemaBaselineOut,
  SchemaChangeRequestOut,
  SchemaRepositoryOut,
  SchemaProgressReportOut,
  SchemaSubmissionOut,
  SchemaEvaluationOut,
  SchemaReleaseOut,
  SchemaStatusAccountingReport,
  SchemaAuditReportOut,
  SchemaTimelineEvent,
  SchemaProjectOut,
} from '../api/client';
import { useAuth } from '../lib/AuthContext';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { StatusBadge } from '../components/StatusBadge';

export const TeamDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user, role } = useAuth();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<
    | 'overview'
    | 'proposal'
    | 'cis'
    | 'versions'
    | 'baselines'
    | 'change_requests'
    | 'git'
    | 'progress'
    | 'submissions'
    | 'evaluation'
    | 'releases'
    | 'status_accounting'
    | 'audit_report'
    | 'timeline'
  >('overview');

  // Fetch Team
  const { data: team, isLoading: teamLoading } = useQuery<SchemaTeamOut>({
    queryKey: ['team', id],
    queryFn: () => apiRequest(`/teams/${id}`),
    enabled: !!id,
  });

  // Fetch Parent Project for rules & themes
  const { data: project } = useQuery<SchemaProjectOut>({
    queryKey: ['project', team?.project_id],
    queryFn: () => apiRequest(`/projects/${team?.project_id}`),
    enabled: !!team?.project_id,
  });

  // Fetch Proposals
  const { data: proposals } = useQuery<SchemaProposalOut[]>({
    queryKey: ['proposals', id],
    queryFn: () => apiRequest(`/teams/${id}/proposals`),
    enabled: !!id && activeTab === 'proposal',
  });

  // Fetch CIs
  const { data: cis } = useQuery<SchemaCIOut[]>({
    queryKey: ['cis', id],
    queryFn: () => apiRequest(`/teams/${id}/cis`),
    enabled: !!id && (activeTab === 'cis' || activeTab === 'versions' || activeTab === 'baselines' || activeTab === 'change_requests' || activeTab === 'status_accounting'),
  });

  // Fetch Baselines
  const { data: baselines } = useQuery<SchemaBaselineOut[]>({
    queryKey: ['baselines', id],
    queryFn: () => apiRequest(`/teams/${id}/baselines`),
    enabled: !!id && (activeTab === 'baselines' || activeTab === 'releases'),
  });

  // Fetch Change Requests
  const { data: changeRequests } = useQuery<SchemaChangeRequestOut[]>({
    queryKey: ['change-requests', id],
    queryFn: () => apiRequest(`/teams/${id}/change-requests`),
    enabled: !!id && (activeTab === 'change_requests' || activeTab === 'versions'),
  });

  // Fetch Repository
  const { data: repository, refetch: refetchRepo } = useQuery<SchemaRepositoryOut>({
    queryKey: ['repository', id],
    queryFn: () => apiRequest(`/teams/${id}/repository`),
    enabled: !!id && activeTab === 'git',
    retry: false,
  });

  // Fetch Progress Reports
  const { data: progressReports } = useQuery<SchemaProgressReportOut[]>({
    queryKey: ['progress', id],
    queryFn: () => apiRequest(`/teams/${id}/progress`),
    enabled: !!id && activeTab === 'progress',
  });

  // Fetch Submissions
  const { data: submissions } = useQuery<SchemaSubmissionOut[]>({
    queryKey: ['submissions', id],
    queryFn: () => apiRequest(`/teams/${id}/submissions`),
    enabled: !!id && activeTab === 'submissions',
  });

  // Fetch Evaluations
  const { data: evaluations } = useQuery<SchemaEvaluationOut[]>({
    queryKey: ['evaluations', id],
    queryFn: () => apiRequest(`/teams/${id}/evaluations`),
    enabled: !!id && activeTab === 'evaluation',
  });

  // Fetch Releases
  const { data: releases } = useQuery<SchemaReleaseOut[]>({
    queryKey: ['releases', id],
    queryFn: () => apiRequest(`/teams/${id}/releases`),
    enabled: !!id && activeTab === 'releases',
  });

  // Fetch Status Accounting
  const { data: statusAccounting } = useQuery<SchemaStatusAccountingReport>({
    queryKey: ['status-accounting', id],
    queryFn: () => apiRequest(`/teams/${id}/status-accounting`),
    enabled: !!id && activeTab === 'status_accounting',
  });

  // Fetch Audit Report
  const { data: auditReport } = useQuery<SchemaAuditReportOut>({
    queryKey: ['audit-report', id],
    queryFn: () => apiRequest(`/teams/${id}/audit-report`),
    enabled: !!id && activeTab === 'audit_report',
  });

  // Fetch Timeline
  const { data: timeline } = useQuery<SchemaTimelineEvent[]>({
    queryKey: ['timeline', id],
    queryFn: () => apiRequest(`/teams/${id}/timeline`),
    enabled: !!id && activeTab === 'timeline',
  });

  // --- LOCAL FORM STATES ---
  // Proposal
  const [propTitle, setPropTitle] = useState('');
  const [propAbstract, setPropAbstract] = useState('');
  const [propProblem, setPropProblem] = useState('');
  const [propObjectives, setPropObjectives] = useState('');
  const [propOutcome, setPropOutcome] = useState('');
  const [propThemeId, setPropThemeId] = useState('');
  const [propFeedback, setPropFeedback] = useState('');

  // CI Creation
  const [newCiName, setNewCiName] = useState('');
  const [newCiType, setNewCiType] = useState('requirements');

  // CI Version Upload
  const [uploadCiId, setUploadCiId] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadDesc, setUploadDesc] = useState('');
  const [uploadBump, setUploadBump] = useState<'minor' | 'major'>('minor');
  const [uploadCommitSha, setUploadCommitSha] = useState('');
  const [uploadCrId, setUploadCrId] = useState('');

  // Version Rollback
  const [rollbackTargetId, setRollbackTargetId] = useState('');
  const [rollbackReason, setRollbackReason] = useState('');
  const [rollbackCrId, setRollbackCrId] = useState('');

  // Baseline Creation
  const [blName, setBlName] = useState('');
  const [blDesc, setBlDesc] = useState('');
  const [blVersionIds, setBlVersionIds] = useState<string[]>([]);

  // Change Request Creation
  const [crTitle, setCrTitle] = useState('');
  const [crDesc, setCrDesc] = useState('');
  const [crReason, setCrReason] = useState('');
  const [crPriority, setCrPriority] = useState<'low' | 'medium' | 'high' | 'critical'>('medium');
  const [crAffectedCis, setCrAffectedCis] = useState<string[]>([]);
  const [crComponents, setCrComponents] = useState<string[]>([]);

  // Git repo linking
  const [gitUrl, setGitUrl] = useState('');

  // Progress report
  const [prReq, setPrReq] = useState(0);
  const [prDes, setPrDes] = useState(0);
  const [prImp, setPrImp] = useState(0);
  const [prTest, setPrTest] = useState(0);
  const [prDoc, setPrDoc] = useState(0);
  const [prNotes, setPrNotes] = useState('');

  // Submission
  const [subKind, setSubKind] = useState<'github' | 'zip' | 'source' | 'release_package'>('github');
  const [subCommit, setSubCommit] = useState('');
  const [subNotes, setSubNotes] = useState('');
  const [subFile, setSubFile] = useState<File | null>(null);

  // Evaluation form (Faculty)
  const [evalStage, setEvalStage] = useState<'review' | 'final'>('review');
  const [evalScores, setEvalScores] = useState<Record<string, number>>({});
  const [evalFeedback, setEvalFeedback] = useState('');

  // Release Request
  const [relCode, setRelCode] = useState('REL-1.0.0');
  const [relVersion, setRelVersion] = useState('1.0.0');
  const [relBaselineId, setRelBaselineId] = useState('');
  const [relCommitSha, setRelCommitSha] = useState('');
  const [relNotes, setRelNotes] = useState('');

  // Mutation Helper
  const refreshAll = () => {
    queryClient.invalidateQueries({ queryKey: ['team', id] });
    queryClient.invalidateQueries({ queryKey: ['proposals', id] });
    queryClient.invalidateQueries({ queryKey: ['cis', id] });
    queryClient.invalidateQueries({ queryKey: ['baselines', id] });
    queryClient.invalidateQueries({ queryKey: ['change-requests', id] });
    queryClient.invalidateQueries({ queryKey: ['repository', id] });
    queryClient.invalidateQueries({ queryKey: ['progress', id] });
    queryClient.invalidateQueries({ queryKey: ['submissions', id] });
    queryClient.invalidateQueries({ queryKey: ['evaluations', id] });
    queryClient.invalidateQueries({ queryKey: ['releases', id] });
    queryClient.invalidateQueries({ queryKey: ['status-accounting', id] });
    queryClient.invalidateQueries({ queryKey: ['audit-report', id] });
    queryClient.invalidateQueries({ queryKey: ['timeline', id] });
  };

  if (teamLoading) return <div>Loading...</div>;
  if (!team) return <div>Team not found.</div>;

  return (
    <div>
      <Breadcrumbs
        items={[
          { label: 'Dashboard', to: '/' },
          { label: team.project_name || 'Project', to: `/projects/${team.project_id}` },
          { label: `Team ${team.number} (${team.title})` },
        ]}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div>
          <h1>Team {team.number}: {team.title}</h1>
          <p style={{ color: 'var(--muted-text)', fontSize: '13px' }}>
            Project: <Link to={`/projects/${team.project_id}`}>{team.project_name}</Link> | Members: {team.member_count}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <StatusBadge status={team.status} />
          {team.is_delayed && (
            <StatusBadge status="delayed" />
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs-bar">
        <button type="button" className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>
          Overview
        </button>
        <button type="button" className={`tab-btn ${activeTab === 'proposal' ? 'active' : ''}`} onClick={() => setActiveTab('proposal')}>
          Proposal
        </button>
        <button type="button" className={`tab-btn ${activeTab === 'cis' ? 'active' : ''}`} onClick={() => setActiveTab('cis')}>
          Configuration Items ({cis?.length || 0})
        </button>
        <button type="button" className={`tab-btn ${activeTab === 'versions' ? 'active' : ''}`} onClick={() => setActiveTab('versions')}>
          Version History
        </button>
        <button type="button" className={`tab-btn ${activeTab === 'baselines' ? 'active' : ''}`} onClick={() => setActiveTab('baselines')}>
          Baselines ({baselines?.length || 0})
        </button>
        <button type="button" className={`tab-btn ${activeTab === 'change_requests' ? 'active' : ''}`} onClick={() => setActiveTab('change_requests')}>
          Change Requests ({changeRequests?.length || 0})
        </button>
        <button type="button" className={`tab-btn ${activeTab === 'git' ? 'active' : ''}`} onClick={() => setActiveTab('git')}>
          Git Repository
        </button>
        <button type="button" className={`tab-btn ${activeTab === 'progress' ? 'active' : ''}`} onClick={() => setActiveTab('progress')}>
          Progress
        </button>
        <button type="button" className={`tab-btn ${activeTab === 'submissions' ? 'active' : ''}`} onClick={() => setActiveTab('submissions')}>
          Submissions
        </button>
        <button type="button" className={`tab-btn ${activeTab === 'evaluation' ? 'active' : ''}`} onClick={() => setActiveTab('evaluation')}>
          Evaluation
        </button>
        <button type="button" className={`tab-btn ${activeTab === 'releases' ? 'active' : ''}`} onClick={() => setActiveTab('releases')}>
          Releases
        </button>
        <button type="button" className={`tab-btn ${activeTab === 'status_accounting' ? 'active' : ''}`} onClick={() => setActiveTab('status_accounting')}>
          Status Accounting
        </button>
        <button type="button" className={`tab-btn ${activeTab === 'audit_report' ? 'active' : ''}`} onClick={() => setActiveTab('audit_report')}>
          Audit Report
        </button>
        <button type="button" className={`tab-btn ${activeTab === 'timeline' ? 'active' : ''}`} onClick={() => setActiveTab('timeline')}>
          Timeline
        </button>
      </div>

      {/* 1. OVERVIEW */}
      {activeTab === 'overview' && (
        <div>
          <div className="panel" style={{ maxWidth: '640px' }}>
            <h2>Team Information</h2>
            <div className="desc-list">
              <span className="desc-label">Team Number:</span>
              <span className="desc-value">Team {team.number}</span>

              <span className="desc-label">Lifecycle Status:</span>
              <span className="desc-value"><StatusBadge status={team.status} /></span>

              <span className="desc-label">Formed By:</span>
              <span className="desc-value">{team.formed_by}</span>

              <span className="desc-label">Overall Progress:</span>
              <span className="desc-value">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <progress value={team.overall_progress || 0} max={100} style={{ width: '140px' }} />
                  <span>{Math.round(team.overall_progress || 0)}%</span>
                </div>
              </span>
            </div>

            {/* Faculty Manual Lifecycle Transition Control */}
            {role === 'FACULTY' && (
              <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
                <h3>Move Lifecycle Stage (Faculty Control)</h3>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '6px' }}>
                  <select
                    id="stage-select"
                    defaultValue={team.status}
                    onChange={async (e) => {
                      const nextStage = e.target.value;
                      if (nextStage !== team.status) {
                        try {
                          await apiRequest(`/teams/${team.id}/status`, {
                            method: 'POST',
                            body: { target_status: nextStage },
                          });
                          refreshAll();
                        } catch (err: any) {
                          alert(err.message || 'Status transition failed.');
                        }
                      }
                    }}
                  >
                    <option value="Development">Development</option>
                    <option value="Review 1">Review 1</option>
                    <option value="Review 2">Review 2</option>
                    <option value="Testing">Testing</option>
                    <option value="Final Submission">Final Submission</option>
                    <option value="Final Review">Final Review</option>
                    <option value="Released">Released</option>
                    <option value="Completed">Completed</option>
                    <option value="On Hold">On Hold</option>
                    <option value="Cancelled">Cancelled</option>
                  </select>
                </div>
              </div>
            )}
          </div>

          <div className="panel">
            <h2>Team Members</h2>
            <table>
              <thead>
                <tr>
                  <th>Role</th>
                  <th>Student Name</th>
                  <th>Register Number</th>
                  <th>Email</th>
                  <th>Department</th>
                  <th>Joined Date</th>
                </tr>
              </thead>
              <tbody>
                {team.members.map((m: any) => (
                  <tr key={m.id}>
                    <td><strong>{m.role.toUpperCase()}</strong></td>
                    <td>{m.student_name}</td>
                    <td>{m.student_register_number}</td>
                    <td>{m.student_email}</td>
                    <td>{m.department || '-'}</td>
                    <td>{new Date(m.joined_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 2. PROPOSAL */}
      {activeTab === 'proposal' && (
        <div>
          {/* Submit Proposal Form if eligible */}
          {(!proposals || proposals.length === 0 || proposals[0].status === 'revision_required') && (
            <div className="panel" style={{ maxWidth: '640px' }}>
              <h2>Submit Project Proposal {proposals && proposals.length > 0 ? `(Revision ${proposals[0].revision_no + 1})` : ''}</h2>
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  try {
                    await apiRequest(`/teams/${team.id}/proposals`, {
                      method: 'POST',
                      body: {
                        title: propTitle.trim(),
                        abstract: propAbstract.trim(),
                        problem_statement: propProblem.trim(),
                        objectives: propObjectives.trim(),
                        expected_outcome: propOutcome.trim(),
                        theme_id: propThemeId || undefined,
                      },
                    });
                    refreshAll();
                  } catch (err: any) {
                    alert(err.message || 'Failed to submit proposal.');
                  }
                }}
              >
                <div className="form-group">
                  <label htmlFor="prop-title">Proposal Title</label>
                  <input id="prop-title" type="text" required value={propTitle} onChange={(e) => setPropTitle(e.target.value)} />
                </div>

                {project?.themes && project.themes.length > 0 && (
                  <div className="form-group">
                    <label htmlFor="prop-theme">Select Theme (Optional)</label>
                    <select id="prop-theme" value={propThemeId} onChange={(e) => setPropThemeId(e.target.value)}>
                      <option value="">-- Select Theme --</option>
                      {project.themes.map((t: any) => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="prop-abs">Abstract</label>
                  <textarea id="prop-abs" rows={3} required value={propAbstract} onChange={(e) => setPropAbstract(e.target.value)} />
                </div>

                <div className="form-group">
                  <label htmlFor="prop-prob">Problem Statement</label>
                  <textarea id="prop-prob" rows={3} required value={propProblem} onChange={(e) => setPropProblem(e.target.value)} />
                </div>

                <div className="form-group">
                  <label htmlFor="prop-obj">Objectives</label>
                  <textarea id="prop-obj" rows={3} required value={propObjectives} onChange={(e) => setPropObjectives(e.target.value)} />
                </div>

                <div className="form-group">
                  <label htmlFor="prop-out">Expected Outcome</label>
                  <textarea id="prop-out" rows={2} required value={propOutcome} onChange={(e) => setPropOutcome(e.target.value)} />
                </div>

                <button type="submit" className="primary">Submit Proposal</button>
              </form>
            </div>
          )}

          {/* Proposal Revisions History */}
          <div className="panel">
            <h2>Proposal History</h2>
            {!proposals || proposals.length === 0 ? (
              <p style={{ color: 'var(--muted-text)' }}>No proposal submitted yet.</p>
            ) : (
              proposals.map((p) => (
                <div key={p.id} style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '16px', marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <h3>Revision {p.revision_no}: {p.title}</h3>
                    <StatusBadge status={p.status} />
                  </div>
                  <div className="desc-list">
                    <span className="desc-label">Theme:</span>
                    <span className="desc-value">{p.theme_name || 'None'}</span>

                    <span className="desc-label">Submitted By:</span>
                    <span className="desc-value">{p.submitted_by_name} on {new Date(p.created_at).toLocaleString()}</span>

                    <span className="desc-label">Abstract:</span>
                    <span className="desc-value">{p.abstract}</span>

                    <span className="desc-label">Problem Statement:</span>
                    <span className="desc-value">{p.problem_statement}</span>

                    <span className="desc-label">Objectives:</span>
                    <span className="desc-value">{p.objectives}</span>

                    <span className="desc-label">Expected Outcome:</span>
                    <span className="desc-value">{p.expected_outcome}</span>

                    {p.faculty_feedback && (
                      <>
                        <span className="desc-label" style={{ color: 'var(--accent-color)' }}>Faculty Feedback:</span>
                        <span className="desc-value" style={{ fontWeight: '500' }}>{p.faculty_feedback}</span>
                      </>
                    )}
                  </div>

                  {/* Faculty Decision Controls */}
                  {role === 'FACULTY' && p.status === 'submitted' && (
                    <div style={{ marginTop: '12px', background: '#fafaf6', padding: '10px', border: '1px solid var(--border-color)' }}>
                      <h4>Faculty Review Decision</h4>
                      <div className="form-group" style={{ margin: '8px 0' }}>
                        <label htmlFor={`fb-${p.id}`}>Feedback / Reason (Required for rejection or modification)</label>
                        <input
                          id={`fb-${p.id}`}
                          type="text"
                          value={propFeedback}
                          onChange={(e) => setPropFeedback(e.target.value)}
                          placeholder="Provide specific constructive feedback"
                        />
                      </div>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          type="button"
                          className="primary"
                          onClick={async () => {
                            try {
                              await apiRequest(`/proposals/${p.id}/decision`, {
                                method: 'POST',
                                body: { decision: 'approved', feedback: propFeedback || undefined },
                              });
                              refreshAll();
                            } catch (err: any) {
                              alert(err.message || 'Failed.');
                            }
                          }}
                        >
                          Approve Proposal
                        </button>
                        <button
                          type="button"
                          onClick={async () => {
                            if (!propFeedback.trim()) {
                              alert('Feedback is required when requesting modifications.');
                              return;
                            }
                            try {
                              await apiRequest(`/proposals/${p.id}/decision`, {
                                method: 'POST',
                                body: { decision: 'revision_required', feedback: propFeedback.trim() },
                              });
                              refreshAll();
                            } catch (err: any) {
                              alert(err.message || 'Failed.');
                            }
                          }}
                        >
                          Request Modification
                        </button>
                        <button
                          type="button"
                          className="danger"
                          onClick={async () => {
                            if (!propFeedback.trim()) {
                              alert('Feedback is required when rejecting a proposal.');
                              return;
                            }
                            try {
                              await apiRequest(`/proposals/${p.id}/decision`, {
                                method: 'POST',
                                body: { decision: 'rejected', feedback: propFeedback.trim() },
                              });
                              refreshAll();
                            } catch (err: any) {
                              alert(err.message || 'Failed.');
                            }
                          }}
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* 3. CONFIGURATION ITEMS */}
      {activeTab === 'cis' && (
        <div>
          <div className="panel" style={{ maxWidth: '560px' }}>
            <h2>Create Configuration Item (CI)</h2>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                try {
                  await apiRequest(`/teams/${team.id}/cis`, {
                    method: 'POST',
                    body: { name: newCiName.trim(), ci_type: newCiType },
                  });
                  setNewCiName('');
                  refreshAll();
                } catch (err: any) {
                  alert(err.message || 'Failed to create CI.');
                }
              }}
            >
              <div className="form-row">
                <div className="form-group" style={{ flex: '2' }}>
                  <label htmlFor="ci-name">CI Name</label>
                  <input id="ci-name" type="text" required value={newCiName} onChange={(e) => setNewCiName(e.target.value)} placeholder="e.g. Database Schema" />
                </div>
                <div className="form-group" style={{ flex: '1' }}>
                  <label htmlFor="ci-type">CI Type</label>
                  <select id="ci-type" value={newCiType} onChange={(e) => setNewCiType(e.target.value)}>
                    <option value="requirements">Requirements</option>
                    <option value="srs">SRS</option>
                    <option value="architecture">Architecture</option>
                    <option value="database_design">Database Design</option>
                    <option value="backend">Backend</option>
                    <option value="frontend">Frontend</option>
                    <option value="test_cases">Test Cases</option>
                    <option value="test_report">Test Report</option>
                    <option value="documentation">Documentation</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>
              <button type="submit" className="primary">Add CI</button>
            </form>
          </div>

          <div className="panel">
            <h2>Configuration Items Inventory</h2>
            {!cis || cis.length === 0 ? (
              <p style={{ color: 'var(--muted-text)' }}>No configuration items registered yet.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>CI Code</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Latest Version</th>
                    <th>Approved Version</th>
                    <th>State</th>
                    <th>Baselines</th>
                  </tr>
                </thead>
                <tbody>
                  {cis.map((ci) => (
                    <tr key={ci.id}>
                      <td><strong>{ci.ci_code}</strong></td>
                      <td>{ci.name}</td>
                      <td>{ci.ci_type}</td>
                      <td>{ci.latest_version ? `v${ci.latest_version.version_label} (${ci.latest_version.status})` : 'None'}</td>
                      <td>{ci.latest_approved_version ? `v${ci.latest_approved_version.version_label}` : 'None'}</td>
                      <td><StatusBadge status={ci.status} isLocked={ci.is_locked} /></td>
                      <td>{ci.baseline_codes?.join(', ') || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* 4. VERSION HISTORY */}
      {activeTab === 'versions' && (
        <div>
          {/* Upload New Version Form */}
          <div className="panel" style={{ maxWidth: '560px' }}>
            <h2>Upload New CI Version</h2>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                if (!uploadCiId || !uploadFile) {
                  alert('Please select a CI and a file.');
                  return;
                }
                const formData = new FormData();
                formData.append('file', uploadFile);
                formData.append('change_description', uploadDesc.trim());
                formData.append('bump_type', uploadBump);
                if (uploadCommitSha.trim()) formData.append('commit_sha', uploadCommitSha.trim());
                if (uploadCrId) formData.append('change_request_id', uploadCrId);

                try {
                  await apiRequest(`/cis/${uploadCiId}/versions`, {
                    method: 'POST',
                    body: formData,
                  });
                  setUploadFile(null);
                  setUploadDesc('');
                  setUploadCommitSha('');
                  setUploadCrId('');
                  refreshAll();
                  alert('Version uploaded successfully.');
                } catch (err: any) {
                  alert(err.message || 'Upload failed.');
                }
              }}
            >
              <div className="form-group">
                <label htmlFor="upload-ci">Target Configuration Item</label>
                <select id="upload-ci" required value={uploadCiId} onChange={(e) => setUploadCiId(e.target.value)}>
                  <option value="">-- Select CI --</option>
                  {cis?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.ci_code}: {c.name} {c.is_locked ? '(LOCKED)' : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group" style={{ flex: '1' }}>
                  <label htmlFor="upload-file">Select Artifact File</label>
                  <input
                    id="upload-file"
                    type="file"
                    required
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  />
                </div>
                <div className="form-group" style={{ flex: '1' }}>
                  <label htmlFor="upload-bump">Version Increment</label>
                  <select id="upload-bump" value={uploadBump} onChange={(e) => setUploadBump(e.target.value as any)}>
                    <option value="minor">Minor bump (e.g. 1.0 -&gt; 1.1)</option>
                    <option value="major">Major bump (e.g. 1.0 -&gt; 2.0)</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="upload-desc">Change Description / Rationale</label>
                <textarea id="upload-desc" rows={2} required value={uploadDesc} onChange={(e) => setUploadDesc(e.target.value)} />
              </div>

              <div className="form-group">
                <label htmlFor="upload-commit">Git Commit SHA (Optional)</label>
                <input id="upload-commit" type="text" value={uploadCommitSha} onChange={(e) => setUploadCommitSha(e.target.value)} placeholder="e.g. a1b2c3d" />
              </div>

              {/* CR Selector if CI is locked */}
              <div className="form-group">
                <label htmlFor="upload-cr">Linked Approved Change Request (Mandatory if CI is locked)</label>
                <select id="upload-cr" value={uploadCrId} onChange={(e) => setUploadCrId(e.target.value)}>
                  <option value="">-- None / Direct Upload --</option>
                  {changeRequests
                    ?.filter((cr) => cr.status === 'approved' || cr.status === 'implemented')
                    .map((cr) => (
                      <option key={cr.id} value={cr.id}>
                        {cr.cr_code}: {cr.title} ({cr.status})
                      </option>
                    ))}
                </select>
              </div>

              <button type="submit" className="primary">Upload Version</button>
            </form>
          </div>

          {/* Rollback Section */}
          <div className="panel" style={{ maxWidth: '560px' }}>
            <h2>Rollback Configuration Item</h2>
            <p style={{ fontSize: '12px', color: 'var(--muted-text)', marginBottom: '8px' }}>
              Rollback never deletes history. It creates a new immutable version reusing the target version's contents and records the rollback reference.
            </p>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                if (!uploadCiId || !rollbackTargetId || !rollbackReason) {
                  alert('Please select CI, target version, and reason.');
                  return;
                }
                try {
                  await apiRequest(`/cis/${uploadCiId}/rollback`, {
                    method: 'POST',
                    body: {
                      target_version_id: rollbackTargetId,
                      reason: rollbackReason.trim(),
                      change_request_id: rollbackCrId || undefined,
                    },
                  });
                  setRollbackReason('');
                  setRollbackTargetId('');
                  refreshAll();
                  alert('Rollback executed successfully.');
                } catch (err: any) {
                  alert(err.message || 'Rollback failed.');
                }
              }}
            >
              <div className="form-group">
                <label htmlFor="rb-ci">Select CI</label>
                <select id="rb-ci" value={uploadCiId} onChange={(e) => setUploadCiId(e.target.value)}>
                  <option value="">-- Select CI --</option>
                  {cis?.map((c) => (
                    <option key={c.id} value={c.id}>{c.ci_code}: {c.name}</option>
                  ))}
                </select>
              </div>

              {uploadCiId && (
                <div className="form-group">
                  <label htmlFor="rb-target">Rollback to Version</label>
                  <select id="rb-target" value={rollbackTargetId} onChange={(e) => setRollbackTargetId(e.target.value)}>
                    <option value="">-- Select Target Version --</option>
                    {cis
                      ?.find((c) => c.id === uploadCiId)
                      ?.versions?.map((v: any) => (
                        <option key={v.id} value={v.id}>
                          v{v.version_label} ({v.change_description})
                        </option>
                      ))}
                  </select>
                </div>
              )}

              <div className="form-group">
                <label htmlFor="rb-reason">Rollback Reason</label>
                <input id="rb-reason" type="text" value={rollbackReason} onChange={(e) => setRollbackReason(e.target.value)} placeholder="Reason for rollback" />
              </div>

              <div className="form-group">
                <label htmlFor="rb-cr">Change Request (If CI is locked)</label>
                <select id="rb-cr" value={rollbackCrId} onChange={(e) => setRollbackCrId(e.target.value)}>
                  <option value="">-- None --</option>
                  {changeRequests
                    ?.filter((cr) => cr.status === 'approved' || cr.status === 'implemented')
                    .map((cr) => (
                      <option key={cr.id} value={cr.id}>{cr.cr_code}: {cr.title}</option>
                    ))}
                </select>
              </div>

              <button type="submit">Execute Rollback</button>
            </form>
          </div>

          {/* All Versions Table */}
          <div className="panel">
            <h2>Version History & Actions</h2>
            {!cis || cis.length === 0 ? (
              <p style={{ color: 'var(--muted-text)' }}>No CIs available.</p>
            ) : (
              cis.map((ci) => (
                <div key={ci.id} style={{ marginBottom: '24px' }}>
                  <h3>{ci.ci_code}: {ci.name} ({ci.ci_type}) {ci.is_locked && <span className="status-badge locked">LOCKED</span>}</h3>
                  {ci.versions.length === 0 ? (
                    <p style={{ color: 'var(--muted-text)', fontSize: '13px' }}>No versions uploaded yet.</p>
                  ) : (
                    <table>
                      <thead>
                        <tr>
                          <th>Version</th>
                          <th>Kind</th>
                          <th>File Name</th>
                          <th>SHA-256</th>
                          <th>Uploaded By</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ci.versions.map((v: any) => (
                          <tr key={v.id}>
                            <td><strong>v{v.version_label}</strong></td>
                            <td>{v.kind}</td>
                            <td>{v.original_file_name}</td>
                            <td><code>{v.content_sha256.substring(0, 10)}...</code></td>
                            <td>{v.created_by_name} ({new Date(v.created_at).toLocaleDateString()})</td>
                            <td><StatusBadge status={v.status} /></td>
                            <td>
                              <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                                <a href={`/api/v1/versions/${v.id}/download`} target="_blank" rel="noreferrer">
                                  Download
                                </a>

                                {v.status === 'draft' && (
                                  <button
                                    type="button"
                                    onClick={async () => {
                                      try {
                                        await apiRequest(`/versions/${v.id}/submit`, { method: 'POST' });
                                        refreshAll();
                                      } catch (err: any) {
                                        alert(err.message || 'Submit failed.');
                                      }
                                    }}
                                  >
                                    Submit
                                  </button>
                                )}

                                {role === 'FACULTY' && v.status === 'submitted' && (
                                  <>
                                    <button
                                      type="button"
                                      className="primary"
                                      onClick={async () => {
                                        try {
                                          await apiRequest(`/versions/${v.id}/decision`, {
                                            method: 'POST',
                                            body: { decision: 'approved' },
                                          });
                                          refreshAll();
                                        } catch (err: any) {
                                          alert(err.message || 'Decision failed.');
                                        }
                                      }}
                                    >
                                      Approve
                                    </button>
                                    <button
                                      type="button"
                                      className="danger"
                                      onClick={async () => {
                                        try {
                                          await apiRequest(`/versions/${v.id}/decision`, {
                                            method: 'POST',
                                            body: { decision: 'rejected' },
                                          });
                                          refreshAll();
                                        } catch (err: any) {
                                          alert(err.message || 'Decision failed.');
                                        }
                                      }}
                                    >
                                      Reject
                                    </button>
                                  </>
                                )}

                                {ci.versions.length > 1 && (
                                  <Link to={`/cis/${ci.id}/compare?from=${ci.versions[ci.versions.length - 1].id}&to=${v.id}`}>
                                    Compare
                                  </Link>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* 5. BASELINES */}
      {activeTab === 'baselines' && (
        <div>
          {/* Create Baseline Form */}
          <div className="panel" style={{ maxWidth: '560px' }}>
            <h2>{role === 'FACULTY' ? 'Create & Lock Baseline' : 'Propose Baseline'}</h2>
            <p style={{ fontSize: '12px', color: 'var(--muted-text)', marginBottom: '8px' }}>
              Only approved versions can be baselined. Locking a baseline freezes its constituent CIs against unapproved modifications.
            </p>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                if (blVersionIds.length === 0) {
                  alert('Select at least one approved CI version.');
                  return;
                }
                try {
                  await apiRequest(`/teams/${team.id}/baselines`, {
                    method: 'POST',
                    body: {
                      name: blName.trim(),
                      description: blDesc.trim() || undefined,
                      ci_version_ids: blVersionIds,
                    },
                  });
                  setBlName('');
                  setBlDesc('');
                  setBlVersionIds([]);
                  refreshAll();
                  alert('Baseline created.');
                } catch (err: any) {
                  alert(err.message || 'Failed to create baseline.');
                }
              }}
            >
              <div className="form-group">
                <label htmlFor="bl-name">Baseline Name</label>
                <input id="bl-name" type="text" required value={blName} onChange={(e) => setBlName(e.target.value)} placeholder="e.g. Review 1 Baseline" />
              </div>

              <div className="form-group">
                <label htmlFor="bl-desc">Description</label>
                <textarea id="bl-desc" rows={2} value={blDesc} onChange={(e) => setBlDesc(e.target.value)} />
              </div>

              <div className="form-group">
                <label>Select Approved Versions to Include</label>
                <div style={{ maxHeight: '140px', overflowY: 'auto', border: '1px solid var(--border-color)', padding: '6px' }}>
                  {cis?.flatMap((c) =>
                    c.versions
                      .filter((v: any) => v.status === 'approved')
                      .map((v: any) => (
                        <label key={v.id} style={{ display: 'block', fontSize: '13px', margin: '3px 0' }}>
                          <input
                            type="checkbox"
                            checked={blVersionIds.includes(v.id)}
                            onChange={(e) => {
                              if (e.target.checked) setBlVersionIds([...blVersionIds, v.id]);
                              else setBlVersionIds(blVersionIds.filter((id) => id !== v.id));
                            }}
                          />{' '}
                          <strong>{c.ci_code}</strong>: {c.name} (v{v.version_label})
                        </label>
                      ))
                  )}
                </div>
              </div>

              <button type="submit" className="primary">
                {role === 'FACULTY' ? 'Create & Lock Baseline' : 'Propose Baseline'}
              </button>
            </form>
          </div>

          <div className="panel">
            <h2>Baselines List</h2>
            {!baselines || baselines.length === 0 ? (
              <p style={{ color: 'var(--muted-text)' }}>No baselines established yet.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Baseline Code</th>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Locked Date</th>
                    <th>Items Included</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {baselines.map((bl) => (
                    <tr key={bl.id}>
                      <td><strong>{bl.code}</strong></td>
                      <td>{bl.name}</td>
                      <td><StatusBadge status={bl.status} /></td>
                      <td>{bl.locked_at ? new Date(bl.locked_at).toLocaleString() : 'Not locked'}</td>
                      <td>
                        {bl.items.map((it: any) => (
                          <div key={it.id} style={{ fontSize: '12px' }}>
                            v{it.version_label} ({it.original_file_name})
                          </div>
                        ))}
                      </td>
                      <td>
                        {role === 'FACULTY' && bl.status === 'proposed' && (
                          <button
                            type="button"
                            className="primary"
                            onClick={async () => {
                              try {
                                await apiRequest(`/baselines/${bl.id}/approve`, { method: 'POST' });
                                refreshAll();
                              } catch (err: any) {
                                alert(err.message || 'Failed to approve baseline.');
                              }
                            }}
                          >
                            Approve & Lock
                          </button>
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

      {/* 6. CHANGE REQUESTS */}
      {activeTab === 'change_requests' && (
        <div>
          <div className="panel" style={{ maxWidth: '640px' }}>
            <h2>Submit Change Request (CR)</h2>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                try {
                  await apiRequest(`/teams/${team.id}/change-requests`, {
                    method: 'POST',
                    body: {
                      title: crTitle.trim(),
                      description: crDesc.trim(),
                      reason: crReason.trim(),
                      priority: crPriority,
                      affected_ci_ids: crAffectedCis,
                      components: crComponents,
                    },
                  });
                  setCrTitle('');
                  setCrDesc('');
                  setCrReason('');
                  setCrAffectedCis([]);
                  setCrComponents([]);
                  refreshAll();
                  alert('Change request created.');
                } catch (err: any) {
                  alert(err.message || 'Failed to create CR.');
                }
              }}
            >
              <div className="form-group">
                <label htmlFor="cr-title">Title</label>
                <input id="cr-title" type="text" required value={crTitle} onChange={(e) => setCrTitle(e.target.value)} placeholder="e.g. Modify User Authentication Flow" />
              </div>

              <div className="form-row">
                <div className="form-group" style={{ flex: '1' }}>
                  <label htmlFor="cr-prio">Priority</label>
                  <select id="cr-prio" value={crPriority} onChange={(e) => setCrPriority(e.target.value as any)}>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="cr-desc">Description of Change</label>
                <textarea id="cr-desc" rows={2} required value={crDesc} onChange={(e) => setCrDesc(e.target.value)} />
              </div>

              <div className="form-group">
                <label htmlFor="cr-reason">Reason / Justification</label>
                <textarea id="cr-reason" rows={2} required value={crReason} onChange={(e) => setCrReason(e.target.value)} />
              </div>

              <div className="form-group">
                <label>Affected Components (Tick all that apply)</label>
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                  {['backend', 'database', 'frontend', 'test_cases', 'documentation', 'other'].map((c) => (
                    <label key={c} style={{ fontSize: '13px' }}>
                      <input
                        type="checkbox"
                        checked={crComponents.includes(c)}
                        onChange={(e) => {
                          if (e.target.checked) setCrComponents([...crComponents, c]);
                          else setCrComponents(crComponents.filter((x) => x !== c));
                        }}
                      />{' '}
                      {c.replace('_', ' ').toUpperCase()}
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label>Directly Affected Configuration Items</label>
                <div style={{ maxHeight: '120px', overflowY: 'auto', border: '1px solid var(--border-color)', padding: '6px' }}>
                  {cis?.map((c) => (
                    <label key={c.id} style={{ display: 'block', fontSize: '13px' }}>
                      <input
                        type="checkbox"
                        checked={crAffectedCis.includes(c.id)}
                        onChange={(e) => {
                          if (e.target.checked) setCrAffectedCis([...crAffectedCis, c.id]);
                          else setCrAffectedCis(crAffectedCis.filter((x) => x !== c.id));
                        }}
                      />{' '}
                      {c.ci_code}: {c.name} {c.is_locked ? '(LOCKED)' : ''}
                    </label>
                  ))}
                </div>
              </div>

              <button type="submit" className="primary">Create Change Request</button>
            </form>
          </div>

          <div className="panel">
            <h2>Change Requests Log</h2>
            {!changeRequests || changeRequests.length === 0 ? (
              <p style={{ color: 'var(--muted-text)' }}>No change requests yet.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>CR Code</th>
                    <th>Title</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Components</th>
                    <th>Created By</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {changeRequests.map((cr) => (
                    <tr key={cr.id}>
                      <td><strong>{cr.cr_code}</strong></td>
                      <td>
                        <Link to={`/change-requests/${cr.id}`}>{cr.title}</Link>
                      </td>
                      <td>{cr.priority.toUpperCase()}</td>
                      <td><StatusBadge status={cr.status} /></td>
                      <td>{cr.components?.join(', ') || '-'}</td>
                      <td>{cr.created_by_name}</td>
                      <td>
                        <Link to={`/change-requests/${cr.id}`}>View & Transition</Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* 7. GIT REPOSITORY */}
      {activeTab === 'git' && (
        <div>
          <div className="panel" style={{ maxWidth: '560px' }}>
            <h2>Link GitHub Repository</h2>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                try {
                  await apiRequest(`/teams/${team.id}/repository`, {
                    method: 'PUT',
                    body: { url: gitUrl.trim() },
                  });
                  setGitUrl('');
                  refetchRepo();
                } catch (err: any) {
                  alert(err.message || 'Failed to link repository.');
                }
              }}
            >
              <div className="form-group">
                <label htmlFor="repo-url-input">GitHub Repository URL</label>
                <input
                  id="repo-url-input"
                  type="text"
                  required
                  value={gitUrl}
                  onChange={(e) => setGitUrl(e.target.value)}
                  placeholder="https://github.com/owner/repository"
                />
              </div>
              <button type="submit" className="primary">Save & Sync</button>
            </form>
          </div>

          {repository && (
            <div className="panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2>Linked Repository: {repository.owner}/{repository.name}</h2>
                <button
                  type="button"
                  onClick={async () => {
                    try {
                      await apiRequest(`/teams/${team.id}/repository/sync`, { method: 'POST' });
                      refetchRepo();
                    } catch (err: any) {
                      alert(err.message || 'Sync failed.');
                    }
                  }}
                >
                  Sync Now
                </button>
              </div>

              <div className="desc-list" style={{ margin: '10px 0' }}>
                <span className="desc-label">Default Branch:</span>
                <span className="desc-value">{repository.default_branch}</span>

                <span className="desc-label">Last Synced:</span>
                <span className="desc-value">{repository.last_synced_at ? new Date(repository.last_synced_at).toLocaleString() : 'Never'}</span>

                {repository.last_sync_error && (
                  <>
                    <span className="desc-label" style={{ color: 'var(--danger-color)' }}>Sync Error:</span>
                    <span className="desc-value" style={{ color: 'var(--danger-color)' }}>{repository.last_sync_error}</span>
                  </>
                )}
              </div>

              <h3>Branches</h3>
              <table>
                <thead>
                  <tr>
                    <th>Branch Name</th>
                    <th>Head SHA</th>
                    <th>Policy Check</th>
                  </tr>
                </thead>
                <tbody>
                  {repository.branches?.map((b: any) => (
                    <tr key={b.id}>
                      <td><strong>{b.name}</strong></td>
                      <td><code>{b.head_sha.substring(0, 7)}</code></td>
                      <td>
                        {b.follows_policy ? (
                          <span style={{ color: 'var(--success-color)' }}>OK</span>
                        ) : (
                          <span style={{ color: 'var(--danger-color)', fontWeight: 'bold' }}>Violates GitFlow Lite policy</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <h3>Recent Commits</h3>
              <table>
                <thead>
                  <tr>
                    <th>SHA</th>
                    <th>Author</th>
                    <th>Message</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {repository.commits?.map((c: any) => (
                    <tr key={c.id}>
                      <td>
                        <a href={`${repository.url}/commit/${c.sha}`} target="_blank" rel="noreferrer">
                          <code>{c.sha.substring(0, 7)}</code>
                        </a>
                      </td>
                      <td>{c.author_name}</td>
                      <td>{c.message}</td>
                      <td>{new Date(c.committed_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* 8. PROGRESS */}
      {activeTab === 'progress' && (
        <div>
          <div className="panel" style={{ maxWidth: '560px' }}>
            <h2>Submit Progress Report</h2>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                try {
                  await apiRequest(`/teams/${team.id}/progress`, {
                    method: 'POST',
                    body: {
                      requirements_pct: Number(prReq),
                      design_pct: Number(prDes),
                      implementation_pct: Number(prImp),
                      testing_pct: Number(prTest),
                      documentation_pct: Number(prDoc),
                      notes: prNotes.trim(),
                    },
                  });
                  setPrNotes('');
                  refreshAll();
                  alert('Progress report submitted.');
                } catch (err: any) {
                  alert(err.message || 'Failed to submit progress.');
                }
              }}
            >
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="pr-req">Requirements (%)</label>
                  <input id="pr-req" type="number" min={0} max={100} value={prReq} onChange={(e) => setPrReq(Number(e.target.value))} />
                </div>
                <div className="form-group">
                  <label htmlFor="pr-des">Design (%)</label>
                  <input id="pr-des" type="number" min={0} max={100} value={prDes} onChange={(e) => setPrDes(Number(e.target.value))} />
                </div>
                <div className="form-group">
                  <label htmlFor="pr-imp">Implementation (%)</label>
                  <input id="pr-imp" type="number" min={0} max={100} value={prImp} onChange={(e) => setPrImp(Number(e.target.value))} />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="pr-test">Testing (%)</label>
                  <input id="pr-test" type="number" min={0} max={100} value={prTest} onChange={(e) => setPrTest(Number(e.target.value))} />
                </div>
                <div className="form-group">
                  <label htmlFor="pr-doc">Documentation (%)</label>
                  <input id="pr-doc" type="number" min={0} max={100} value={prDoc} onChange={(e) => setPrDoc(Number(e.target.value))} />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="pr-notes">Weekly Progress Notes</label>
                <textarea id="pr-notes" rows={3} required value={prNotes} onChange={(e) => setPrNotes(e.target.value)} placeholder="Summary of work completed and milestones achieved." />
              </div>

              <button type="submit" className="primary">Submit Report</button>
            </form>
          </div>

          <div className="panel">
            <h2>Progress Reports History</h2>
            {!progressReports || progressReports.length === 0 ? (
              <p style={{ color: 'var(--muted-text)' }}>No progress reports submitted yet.</p>
            ) : (
              progressReports.map((pr) => (
                <div key={pr.id} style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <h3>Report #{pr.seq} - Overall: {pr.overall_progress_pct}%</h3>
                    <span style={{ fontSize: '12px', color: 'var(--muted-text)' }}>{new Date(pr.created_at).toLocaleString()}</span>
                  </div>
                  <p style={{ margin: '6px 0' }}>{pr.notes}</p>
                  <div style={{ fontSize: '12px', color: 'var(--muted-text)' }}>
                    Req: {pr.requirements_pct}% | Design: {pr.design_pct}% | Imp: {pr.implementation_pct}% | Test: {pr.testing_pct}% | Doc: {pr.documentation_pct}%
                  </div>
                  {pr.faculty_comment && (
                    <div style={{ marginTop: '6px', fontSize: '13px', color: 'var(--accent-color)' }}>
                      <strong>Faculty Feedback:</strong> {pr.faculty_comment}
                    </div>
                  )}

                  {role === 'FACULTY' && !pr.faculty_comment && (
                    <form
                      style={{ marginTop: '8px' }}
                      onSubmit={async (e) => {
                        e.preventDefault();
                        const commentInput = (e.currentTarget.elements.namedItem('fac_comment') as HTMLInputElement).value;
                        if (!commentInput.trim()) return;
                        try {
                          await apiRequest(`/progress/${pr.id}/comment`, {
                            method: 'POST',
                            body: { faculty_comment: commentInput.trim() },
                          });
                          refreshAll();
                        } catch (err: any) {
                          alert(err.message || 'Failed.');
                        }
                      }}
                    >
                      <div className="form-group">
                        <input name="fac_comment" type="text" placeholder="Add faculty feedback..." />
                      </div>
                      <button type="submit">Submit Feedback</button>
                    </form>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* 9. SUBMISSIONS */}
      {activeTab === 'submissions' && (
        <div>
          <div className="panel" style={{ maxWidth: '560px' }}>
            <h2>Make a Milestone Submission</h2>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const formData = new FormData();
                formData.append('kind', subKind);
                if (subCommit.trim()) formData.append('commit_sha', subCommit.trim());
                if (subNotes.trim()) formData.append('notes', subNotes.trim());
                if (subFile) formData.append('file', subFile);

                try {
                  await apiRequest(`/teams/${team.id}/submissions`, {
                    method: 'POST',
                    body: formData,
                  });
                  setSubCommit('');
                  setSubNotes('');
                  setSubFile(null);
                  refreshAll();
                  alert('Submission created.');
                } catch (err: any) {
                  alert(err.message || 'Submission failed.');
                }
              }}
            >
              <div className="form-group">
                <label htmlFor="sub-kind">Submission Kind</label>
                <select id="sub-kind" value={subKind} onChange={(e) => setSubKind(e.target.value as any)}>
                  <option value="github">GitHub Commit / Release</option>
                  <option value="zip">ZIP Package</option>
                  <option value="source">Source Code Bundle</option>
                  <option value="release_package">Formal Release Package</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="sub-commit">Git Commit SHA (Optional)</label>
                <input id="sub-commit" type="text" value={subCommit} onChange={(e) => setSubCommit(e.target.value)} placeholder="e.g. 9b3d1f0" />
              </div>

              <div className="form-group">
                <label htmlFor="sub-file">Upload Package / Document (Optional)</label>
                <input id="sub-file" type="file" onChange={(e) => setSubFile(e.target.files?.[0] || null)} />
              </div>

              <div className="form-group">
                <label htmlFor="sub-notes">Submission Notes</label>
                <textarea id="sub-notes" rows={2} value={subNotes} onChange={(e) => setSubNotes(e.target.value)} />
              </div>

              <button type="submit" className="primary">Submit</button>
            </form>
          </div>

          <div className="panel">
            <h2>Submissions History</h2>
            {!submissions || submissions.length === 0 ? (
              <p style={{ color: 'var(--muted-text)' }}>No submissions recorded.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Kind</th>
                    <th>Commit / File</th>
                    <th>Late Flag</th>
                    <th>Status</th>
                    <th>Submitted At</th>
                    <th>Faculty Action</th>
                  </tr>
                </thead>
                <tbody>
                  {submissions.map((s) => (
                    <tr key={s.id}>
                      <td><strong>{s.kind.toUpperCase()}</strong></td>
                      <td>
                        {s.commit_sha && <code>{s.commit_sha.substring(0, 7)} </code>}
                        {s.original_file_name}
                      </td>
                      <td>
                        {s.is_late ? (
                          <span style={{ color: 'var(--danger-color)', fontWeight: 'bold' }}>LATE</span>
                        ) : (
                          'ON TIME'
                        )}
                      </td>
                      <td><StatusBadge status={s.status} /></td>
                      <td>{new Date(s.created_at).toLocaleString()}</td>
                      <td>
                        {role === 'FACULTY' && s.status === 'submitted' && (
                          <div style={{ display: 'flex', gap: '4px' }}>
                            <button
                              type="button"
                              className="primary"
                              onClick={async () => {
                                try {
                                  await apiRequest(`/submissions/${s.id}/decision`, {
                                    method: 'POST',
                                    body: { decision: 'accepted' },
                                  });
                                  refreshAll();
                                } catch (err: any) {
                                  alert(err.message || 'Decision failed.');
                                }
                              }}
                            >
                              Accept
                            </button>
                            <button
                              type="button"
                              className="danger"
                              onClick={async () => {
                                try {
                                  await apiRequest(`/submissions/${s.id}/decision`, {
                                    method: 'POST',
                                    body: { decision: 'rejected' },
                                  });
                                  refreshAll();
                                } catch (err: any) {
                                  alert(err.message || 'Decision failed.');
                                }
                              }}
                            >
                              Reject
                            </button>
                          </div>
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

      {/* 10. EVALUATION */}
      {activeTab === 'evaluation' && (
        <div>
          {/* Faculty Record Evaluation Form */}
          {role === 'FACULTY' && (
            <div className="panel" style={{ maxWidth: '640px' }}>
              <h2>Record Team Evaluation</h2>
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  const scoresList = project?.evaluation_criteria?.map((c: any) => ({
                    criterion_id: c.id,
                    marks: Number(evalScores[c.id] || 0),
                  })) || [];

                  try {
                    await apiRequest(`/teams/${team.id}/evaluations`, {
                      method: 'POST',
                      body: {
                        stage: evalStage,
                        scores: scoresList,
                        feedback: evalFeedback.trim() || undefined,
                      },
                    });
                    setEvalFeedback('');
                    refreshAll();
                    alert('Evaluation recorded.');
                  } catch (err: any) {
                    alert(err.message || 'Failed to record evaluation.');
                  }
                }}
              >
                <div className="form-group">
                  <label htmlFor="eval-stage">Evaluation Stage</label>
                  <select id="eval-stage" value={evalStage} onChange={(e) => setEvalStage(e.target.value as any)}>
                    <option value="review">Review Evaluation</option>
                    <option value="final">Final Evaluation</option>
                  </select>
                </div>

                <h3>Criteria Scores</h3>
                {project?.evaluation_criteria?.map((crit: any) => (
                  <div key={crit.id} className="form-row" style={{ alignItems: 'center' }}>
                    <div style={{ flex: '2', fontSize: '13px' }}>
                      <strong>{crit.name}</strong> (Max: {crit.max_marks})
                    </div>
                    <div className="form-group" style={{ flex: '1', margin: 0 }}>
                      <input
                        type="number"
                        min={0}
                        max={crit.max_marks}
                        required
                        value={evalScores[crit.id] || 0}
                        onChange={(e) => setEvalScores({ ...evalScores, [crit.id]: Number(e.target.value) })}
                      />
                    </div>
                  </div>
                ))}

                <div className="form-group" style={{ marginTop: '12px' }}>
                  <label htmlFor="eval-fb">General Feedback</label>
                  <textarea id="eval-fb" rows={2} value={evalFeedback} onChange={(e) => setEvalFeedback(e.target.value)} />
                </div>

                <button type="submit" className="primary">Save Evaluation</button>
              </form>
            </div>
          )}

          <div className="panel">
            <h2>Evaluations History</h2>
            {!evaluations || evaluations.length === 0 ? (
              <p style={{ color: 'var(--muted-text)' }}>No evaluations recorded yet.</p>
            ) : (
              evaluations.map((ev) => (
                <div key={ev.id} style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '16px', marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3>{ev.stage.toUpperCase()} Evaluation: {ev.total_marks} marks (Grade {ev.grade})</h3>
                    <span style={{ fontSize: '12px', color: 'var(--muted-text)' }}>{new Date(ev.created_at).toLocaleString()}</span>
                  </div>
                  {ev.feedback && <p style={{ margin: '6px 0' }}>Feedback: {ev.feedback}</p>}

                  <table>
                    <thead>
                      <tr>
                        <th>Criterion</th>
                        <th>Max Marks</th>
                        <th>Awarded Marks</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ev.scores?.map((sc: any) => (
                        <tr key={sc.id}>
                          <td>{sc.criterion_name}</td>
                          <td>{sc.max_marks}</td>
                          <td><strong>{sc.marks}</strong></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* 11. RELEASES */}
      {activeTab === 'releases' && (
        <div>
          {/* Request Release Form */}
          <div className="panel" style={{ maxWidth: '560px' }}>
            <h2>Request Release</h2>
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                if (!relBaselineId) {
                  alert('Please select a locked baseline.');
                  return;
                }
                try {
                  await apiRequest(`/teams/${team.id}/releases`, {
                    method: 'POST',
                    body: {
                      code: relCode.trim(),
                      version: relVersion.trim(),
                      baseline_id: relBaselineId,
                      commit_sha: relCommitSha.trim() || undefined,
                      notes: relNotes.trim() || undefined,
                    },
                  });
                  refreshAll();
                  alert('Release request submitted.');
                } catch (err: any) {
                  alert(err.message || 'Failed to request release.');
                }
              }}
            >
              <div className="form-row">
                <div className="form-group" style={{ flex: '1' }}>
                  <label htmlFor="rel-code">Release Code</label>
                  <input id="rel-code" type="text" required value={relCode} onChange={(e) => setRelCode(e.target.value)} />
                </div>
                <div className="form-group" style={{ flex: '1' }}>
                  <label htmlFor="rel-ver">Semantic Version</label>
                  <input id="rel-ver" type="text" required value={relVersion} onChange={(e) => setRelVersion(e.target.value)} />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="rel-bl">Target Locked Baseline</label>
                <select id="rel-bl" required value={relBaselineId} onChange={(e) => setRelBaselineId(e.target.value)}>
                  <option value="">-- Select Baseline --</option>
                  {baselines?.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.code}: {b.name} ({b.status.toUpperCase()})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="rel-sha">Git Commit SHA (Mandatory if Git is required)</label>
                <input id="rel-sha" type="text" value={relCommitSha} onChange={(e) => setRelCommitSha(e.target.value)} />
              </div>

              <div className="form-group">
                <label htmlFor="rel-notes">Release Notes</label>
                <textarea id="rel-notes" rows={2} value={relNotes} onChange={(e) => setRelNotes(e.target.value)} />
              </div>

              <button type="submit" className="primary">Request Release</button>
            </form>
          </div>

          <div className="panel">
            <h2>Releases</h2>
            {!releases || releases.length === 0 ? (
              <p style={{ color: 'var(--muted-text)' }}>No releases requested yet.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Version</th>
                    <th>Baseline</th>
                    <th>Tests</th>
                    <th>Docs</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {releases.map((rel) => (
                    <tr key={rel.id}>
                      <td><strong>{rel.code}</strong></td>
                      <td>v{rel.version}</td>
                      <td>{rel.baseline_code}</td>
                      <td>{rel.test_status.toUpperCase()}</td>
                      <td>{rel.doc_status.toUpperCase()}</td>
                      <td><StatusBadge status={rel.status} /></td>
                      <td>
                        {role === 'FACULTY' && rel.status === 'requested' && (
                          <div style={{ display: 'flex', gap: '4px' }}>
                            <button
                              type="button"
                              className="primary"
                              onClick={async () => {
                                try {
                                  await apiRequest(`/releases/${rel.id}/decision`, {
                                    method: 'POST',
                                    body: {
                                      decision: 'approved',
                                      test_status: 'passed',
                                      doc_status: 'approved',
                                    },
                                  });
                                  refreshAll();
                                } catch (err: any) {
                                  alert(err.message || 'Approval failed.');
                                }
                              }}
                            >
                              Approve (Set Test & Doc Passed)
                            </button>
                            <button
                              type="button"
                              className="danger"
                              onClick={async () => {
                                try {
                                  await apiRequest(`/releases/${rel.id}/decision`, {
                                    method: 'POST',
                                    body: { decision: 'rejected' },
                                  });
                                  refreshAll();
                                } catch (err: any) {
                                  alert(err.message || 'Rejection failed.');
                                }
                              }}
                            >
                              Reject
                            </button>
                          </div>
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

      {/* 12. STATUS ACCOUNTING */}
      {activeTab === 'status_accounting' && (
        <div className="panel">
          <h2>Configuration Status Accounting</h2>
          <p style={{ fontSize: '13px', color: 'var(--muted-text)', marginBottom: '10px' }}>
            Answers: What is the current configuration of this project? (Latest approved version, current state, locked status, and baselines).
          </p>
          {!statusAccounting || statusAccounting.items.length === 0 ? (
            <p style={{ color: 'var(--muted-text)' }}>No configuration items recorded.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>CI Code</th>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Owner</th>
                  <th>Locked</th>
                  <th>Latest Version</th>
                  <th>State</th>
                  <th>Latest Approved Version</th>
                  <th>Baselines</th>
                </tr>
              </thead>
              <tbody>
                {statusAccounting.items.map((it: any) => (
                  <tr key={it.ci_id}>
                    <td><strong>{it.ci_code}</strong></td>
                    <td>{it.ci_name}</td>
                    <td>{it.ci_type}</td>
                    <td>{it.owner_name || 'Unassigned'}</td>
                    <td>{it.is_locked ? <span className="status-badge locked">LOCKED</span> : 'No'}</td>
                    <td>{it.latest_version_label ? `v${it.latest_version_label}` : '-'}</td>
                    <td><StatusBadge status={it.latest_version_status || 'none'} /></td>
                    <td>{it.latest_approved_version_label ? `v${it.latest_approved_version_label}` : 'None'}</td>
                    <td>{it.baselines?.join(', ') || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* 13. AUDIT REPORT */}
      {activeTab === 'audit_report' && (
        <div className="panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2>SCM Audit Report & Findings</h2>
            <a href={`/api/v1/teams/${team.id}/audit-report?format=csv`} className="btn" target="_blank" rel="noreferrer">
              Export Audit CSV
            </a>
          </div>

          {(auditReport as any)?.findings && (auditReport as any).findings.length > 0 ? (
            <div style={{ marginTop: '12px' }}>
              <h3>Findings & Compliance Gaps</h3>
              <table>
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Severity</th>
                    <th>Entity Code</th>
                    <th>Description</th>
                    <th>Recommendation</th>
                  </tr>
                </thead>
                <tbody>
                  {(auditReport as any).findings.map((f: any, idx: number) => (
                    <tr key={idx}>
                      <td><strong>{f.category}</strong></td>
                      <td>
                        <span style={{ color: f.severity === 'error' ? 'var(--danger-color)' : 'var(--warning-color)', fontWeight: 'bold' }}>
                          {f.severity.toUpperCase()}
                        </span>
                      </td>
                      <td><code>{f.entity_code || '-'}</code></td>
                      <td>{f.description}</td>
                      <td>{f.recommendation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p style={{ color: 'var(--success-color)', margin: '12px 0' }}>
              No audit violations or compliance gaps identified.
            </p>
          )}
        </div>
      )}

      {/* 14. TIMELINE */}
      {activeTab === 'timeline' && (
        <div className="panel">
          <h2>Immutable Activity Timeline</h2>
          <p style={{ fontSize: '12px', color: 'var(--muted-text)', marginBottom: '12px' }}>
            Built directly from the append-only database audit log.
          </p>
          {!timeline || timeline.length === 0 ? (
            <p style={{ color: 'var(--muted-text)' }}>No activity recorded yet.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Actor</th>
                  <th>Action</th>
                  <th>Entity</th>
                  <th>Summary</th>
                </tr>
              </thead>
              <tbody>
                {timeline.map((ev) => (
                  <tr key={ev.id}>
                    <td>{new Date(ev.at).toLocaleString()}</td>
                    <td><strong>{ev.actor_name}</strong> ({ev.actor_role})</td>
                    <td><code>{ev.action}</code></td>
                    <td>{ev.entity_type}</td>
                    <td>{ev.summary}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};
