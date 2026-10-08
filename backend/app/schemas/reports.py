import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class StatusAccountingItem(BaseModel):
    ci_id: uuid.UUID
    ci_code: str
    ci_name: str
    ci_type: str
    owner_name: Optional[str] = None
    is_locked: bool
    latest_version_label: Optional[str] = None
    latest_version_status: Optional[str] = None
    latest_approved_version_label: Optional[str] = None
    latest_approved_at: Optional[datetime] = None
    baselines: List[str] = []


class StatusAccountingReport(BaseModel):
    team_id: uuid.UUID
    team_number: int
    team_title: str
    generated_at: datetime
    total_cis: int
    items: List[StatusAccountingItem] = []


class AuditFinding(BaseModel):
    category: str
    severity: str  # warning, error, info
    description: str
    entity_code: Optional[str] = None
    recommendation: str


class AuditReportOut(BaseModel):
    team_id: uuid.UUID
    team_number: int
    team_title: str
    generated_at: datetime
    totals: Dict[str, Any]
    findings: List[AuditFinding] = []


class TimelineEvent(BaseModel):
    id: int
    at: datetime
    actor_name: str
    actor_role: str
    action: str
    entity_type: str
    entity_id: str
    summary: str
    note: Optional[str] = None


class AnalyticsOut(BaseModel):
    project_id: uuid.UUID
    total_students: int
    total_teams: int
    active_teams: int
    completed_teams: int
    pending_proposals: int
    pending_changes: int
    upcoming_reviews: int
    average_score: Optional[float] = None
    delayed_teams: List[Dict[str, Any]] = []
    inactive_teams: List[Dict[str, Any]] = []  # no activity in 14 days
    teams_with_frequent_changes: List[Dict[str, Any]] = []
    overdue_reviews: List[Dict[str, Any]] = []
