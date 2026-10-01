from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_person
from app.config import PARTY_NAME
from app.database import get_db
from app.models import Attendance, Game, GameSession, Person

DATETIME_INPUT_FORMAT = "%Y-%m-%dT%H:%M"

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/games")
def list_games(
    request: Request,
    db: Session = Depends(get_db),
    current_person: Person | None = Depends(get_current_person),
):
    games = db.scalars(select(Game).order_by(Game.name)).all()
    return templates.TemplateResponse(
        request,
        "games.html",
        {"party_name": PARTY_NAME, "current_person": current_person, "games": games},
    )


@router.post("/games")
def create_game(
    request: Request,
    name: str = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    name = name.strip()
    if name and not db.scalar(select(Game).where(Game.name == name)):
        db.add(Game(name=name, notes=notes.strip()))
        db.commit()
    return RedirectResponse("/games", status_code=303)


@router.post("/games/{game_id}/delete")
def delete_game(game_id: int, db: Session = Depends(get_db)):
    game = db.get(Game, game_id)
    if game:
        db.delete(game)
        db.commit()
    return RedirectResponse("/games", status_code=303)


@router.get("/games/{game_id}")
def game_detail(
    game_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_person: Person | None = Depends(get_current_person),
):
    game = db.get(Game, game_id)
    if not game:
        return RedirectResponse("/games", status_code=303)

    now = datetime.now()
    first_arrival = db.scalar(select(func.min(Attendance.start)))
    last_departure = db.scalar(select(func.max(Attendance.end)))
    default_start = first_arrival if first_arrival and first_arrival > now else None
    default_end = last_departure if last_departure and last_departure > now else None

    return templates.TemplateResponse(
        request,
        "game_detail.html",
        {
            "party_name": PARTY_NAME,
            "current_person": current_person,
            "game": game,
            "default_start": default_start.strftime(DATETIME_INPUT_FORMAT) if default_start else None,
            "default_end": default_end.strftime(DATETIME_INPUT_FORMAT) if default_end else None,
        },
    )


@router.post("/games/{game_id}/sessions")
def create_session(
    game_id: int,
    start: str = Form(...),
    end: str = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    game = db.get(Game, game_id)
    if not game:
        return RedirectResponse("/games", status_code=303)
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
    except ValueError:
        return RedirectResponse(f"/games/{game_id}", status_code=303)
    if end_dt > start_dt:
        db.add(GameSession(game_id=game_id, start=start_dt, end=end_dt, notes=notes.strip()))
        db.commit()
    return RedirectResponse(f"/games/{game_id}", status_code=303)


@router.post("/games/{game_id}/sessions/{session_id}/delete")
def delete_session(game_id: int, session_id: int, db: Session = Depends(get_db)):
    session_obj = db.get(GameSession, session_id)
    if session_obj:
        db.delete(session_obj)
        db.commit()
    return RedirectResponse(f"/games/{game_id}", status_code=303)


@router.post("/games/{game_id}/sessions/{session_id}/toggle")
def toggle_session_player(
    game_id: int,
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_person: Person | None = Depends(get_current_person),
):
    session_obj = db.get(GameSession, session_id)
    if session_obj is None or current_person is None:
        return RedirectResponse(f"/games/{game_id}", status_code=303)

    if current_person in session_obj.players:
        session_obj.players.remove(current_person)
    else:
        session_obj.players.append(current_person)
    db.commit()
    db.refresh(session_obj)

    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            request,
            "partials/session_card.html",
            {"session": session_obj, "game": session_obj.game, "current_person": current_person},
        )
    return RedirectResponse(f"/games/{game_id}", status_code=303)
