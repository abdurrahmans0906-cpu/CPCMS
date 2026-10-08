from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.project import ProjectDeadline, ProjectStudent
from app.models.notification import Notification
from app.models.user import User

scheduler = BackgroundScheduler()


def check_upcoming_deadlines_job():
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        # Check deadlines within 3 days and within 1 day
        three_days_later = now + timedelta(days=3)
        one_day_later = now + timedelta(days=1)

        deadlines = db.query(ProjectDeadline).filter(
            ProjectDeadline.due_at > now,
            ProjectDeadline.due_at <= three_days_later
        ).all()

        for dl in deadlines:
            remaining_hours = (dl.due_at - now).total_seconds() / 3600
            tag = "3 days" if remaining_hours > 24 else "1 day"

            # Enrolled students
            enrolled = db.query(ProjectStudent).filter(
                ProjectStudent.project_id == dl.project_id,
                ProjectStudent.student_user_id.isnot(None)
            ).all()

            for es in enrolled:
                if not es.student_user_id:
                    continue
                # Check if notification was already sent in the last 24h
                already_sent = db.query(Notification).filter(
                    Notification.user_id == es.student_user_id,
                    Notification.kind == f"deadline_{tag.replace(' ', '_')}",
                    Notification.message.like(f"%{dl.title}%")
                ).first()

                if not already_sent:
                    notif = Notification(
                        user_id=es.student_user_id,
                        kind=f"deadline_{tag.replace(' ', '_')}",
                        message=f"Reminder: Deadline '{dl.title}' for {dl.project.name} is due in {tag} (at {dl.due_at.strftime('%Y-%m-%d %H:%M')}).",
                        link=f"/projects/{dl.project_id}",
                        is_read=False
                    )
                    db.add(notif)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error in scheduler job check_upcoming_deadlines: {e}")
    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(check_upcoming_deadlines_job, "interval", hours=12, id="deadline_notifications", replace_existing=True)
        scheduler.start()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
