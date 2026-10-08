import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.models.user import User, Student, Faculty, Course
from app.models.project import (
    Project, ProjectTheme, ProjectOutcome, ProjectCITemplate,
    ProjectDeadline, EvaluationCriteria, Review, ReviewSlot, ProjectStudent
)
from app.models.team import Team, TeamMember
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectOut, ProjectSummaryOut,
    ThemeCreate, ThemeOut, OutcomeCreate, OutcomeOut,
    CITemplateCreate, CITemplateOut, DeadlineCreate, DeadlineOut,
    CriteriaCreate, CriteriaOut, ReviewCreate, ReviewOut,
    ReviewSlotCreate, ReviewSlotOut, ProjectStudentOut, StudentEnrollBulkRequest
)
from app.permissions import get_current_user, require_faculty, get_project_with_access
from app.services.audit import record_audit
from app.services.notifications import create_notification

router = APIRouter(prefix="/projects", tags=["Projects"])


def _populate_project_out(project: Project, user: User, db: Session) -> ProjectOut:
    user_team = None
    if user.role == "STUDENT":
        membership = db.query(TeamMember).filter(
            TeamMember.project_id == project.id,
            TeamMember.student_user_id == user.id
        ).first()
        if membership:
            user_team = membership.team

    return ProjectOut(
        id=project.id,
        course_id=project.course_id,
        course_code=project.course.code if project.course else None,
        course_name=project.course.name if project.course else None,
        faculty_user_id=project.faculty_user_id,
        faculty_name=project.faculty_user.name if project.faculty_user else None,
        name=project.name,
        semester=project.semester,
        academic_year=project.academic_year,
        description=project.description,
        problem_statement=project.problem_statement,
        objectives=project.objectives,
        min_team_size=project.min_team_size,
        max_team_size=project.max_team_size,
        team_formation_mode=project.team_formation_mode,
        team_formation_deadline=project.team_formation_deadline,
        max_projects_per_student=project.max_projects_per_student,
        allowed_file_exts=project.allowed_file_exts or [],
        max_file_mb=project.max_file_mb,
        late_policy=project.late_policy,
        late_penalty_percent=float(project.late_penalty_percent),
        versioning_required=project.versioning_required,
        git_required=project.git_required,
        baseline_frequency=project.baseline_frequency,
        change_request_required=project.change_request_required,
        approval_required=project.approval_required,
        branching_policy=project.branching_policy,
        total_marks=project.total_marks,
        grade_bands=project.grade_bands,
        status=project.status,
        created_at=project.created_at,
        themes=[ThemeOut.model_validate(t) for t in project.themes],
        outcomes=[OutcomeOut.model_validate(o) for o in project.outcomes],
        ci_templates=[CITemplateOut.model_validate(c) for c in project.ci_templates],
        deadlines=[DeadlineOut.model_validate(d) for d in project.deadlines],
        evaluation_criteria=[CriteriaOut.model_validate(ec) for ec in project.evaluation_criteria],
        user_team_id=user_team.id if user_team else None,
        user_team_number=user_team.number if user_team else None,
        user_team_status=user_team.status if user_team else None
    )


