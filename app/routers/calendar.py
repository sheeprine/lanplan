from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_person
from app.config import PARTY_NAME
from app.database import get_db
from app.models import Attendance, GameSession, Person

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

DAYS_IN_VIEW = 7


def _parse_start(start: str | None) -> date:
    if start:
        try:
            return date.fromisoformat(start)
        except ValueError:
            pass
    return date.today()


def _build_days(db: Session, view_start: date):
    days = []
    for offset in range(DAYS_IN_VIEW):
        day = view_start + timedelta(days=offset)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = day_start + timedelta(days=1)

        attendances = db.scalars(
            select(Attendance)
            .where(Attendance.start < day_end, Attendance.end > day_start)
            .order_by(Attendance.start)
        ).all()
        sessions = db.scalars(
            select(GameSession)
            .where(GameSession.start < day_end, GameSession.end > day_start)
            .order_by(GameSession.start)
        ).all()

        days.append(
            {
                "date": day,
                "is_today": day == date.today(),
                "attendances": attendances,
                "sessions": sessions,
            }
        )
    return days


@router.get("/calendar")
def calendar_view(
    request: Request,
    start: str | None = None,
    db: Session = Depends(get_db),
    current_person: Person | None = Depends(get_current_person),
):
    view_start = _parse_start(start)
    days = _build_days(db, view_start)
    people = db.scalars(select(Person).order_by(Person.name)).all()
    return templates.TemplateResponse(
        request,
        "calendar.html",
        {
            "party_name": PARTY_NAME,
            "current_person": current_person,
            "people": people,
            "days": days,
            "view_start": view_start,
            "today": date.today(),
            "prev_start": view_start - timedelta(days=DAYS_IN_VIEW),
            "next_start": view_start + timedelta(days=DAYS_IN_VIEW),
        },
    )


@router.post("/calendar/attendance")
def add_attendance(
    request: Request,
    start: str = Form(...),
    end: str = Form(...),
    view_start: str = Form(...),
    db: Session = Depends(get_db),
    current_person: Person | None = Depends(get_current_person),
):
    if current_person is None:
        return RedirectResponse("/select-person", status_code=303)

    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
    except ValueError:
        return RedirectResponse(f"/calendar?start={view_start}", status_code=303)

    if end_dt > start_dt:
        db.add(Attendance(person_id=current_person.id, start=start_dt, end=end_dt))
        db.commit()

    return RedirectResponse(f"/calendar?start={view_start}", status_code=303)


@router.post("/calendar/attendance/{attendance_id}/delete")
def delete_attendance(
    attendance_id: int,
    view_start: str = Form(...),
    db: Session = Depends(get_db),
    current_person: Person | None = Depends(get_current_person),
):
    attendance = db.get(Attendance, attendance_id)
    if attendance and current_person and attendance.person_id == current_person.id:
        db.delete(attendance)
        db.commit()
    return RedirectResponse(f"/calendar?start={view_start}", status_code=303)
