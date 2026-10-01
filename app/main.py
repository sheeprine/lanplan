from datetime import date, datetime, timedelta

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.auth import get_current_person, path_requires_auth, path_requires_person
from app.config import PARTY_NAME, SECRET_KEY
from app.database import Base, engine, get_db
from app.models import Attendance, GameSession, Person
from app.routers import auth as auth_router
from app.routers import calendar as calendar_router
from app.routers import games as games_router
from app.routers import inventory as inventory_router
from app.routers import meals as meals_router
from sqlalchemy.orm import Session

app = FastAPI(title=PARTY_NAME)


class AuthGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path_requires_auth(path) and not request.session.get("authed"):
            return RedirectResponse("/login")
        if path_requires_person(path) and not request.session.get("person_id"):
            return RedirectResponse("/select-person")
        return await call_next(request)


# Starlette's add_middleware() inserts at the front of the stack, so the
# middleware added *last* here ends up running *first* at request time.
# AuthGuardMiddleware must run after SessionMiddleware (so request.session
# exists), which means SessionMiddleware has to be added last.
app.add_middleware(AuthGuardMiddleware)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth_router.router)
app.include_router(calendar_router.router)
app.include_router(games_router.router)
app.include_router(inventory_router.router)
app.include_router(meals_router.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_person: Person | None = Depends(get_current_person),
):
    now = datetime.now()
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = today_start + timedelta(days=1)

    here_today = db.scalars(
        select(Person)
        .join(Attendance)
        .where(Attendance.start < today_end, Attendance.end > today_start)
        .distinct()
        .order_by(Person.name)
    ).all()

    upcoming_sessions = db.scalars(
        select(GameSession).where(GameSession.end > now).order_by(GameSession.start).limit(5)
    ).all()

    first_arrival = db.scalar(select(func.min(Attendance.start)))

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "party_name": PARTY_NAME,
            "current_person": current_person,
            "here_today": here_today,
            "upcoming_sessions": upcoming_sessions,
            "first_arrival": first_arrival.date() if first_arrival else None,
        },
    )