@router.get("", response_model=List[ProjectOut])
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "FACULTY":
        projects = db.query(Project).filter(
            Project.faculty_user_id == current_user.id
        ).order_by(Project.created_at.desc()).all()
    else:
        # Enrolled projects
        student_profile = current_user.student_profile
        reg_no = student_profile.register_number if student_profile else ""
        projects = (
            db.query(Project)
            .join(ProjectStudent, Project.id == ProjectStudent.project_id)
            .filter(
                (ProjectStudent.student_user_id == current_user.id) | (
                    ProjectStudent.register_number == reg_no
                )
            )
            .order_by(Project.created_at.desc())
            .all()
        )

    return [_populate_project_out(p, current_user, db) for p in projects]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(
        Course.id == payload.course_id,
        Course.faculty_user_id == current_user.id
    ).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    project = Project(
        course_id=payload.course_id,
        faculty_user_id=current_user.id,
        name=payload.name.strip(),
        semester=payload.semester.strip(),
        academic_year=payload.academic_year.strip(),
        description=payload.description,
        problem_statement=payload.problem_statement,
        objectives=payload.objectives,
        min_team_size=payload.min_team_size,
        max_team_size=payload.max_team_size,
        team_formation_mode=payload.team_formation_mode,
        team_formation_deadline=payload.team_formation_deadline,
        max_projects_per_student=payload.max_projects_per_student,
        allowed_file_exts=payload.allowed_file_exts,
        max_file_mb=payload.max_file_mb,
        late_policy=payload.late_policy,
        late_penalty_percent=payload.late_penalty_percent,
        versioning_required=payload.versioning_required,
        git_required=payload.git_required,
        baseline_frequency=payload.baseline_frequency,
        change_request_required=payload.change_request_required,
        approval_required=payload.approval_required,
        branching_policy=payload.branching_policy,
        total_marks=payload.total_marks,
        grade_bands=payload.grade_bands,
        status="active"
    )
    db.add(project)
    db.flush()

    # Initial themes
    for t_name in (payload.themes or []):
        if t_name.strip():
            db.add(ProjectTheme(project_id=project.id, name=t_name.strip()))

    # Initial outcomes
    for idx, o_text in enumerate(payload.outcomes or [], start=1):
        if o_text.strip():
            db.add(ProjectOutcome(project_id=project.id, position=idx, text=o_text.strip()))

    # Initial CI templates
    for idx, ct in enumerate(payload.ci_templates or [], start=1):
        db.add(ProjectCITemplate(
            project_id=project.id,
            position=idx,
            name=ct.get("name", f"Artifact {idx}"),
            ci_type=ct.get("ci_type", "documentation")
        ))

    # Initial Deadlines
    for dl in (payload.deadlines or []):
        db.add(ProjectDeadline(
            project_id=project.id,
            kind=dl.kind,
            title=dl.title,
            due_at=dl.due_at
        ))

    # Initial Criteria (default or provided)
    if payload.criteria:
        for idx, crit in enumerate(payload.criteria, start=1):
            db.add(EvaluationCriteria(
                project_id=project.id,
                position=idx,
                name=crit.name,
                max_marks=crit.max_marks
            ))
    else:
        # Default criteria set from prompt
        default_criteria = [
            ("Problem Definition", 10),
            ("Design", 15),
            ("Implementation", 25),
            ("Testing", 15),
            ("SCM Practices", 15),
            ("Presentation", 10),
            ("Documentation", 10),
        ]
        for idx, (c_name, c_marks) in enumerate(default_criteria, start=1):
            db.add(EvaluationCriteria(
                project_id=project.id,
                position=idx,
                name=c_name,
                max_marks=c_marks
            ))

    record_audit(
        db=db,
        action="PROJECT_CREATE",
        entity_type="project",
        entity_id=project.id,
        actor=current_user,
        project_id=project.id,
        note=f"Created project: {project.name}"
    )
    db.commit()
    db.refresh(project)
    return _populate_project_out(project, current_user, db)


