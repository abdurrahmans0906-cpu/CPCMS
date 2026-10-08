import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.user import User, Course, Student
from app.models.project import Project, ProjectStudent
from app.schemas.course import CourseCreate, CourseOut
from app.permissions import get_current_user, require_faculty
from app.services.audit import record_audit

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("", response_model=List[CourseOut])
def list_courses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "FACULTY":
        return db.query(Course).filter(Course.faculty_user_id == current_user.id).order_by(Course.code).all()
    else:
        # Student sees courses for projects they are enrolled in
        enrolled_course_ids = (
            db.query(Project.course_id)
            .join(ProjectStudent, Project.id == ProjectStudent.project_id)
            .filter(
                (ProjectStudent.student_user_id == current_user.id) | (
                    ProjectStudent.register_number == (
                        db.query(Student.register_number).filter(Student.user_id == current_user.id).scalar_subquery()
                    )
                )
            )
            .distinct()
            .all()
        )
        c_ids = [c[0] for c in enrolled_course_ids]
        return db.query(Course).filter(Course.id.in_(c_ids)).order_by(Course.code).all()


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    code_clean = payload.code.strip().upper()
    existing = db.query(Course).filter(
        Course.faculty_user_id == current_user.id,
        Course.code == code_clean
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course code '{code_clean}' already exists for your account."
        )

    course = Course(
        code=code_clean,
        name=payload.name.strip(),
        department=payload.department.strip(),
        faculty_user_id=current_user.id
    )
    db.add(course)
    db.flush()

    record_audit(
        db=db,
        action="COURSE_CREATE",
        entity_type="course",
        entity_id=course.id,
        actor=current_user,
        note=f"Created course: {course.code} - {course.name}"
    )
    db.commit()
    db.refresh(course)
    return course


@router.get("/{id}", response_model=CourseOut)
def get_course(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    if current_user.role == "FACULTY" and course.faculty_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    return course
