import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiRequest, SchemaCourseOut } from '../api/client';
import { Breadcrumbs } from '../components/Breadcrumbs';

export const CreateProjectPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: courses, isLoading: coursesLoading } = useQuery<SchemaCourseOut[]>({
    queryKey: ['courses'],
    queryFn: () => apiRequest('/courses'),
  });

  const [courseId, setCourseId] = useState('');
  const [name, setName] = useState('');
  const [semester, setSemester] = useState('Fall');
  const [academicYear, setAcademicYear] = useState('2026-2027');
  const [description, setDescription] = useState('');
  const [problemStatement, setProblemStatement] = useState('');
  const [objectives, setObjectives] = useState('');

  // Team formation settings
  const [minTeamSize, setMinTeamSize] = useState(2);
  const [maxTeamSize, setMaxTeamSize] = useState(4);
  const [teamFormationMode, setTeamFormationMode] = useState<'student' | 'faculty' | 'hybrid'>('hybrid');
  const [teamFormationDeadline, setTeamFormationDeadline] = useState('');
  const [maxProjectsPerStudent, setMaxProjectsPerStudent] = useState(1);

  // SCM Rules
  const [allowedFileExts, setAllowedFileExts] = useState('pdf, zip, docx, md, txt, py, ts, json');
  const [maxFileMb, setMaxFileMb] = useState(25);
  const [latePolicy, setLatePolicy] = useState<'reject' | 'allow_flagged' | 'allow_penalty'>('allow_flagged');
  const [latePenaltyPercent, setLatePenaltyPercent] = useState(10);
  const [versioningRequired, setVersioningRequired] = useState(true);
  const [gitRequired, setGitRequired] = useState(false);
  const [baselineFrequency, setBaselineFrequency] = useState('per_review');
  const [changeRequestRequired, setChangeRequestRequired] = useState(true);
  const [approvalRequired, setApprovalRequired] = useState(true);
  const [branchingPolicy, setBranchingPolicy] = useState<'none' | 'gitflow_lite'>('none');

  // Evaluation
  const [totalMarks, setTotalMarks] = useState(100);

  // Themes, Outcomes, CI Templates
  const [themesText, setThemesText] = useState('Healthcare Systems\nE-Commerce & Supply Chain\nEducational Technologies');
  const [outcomesText, setOutcomesText] = useState('Understand SCM practices and baselines.\nBuild working software with full change control.');
  const [ciTemplatesText, setCiTemplatesText] = useState('SRS Document (srs)\nSystem Architecture (architecture)\nSource Code (backend)\nTest Suite (test_cases)');

  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: (payload: any) => apiRequest('/projects', { method: 'POST', body: payload }),
    onSuccess: (newProj) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      navigate(`/projects/${newProj.id}`);
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to create project.');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!courseId) {
      setError('Please select a course.');
      return;
    }

    // Parse themes
    const themes = themesText
      .split('\n')
      .map((t) => t.trim())
      .filter(Boolean);

    // Parse outcomes
    const outcomes = outcomesText
      .split('\n')
      .map((o) => o.trim())
      .filter(Boolean);

    // Parse CI templates: Name (type)
    const ciTemplates: { name: string; ci_type: string }[] = [];
    ciTemplatesText.split('\n').forEach((line) => {
      const match = line.match(/^(.*?)(?:\s*\((.*?)\))?$/);
      if (match && match[1].trim()) {
        ciTemplates.push({
          name: match[1].trim(),
          ci_type: match[2]?.trim() || 'documentation',
        });
      }
    });

    const exts = allowedFileExts
      .split(',')
      .map((e) => e.trim().replace(/^\./, ''))
      .filter(Boolean);

    const payload = {
      course_id: courseId,
      name: name.trim(),
      semester: semester.trim(),
      academic_year: academicYear.trim(),
      description: description.trim() || undefined,
      problem_statement: problemStatement.trim() || undefined,
      objectives: objectives.trim() || undefined,
      min_team_size: Number(minTeamSize),
      max_team_size: Number(maxTeamSize),
      team_formation_mode: teamFormationMode,
      team_formation_deadline: teamFormationDeadline ? new Date(teamFormationDeadline).toISOString() : undefined,
      max_projects_per_student: Number(maxProjectsPerStudent),
      allowed_file_exts: exts,
      max_file_mb: Number(maxFileMb),
      late_policy: latePolicy,
      late_penalty_percent: Number(latePenaltyPercent),
      versioning_required: versioningRequired,
      git_required: gitRequired,
      baseline_frequency: baselineFrequency,
      change_request_required: changeRequestRequired,
      approval_required: approvalRequired,
      branching_policy: branchingPolicy,
      total_marks: Number(totalMarks),
      themes,
      outcomes,
      ci_templates: ciTemplates,
    };

    createMutation.mutate(payload);
  };

  if (coursesLoading) return <div>Loading...</div>;

  return (
    <div>
      <Breadcrumbs items={[{ label: 'Dashboard', to: '/' }, { label: 'Projects', to: '/projects' }, { label: 'Create Project' }]} />
      <h1>Create Course Project Workspace</h1>

      {error && <div className="banner banner-error">{error}</div>}

      <div className="panel" style={{ maxWidth: '640px' }}>
        <form onSubmit={handleSubmit} style={{ width: '100%', maxWidth: '100%' }}>
          <h2>1. Basic Information</h2>

          <div className="form-group">
            <label htmlFor="course-select">Course</label>
            <select
              id="course-select"
              required
              value={courseId}
              onChange={(e) => setCourseId(e.target.value)}
            >
              <option value="">-- Select Course --</option>
              {courses?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.code} - {c.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="project-name">Project Workspace Name</label>
            <input
              id="project-name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Course Project - Semester Long"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="proj-sem">Semester</label>
              <input
                id="proj-sem"
                type="text"
                required
                value={semester}
                onChange={(e) => setSemester(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="proj-ay">Academic Year</label>
              <input
                id="proj-ay"
                type="text"
                required
                value={academicYear}
                onChange={(e) => setAcademicYear(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="proj-desc">Description</label>
            <textarea
              id="proj-desc"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="proj-prob">Problem Statement Guidelines</label>
            <textarea
              id="proj-prob"
              rows={2}
              value={problemStatement}
              onChange={(e) => setProblemStatement(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="proj-obj">Expected Outcomes / Objectives</label>
            <textarea
              id="proj-obj"
              rows={2}
              value={objectives}
              onChange={(e) => setObjectives(e.target.value)}
            />
          </div>

          <h2 style={{ marginTop: '24px' }}>2. Team Configuration</h2>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="min-team">Min Team Size</label>
              <input
                id="min-team"
                type="number"
                min={1}
                required
                value={minTeamSize}
                onChange={(e) => setMinTeamSize(Number(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label htmlFor="max-team">Max Team Size</label>
              <input
                id="max-team"
                type="number"
                min={minTeamSize}
                required
                value={maxTeamSize}
                onChange={(e) => setMaxTeamSize(Number(e.target.value))}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="formation-mode">Formation Mode</label>
              <select
                id="formation-mode"
                value={teamFormationMode}
                onChange={(e) => setTeamFormationMode(e.target.value as any)}
              >
                <option value="hybrid">Hybrid (Students form first, Faculty auto-assigns after deadline)</option>
                <option value="student">Student (Students create and invite)</option>
                <option value="faculty">Faculty (Instructor creates and assigns only)</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="formation-deadline">Team Formation Deadline (Optional)</label>
            <input
              id="formation-deadline"
              type="datetime-local"
              value={teamFormationDeadline}
              onChange={(e) => setTeamFormationDeadline(e.target.value)}
            />
          </div>

          <h2 style={{ marginTop: '24px' }}>3. SCM & Project Governance Rules</h2>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="allowed-exts">Allowed File Extensions</label>
              <input
                id="allowed-exts"
                type="text"
                value={allowedFileExts}
                onChange={(e) => setAllowedFileExts(e.target.value)}
              />
              <div className="form-help">Comma-separated list (e.g. pdf, zip, md, py, ts)</div>
            </div>
            <div className="form-group">
              <label htmlFor="max-mb">Max File Size (MB)</label>
              <input
                id="max-mb"
                type="number"
                min={1}
                max={200}
                value={maxFileMb}
                onChange={(e) => setMaxFileMb(Number(e.target.value))}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="late-policy">Late Submission Policy</label>
              <select
                id="late-policy"
                value={latePolicy}
                onChange={(e) => setLatePolicy(e.target.value as any)}
              >
                <option value="allow_flagged">Allow and flag as late</option>
                <option value="allow_penalty">Allow with percentage penalty</option>
                <option value="reject">Strictly reject late submissions</option>
              </select>
            </div>
            {latePolicy === 'allow_penalty' && (
              <div className="form-group">
                <label htmlFor="late-penalty">Penalty Percent (%)</label>
                <input
                  id="late-penalty"
                  type="number"
                  min={0}
                  max={100}
                  value={latePenaltyPercent}
                  onChange={(e) => setLatePenaltyPercent(Number(e.target.value))}
                />
              </div>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="branch-policy">Git Branching Policy</label>
              <select
                id="branch-policy"
                value={branchingPolicy}
                onChange={(e) => setBranchingPolicy(e.target.value as any)}
              >
                <option value="none">None (Any branch name)</option>
                <option value="gitflow_lite">GitFlow Lite (main, develop, feature/*, release/*, hotfix/*)</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', margin: '12px 0' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'normal' }}>
              <input
                type="checkbox"
                checked={versioningRequired}
                onChange={(e) => setVersioningRequired(e.target.checked)}
              />
              Versioning required for all artifacts
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'normal' }}>
              <input
                type="checkbox"
                checked={gitRequired}
                onChange={(e) => setGitRequired(e.target.checked)}
              />
              Git repository link required for release requests
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'normal' }}>
              <input
                type="checkbox"
                checked={changeRequestRequired}
                onChange={(e) => setChangeRequestRequired(e.target.checked)}
              />
              Change Request required to edit locked baselined CIs
            </label>
          </div>

          <h2 style={{ marginTop: '24px' }}>4. Templates & Themes</h2>

          <div className="form-group">
            <label htmlFor="themes-text">Project Themes (One per line)</label>
            <textarea
              id="themes-text"
              rows={3}
              value={themesText}
              onChange={(e) => setThemesText(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="ci-templates">Default CI Template Items (One per line, e.g. Name (type))</label>
            <textarea
              id="ci-templates"
              rows={4}
              value={ciTemplatesText}
              onChange={(e) => setCiTemplatesText(e.target.value)}
            />
            <div className="form-help">
              Types: requirements, srs, architecture, database_design, backend, frontend, test_cases, test_report, documentation, other.
            </div>
          </div>

          <div style={{ marginTop: '20px' }}>
            <button type="submit" className="primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Loading...' : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