@router.get("/{id}", response_model=ProjectOut)
def get_project(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_project_with_access(id, current_user, db)
    return _populate_project_out(project, current_user, db)


@router.patch("/{id}", response_model=ProjectOut)
def update_project(
    id: uuid.UUID,
    payload: ProjectUpdate,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    project = get_project_with_access(id, current_user, db)

    update_dict = payload.model_dump(exclude_unset=True)
    before_state = {k: getattr(project, k) for k in update_dict.keys()}

    for key, value in update_dict.items():
        setattr(project, key, value)

    record_audit(
        db=db,
        action="PROJECT_UPDATE",
        entity_type="project",
        entity_id=project.id,
        actor=current_user,
        project_id=project.id,
        before=before_state,
        after=update_dict,
        note=f"Updated project settings"
    )
    db.commit()
    db.refresh(project)
    return _populate_project_out(project, current_user, db)


# --- Sub-resources: Themes, Outcomes, CI Templates, Deadlines, Criteria, Reviews ---

@router.post("/{id}/themes", response_model=ThemeOut, status_code=status.HTTP_201_CREATED)
def add_theme(id: uuid.UUID, payload: ThemeCreate, current_user: User = Depends(require_faculty), db: Session = Depends(get_db)):
    project = get_project_with_access(id, current_user, db)
    theme = ProjectTheme(project_id=project.id, name=payload.name.strip())
    db.add(theme)
    db.commit()
    db.refresh(theme)
    return theme


@router.delete("/{id}/themes/{theme_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_theme(id: uuid.UUID, theme_id: uuid.UUID, current_user: User = Depends(require_faculty), db: Session = Depends(get_db)):
    project = get_project_with_access(id, current_user, db)
    db.query(ProjectTheme).filter(ProjectTheme.id == theme_id, ProjectTheme.project_id == project.id).delete()
    db.commit()


@router.post("/{id}/outcomes", response_model=OutcomeOut, status_code=status.HTTP_201_CREATED)
def add_outcome(id: uuid.UUID, payload: OutcomeCreate, current_user: User = Depends(require_faculty), db: Session = Depends(get_db)):
    project = get_project_with_access(id, current_user, db)
    outcome = ProjectOutcome(project_id=project.id, position=payload.position, text=payload.text.strip())
    db.add(outcome)
    db.commit()
    db.refresh(outcome)
    return outcome


@router.delete("/{id}/outcomes/{outcome_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_outcome(id: uuid.UUID, outcome_id: uuid.UUID, current_user: User = Depends(require_faculty), db: Session = Depends(get_db)):
    project = get_project_with_access(id, current_user, db)
    db.query(ProjectOutcome).filter(ProjectOutcome.id == outcome_id, ProjectOutcome.project_id == project.id).delete()
    db.commit()


@router.post("/{id}/ci-templates", response_model=CITemplateOut, status_code=status.HTTP_201_CREATED)
def add_ci_template(id: uuid.UUID, payload: CITemplateCreate, current_user: User = Depends(require_faculty), db: Session = Depends(get_db)):
    project = get_project_with_access(id, current_user, db)
    template = ProjectCITemplate(project_id=project.id, position=payload.position, name=payload.name.strip(), ci_type=payload.ci_type)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{id}/ci-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ci_template(id: uuid.UUID, template_id: uuid.UUID, current_user: User = Depends(require_faculty), db: Session = Depends(get_db)):
    project = get_project_with_access(id, current_user, db)
    db.query(ProjectCITemplate).filter(ProjectCITemplate.id == template_id, ProjectCITemplate.project_id == project.id).delete()
    db.commit()


@router.post("/{id}/deadlines", response_model=DeadlineOut, status_code=status.HTTP_201_CREATED)
def add_deadline(id: uuid.UUID, payload: DeadlineCreate, current_user: User = Depends(require_faculty), db: Session = Depends(get_db)):
    project = get_project_with_access(id, current_user, db)
    dl = ProjectDeadline(project_id=project.id, kind=payload.kind, title=payload.title.strip(), due_at=payload.due_at)
    db.add(dl)
    db.commit()
    db.refresh(dl)
    return dl


@router.delete("/{id}/deadlines/{deadline_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deadline(id: uuid.UUID, deadline_id: uuid.UUID, current_user: User = Depends(require_faculty), db: Session = Depends(get_db)):
    project = get_project_with_access(id, current_user, db)
    db.query(ProjectDeadline).filter(ProjectDeadline.id == deadline_id, ProjectDeadline.project_id == project.id).delete()
    db.commit()


@router.post("/{id}/criteria", response_model=CriteriaOut, status_code=status.HTTP_201_CREATED)
def add_criteria(id: uuid.UUID, payload: CriteriaCreate, current_user: User = Depends(require_faculty), db: Session = Depends(get_db)):
    project = get_project_with_access(id, current_user, db)
    crit = EvaluationCriteria(project_id=project.id, position=payload.position, name=payload.name.strip(), max_marks=payload.max_marks)
    db.add(crit)
    db.commit()
    db.refresh(crit)
    return crit


@router.delete("/{id}/criteria/{criterion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_criteria(id: uuid.UUID, criterion_id: uuid.UUID, current_user: User = Depends(require_faculty), db: Session = Depends(get_db)):
    project = get_project_with_access(id, current_user, db)
    db.query(EvaluationCriteria).filter(EvaluationCriteria.id == criterion_id, EvaluationCriteria.project_id == project.id).delete()
    db.commit()


@router.get("/{id}/reviews", response_model=List[ReviewOut])
def list_reviews(id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = get_project_with_access(id, current_user, db)
    reviews = db.query(Review).filter(Review.project_id == project.id).order_by(Review.start_at).all()
    results = []
    for r in reviews:
        slots_out = []
        for s in r.slots:
            slots_out.append(ReviewSlotOut(
                id=s.id,
                review_id=s.review_id,
                team_id=s.team_id,
                team_number=s.team.number if s.team else None,
                team_title=s.team.title if s.team else None,
                start_at=s.start_at,
                created_at=s.created_at
            ))
        results.append(ReviewOut(
            id=r.id,
            project_id=r.project_id,
            title=r.title,
            start_at=r.start_at,
            mode=r.mode,
            meeting_link=r.meeting_link,
            venue=r.venue,
            agenda=r.agenda,
            instructions=r.instructions,
            slots=slots_out,
            created_at=r.created_at
        ))
    return results


@router.post("/{id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(id: uuid.UUID, payload: ReviewCreate, current_user: User = Depends(require_faculty), db: Session = Depends(get_db)):
    project = get_project_with_access(id, current_user, db)
    rev = Review(
        project_id=project.id,
        title=payload.title.strip(),
        start_at=payload.start_at,
        mode=payload.mode,
        meeting_link=payload.meeting_link,
        venue=payload.venue,
        agenda=payload.agenda,
        instructions=payload.instructions
    )
    db.add(rev)
    db.flush()

    # Notify students
    enrolled = db.query(ProjectStudent).filter(ProjectStudent.project_id == project.id, ProjectStudent.student_user_id.isnot(None)).all()
    for es in enrolled:
        if es.student_user_id:
            create_notification(
                db=db,
                user_id=es.student_user_id,
                kind="review_scheduled",
                message=f"Review '{rev.title}' has been scheduled for {project.name} on {rev.start_at.strftime('%Y-%m-%d %H:%M')}.",
                link=f"/projects/{project.id}"
            )

    record_audit(
        db=db,
        action="REVIEW_CREATE",
        entity_type="review",
        entity_id=rev.id,
        actor=current_user,
        project_id=project.id,
        note=f"Scheduled review: {rev.title}"
    )
    db.commit()
    db.refresh(rev)
    return ReviewOut(
        id=rev.id,
        project_id=rev.project_id,
        title=rev.title,
        start_at=rev.start_at,
        mode=rev.mode,
        meeting_link=rev.meeting_link,
        venue=rev.venue,
        agenda=rev.agenda,
        instructions=rev.instructions,
        slots=[],
        created_at=rev.created_at
    )


@router.post("/reviews/{review_id}/slots", response_model=ReviewSlotOut, status_code=status.HTTP_201_CREATED)
def add_review_slot(review_id: uuid.UUID, payload: ReviewSlotCreate, current_user: User = Depends(require_faculty), db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.project.faculty_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    slot = ReviewSlot(
        review_id=review.id,
        team_id=payload.team_id,
        start_at=payload.start_at
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return ReviewSlotOut(
        id=slot.id,
        review_id=slot.review_id,
        team_id=slot.team_id,
        team_number=slot.team.number if slot.team else None,
        team_title=slot.team.title if slot.team else None,
        start_at=slot.start_at,
        created_at=slot.created_at
    )


# --- Student Enrolment ---

@router.get("/{id}/students", response_model=List[ProjectStudentOut])
def get_enrolled_students(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_project_with_access(id, current_user, db)
    enrolled = db.query(ProjectStudent).filter(ProjectStudent.project_id == project.id).order_by(ProjectStudent.register_number).all()

    # Preload teams in this project
    team_memberships = db.query(TeamMember).filter(TeamMember.project_id == project.id).all()
    user_to_team = {tm.student_user_id: (tm.team_id, tm.team.number) for tm in team_memberships}

    result = []
    for es in enrolled:
        team_id = None
        team_num = None
        if es.student_user_id and es.student_user_id in user_to_team:
            team_id, team_num = user_to_team[es.student_user_id]

        user_obj = es.student_user
        student_obj = user_obj.student_profile if user_obj else None

        result.append(ProjectStudentOut(
            id=es.id,
            project_id=es.project_id,
            register_number=es.register_number,
            student_user_id=es.student_user_id,
            student_name=user_obj.name if user_obj else None,
            student_email=user_obj.email if user_obj else None,
            department=student_obj.department if student_obj else None,
            is_registered=(user_obj is not None),
            team_id=team_id,
            team_number=team_num,
            added_at=es.added_at
        ))
    return result


@router.post("/{id}/students", response_model=List[ProjectStudentOut])
def enroll_students_bulk(
    id: uuid.UUID,
    payload: StudentEnrollBulkRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    project = get_project_with_access(id, current_user, db)

    # Parse tokens by newline or comma or whitespace
    raw_tokens = re.split(r"[\r\n,]+", payload.register_numbers)
    reg_numbers = [tok.strip().upper() for tok in raw_tokens if tok.strip()]

    if not reg_numbers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No register numbers provided.")

    added_list = []
    for reg in reg_numbers:
        existing = db.query(ProjectStudent).filter(
            ProjectStudent.project_id == project.id,
            ProjectStudent.register_number == reg
        ).first()
        if existing:
            continue

        # Look up if student is already registered
        student_record = db.query(Student).filter(Student.register_number == reg).first()
        student_user_id = student_record.user_id if student_record else None

        # Check max_projects_per_student rule:
        # "max_projects_per_student is checked when enrolling: count the student's enrolments in the same course, semester and academic year."
        if student_user_id:
            count_enrolments = (
                db.query(func.count(ProjectStudent.id))
                .join(Project, ProjectStudent.project_id == Project.id)
                .filter(
                    ProjectStudent.student_user_id == student_user_id,
                    Project.course_id == project.course_id,
                    Project.semester == project.semester,
                    Project.academic_year == project.academic_year
                )
                .scalar()
            )
            if count_enrolments >= project.max_projects_per_student:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Student '{reg}' has already reached the maximum project enrollment limit ({project.max_projects_per_student}) for this semester."
                )

        ps = ProjectStudent(
            project_id=project.id,
            register_number=reg,
            student_user_id=student_user_id,
            added_at=datetime.now(timezone.utc)
        )
        db.add(ps)
        db.flush()
        added_list.append(ps)

        if student_user_id:
            create_notification(
                db=db,
                user_id=student_user_id,
                kind="added_to_project",
                message=f"You have been enrolled in project '{project.name}' for course {project.course.code}.",
                link=f"/projects/{project.id}"
            )

    record_audit(
        db=db,
        action="STUDENTS_ENROLLED_BULK",
        entity_type="project",
        entity_id=project.id,
        actor=current_user,
        project_id=project.id,
        note=f"Enrolled {len(added_list)} students by register number"
    )
    db.commit()

    return get_enrolled_students(project.id, current_user, db)


@router.delete("/{id}/students/{reg_no}", status_code=status.HTTP_204_NO_CONTENT)
def remove_student_enrollment(
    id: uuid.UUID,
    reg_no: str,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    project = get_project_with_access(id, current_user, db)
    reg_clean = reg_no.strip().upper()

    # If student is in a team in this project, prevent removal or clean up
    enrolled = db.query(ProjectStudent).filter(
        ProjectStudent.project_id == project.id,
        ProjectStudent.register_number == reg_clean
    ).first()

    if not enrolled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not enrolled in this project")

    if enrolled.student_user_id:
        membership = db.query(TeamMember).filter(
            TeamMember.project_id == project.id,
            TeamMember.student_user_id == enrolled.student_user_id
        ).first()
        if membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot remove student '{reg_clean}' because they already belong to Team {membership.team.number}."
            )

    db.delete(enrolled)
    db.commit()


@router.get("/{id}/unassigned", response_model=List[ProjectStudentOut])
def get_unassigned_students(
    id: uuid.UUID,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    project = get_project_with_access(id, current_user, db)

    # Subquery of student_user_ids assigned to a team in this project
    assigned_user_ids = db.query(TeamMember.student_user_id).filter(TeamMember.project_id == project.id).subquery()

    unassigned_enrolled = (
        db.query(ProjectStudent)
        .filter(
            ProjectStudent.project_id == project.id,
            (ProjectStudent.student_user_id.is_(None)) | (~ProjectStudent.student_user_id.in_(assigned_user_ids))
        )
        .all()
    )

    result = []
    for es in unassigned_enrolled:
        user_obj = es.student_user
        student_obj = user_obj.student_profile if user_obj else None
        result.append(ProjectStudentOut(
            id=es.id,
            project_id=es.project_id,
            register_number=es.register_number,
            student_user_id=es.student_user_id,
            student_name=user_obj.name if user_obj else None,
            student_email=user_obj.email if user_obj else None,
            department=student_obj.department if student_obj else None,
            is_registered=(user_obj is not None),
            team_id=None,
            team_number=None,
            added_at=es.added_at
        ))
    return result


@router.post("/{id}/auto-assign", response_model=Dict[str, Any])
def auto_assign_unassigned_students(
    id: uuid.UUID,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    project = get_project_with_access(id, current_user, db)

    # Only assign students that have registered accounts
    assigned_user_ids = db.query(TeamMember.student_user_id).filter(TeamMember.project_id == project.id).subquery()

    eligible_unassigned = (
        db.query(ProjectStudent)
        .filter(
            ProjectStudent.project_id == project.id,
            ProjectStudent.student_user_id.isnot(None),
            ~ProjectStudent.student_user_id.in_(assigned_user_ids)
        )
        .all()
    )

    if not eligible_unassigned:
        return {"assigned_count": 0, "new_teams_count": 0, "message": "No eligible registered unassigned students found."}

    students_to_assign = [es.student_user_id for es in eligible_unassigned]

    # 1. Fill existing teams that are below max_team_size
    existing_teams = db.query(Team).filter(Team.project_id == project.id).order_by(Team.number).all()
    assigned_count = 0
    student_idx = 0

    for team in existing_teams:
        cur_size = len(team.members)
        while cur_size < project.max_team_size and student_idx < len(students_to_assign):
            uid = students_to_assign[student_idx]
            db.add(TeamMember(
                team_id=team.id,
                project_id=project.id,
                student_user_id=uid,
                role="member"
            ))
            cur_size += 1
            student_idx += 1
            assigned_count += 1

    # 2. Form new teams for the remainder within min and max team size
    new_teams_count = 0
    next_team_number = (db.query(func.coalesce(func.max(Team.number), 0)).filter(Team.project_id == project.id).scalar() or 0) + 1

    while student_idx < len(students_to_assign):
        chunk_size = min(project.max_team_size, len(students_to_assign) - student_idx)
        new_team = Team(
            project_id=project.id,
            number=next_team_number,
            title=f"Team {next_team_number}",
            status="Created",
            formed_by="faculty"
        )
        db.add(new_team)
        db.flush()
        next_team_number += 1
        new_teams_count += 1

        for i in range(chunk_size):
            uid = students_to_assign[student_idx]
            role = "leader" if i == 0 else "member"
            db.add(TeamMember(
                team_id=new_team.id,
                project_id=project.id,
                student_user_id=uid,
                role=role
            ))
            student_idx += 1
            assigned_count += 1

    db.commit()
    return {
        "assigned_count": assigned_count,
        "new_teams_count": new_teams_count,
        "message": f"Successfully auto-assigned {assigned_count} students across existing and {new_teams_count} new team(s)."
    }


@router.get("/{id}/summary", response_model=ProjectSummaryOut)
def get_project_summary(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_project_with_access(id, current_user, db)

    team_count = db.query(func.count(Team.id)).filter(Team.project_id == project.id).scalar() or 0
    student_count = db.query(func.count(ProjectStudent.id)).filter(ProjectStudent.project_id == project.id).scalar() or 0

    # Teams by status
    status_counts_rows = (
        db.query(Team.status, func.count(Team.id))
        .filter(Team.project_id == project.id)
        .group_by(Team.status)
        .all()
    )
    teams_by_status = {row[0]: row[1] for row in status_counts_rows}

    return ProjectSummaryOut(
        id=project.id,
        name=project.name,
        course_code=project.course.code,
        semester=project.semester,
        academic_year=project.academic_year,
        team_count=team_count,
        student_count=student_count,
        status=project.status,
        teams_by_status=teams_by_status
    )
