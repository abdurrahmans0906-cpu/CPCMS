import type { paths } from './schema';

let accessToken: string | null = localStorage.getItem('cpcms_access_token');

export function setAccessToken(token: string | null) {
  accessToken = token;
  if (token) {
    localStorage.setItem('cpcms_access_token', token);
  } else {
    localStorage.removeItem('cpcms_access_token');
  }
}

export function getAccessToken(): string | null {
  return accessToken;
}

export interface ApiRequestOptions extends Omit<RequestInit, 'body'> {
  body?: any;
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: ApiRequestOptions = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});

  if (accessToken && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  // Handle json payload automatically if object and not FormData
  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
    options.body = JSON.stringify(options.body);
  }

  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'include', // Needed for refresh cookie
  };

  let response = await fetch(`/api/v1${endpoint}`, config);

  // If 401 and not already refreshing or logging in, attempt automatic refresh
  if (response.status === 401 && !endpoint.startsWith('/auth/login') && !endpoint.startsWith('/auth/refresh')) {
    try {
      const refreshRes = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        credentials: 'include',
      });
      if (refreshRes.ok) {
        const refreshData = await refreshRes.json();
        setAccessToken(refreshData.access_token);
        headers.set('Authorization', `Bearer ${refreshData.access_token}`);
        response = await fetch(`/api/v1${endpoint}`, {
          ...options,
          headers,
          credentials: 'include',
        });
      } else {
        setAccessToken(null);
      }
    } catch {
      setAccessToken(null);
    }
  }

  if (!response.ok) {
    let errorDetail = 'An error occurred';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail || `HTTP error ${response.status}`);
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return (await response.json()) as T;
  }
  return (await response.text()) as unknown as T;
}

// Type aliases from generated schema
export type SchemaUserOut = paths['/api/v1/auth/me']['get']['responses']['200']['content']['application/json'];
export type SchemaCourseOut = paths['/api/v1/courses']['get']['responses']['200']['content']['application/json'][number];
export type SchemaProjectOut = paths['/api/v1/projects']['get']['responses']['200']['content']['application/json'][number];
export type SchemaProjectStudentOut = paths['/api/v1/projects/{id}/students']['get']['responses']['200']['content']['application/json'][number];
export type SchemaTeamOut = paths['/api/v1/projects/{project_id}/teams']['get']['responses']['200']['content']['application/json'][number];
export type SchemaProposalOut = paths['/api/v1/teams/{team_id}/proposals']['get']['responses']['200']['content']['application/json'][number];
export type SchemaCIOut = paths['/api/v1/teams/{team_id}/cis']['get']['responses']['200']['content']['application/json'][number];
export type SchemaCIVersionOut = paths['/api/v1/cis/{id}/versions']['post']['responses']['201']['content']['application/json'];
export type SchemaBaselineOut = paths['/api/v1/teams/{team_id}/baselines']['get']['responses']['200']['content']['application/json'][number];
export type SchemaChangeRequestOut = paths['/api/v1/teams/{team_id}/change-requests']['get']['responses']['200']['content']['application/json'][number];
export type SchemaCRImpactOut = paths['/api/v1/change-requests/{id}/impact']['get']['responses']['200']['content']['application/json'];
export type SchemaRepositoryOut = paths['/api/v1/teams/{team_id}/repository']['get']['responses']['200']['content']['application/json'];
export type SchemaProgressReportOut = paths['/api/v1/teams/{team_id}/progress']['get']['responses']['200']['content']['application/json'][number];
export type SchemaSubmissionOut = paths['/api/v1/teams/{team_id}/submissions']['get']['responses']['200']['content']['application/json'][number];
export type SchemaEvaluationOut = paths['/api/v1/teams/{team_id}/evaluations']['get']['responses']['200']['content']['application/json'][number];
export type SchemaReleaseOut = paths['/api/v1/teams/{team_id}/releases']['get']['responses']['200']['content']['application/json'][number];
export type SchemaStatusAccountingReport = paths['/api/v1/teams/{team_id}/status-accounting']['get']['responses']['200']['content']['application/json'];
export type SchemaAuditReportOut = paths['/api/v1/teams/{team_id}/audit-report']['get']['responses']['200']['content']['application/json'];
export type SchemaTimelineEvent = paths['/api/v1/teams/{team_id}/timeline']['get']['responses']['200']['content']['application/json'][number];
export type SchemaAnalyticsOut = paths['/api/v1/projects/{project_id}/analytics']['get']['responses']['200']['content']['application/json'];
