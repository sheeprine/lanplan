import secrets
import random

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import PARTY_NAME, PARTY_PASSWORD
from app.database import get_db
from app.models import PERSON_COLORS, Person

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(
        request, "login.html", {"party_name": PARTY_NAME, "error": None}
    )


@router.post("/login")
def login_submit(request: Request, password: str = Form(...)):
    if not secrets.compare_digest(password, PARTY_PASSWORD):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"party_name": PARTY_NAME, "error": "Wrong password."},
            status_code=400,
        )
    request.session["authed"] = True
    return RedirectResponse("/select-person", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/select-person")
def select_person_form(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("authed"):
        return RedirectResponse("/login", status_code=303)
    people = db.scalars(select(Person).order_by(Person.name)).all()
    return templates.TemplateResponse(
        request, "select_person.html", {"party_name": PARTY_NAME, "people": people, "error": None}
    )


@router.post("/select-person")
def select_person_submit(
    request: Request,
    db: Session = Depends(get_db),
    person_id: int | None = Form(None),
    new_name: str = Form(""),
):
    if not request.session.get("authed"):
        return RedirectResponse("/login", status_code=303)

    new_name = new_name.strip()
    if new_name:
        existing = db.scalar(select(Person).where(Person.name == new_name))
        if existing:
            person = existing
        else:
            used_colors = {p.color for p in db.scalars(select(Person)).all()}
            available = [c for c in PERSON_COLORS if c not in used_colors] or PERSON_COLORS
            person = Person(name=new_name, color=random.choice(available))
            db.add(person)
            db.commit()
            db.refresh(person)
    elif person_id:
        person = db.get(Person, person_id)
    else:
        people = db.scalars(select(Person).order_by(Person.name)).all()
        return templates.TemplateResponse(
            request,
            "select_person.html",
            {
                "party_name": PARTY_NAME,
                "people": people,
                "error": "Pick an existing name or type a new one.",
            },
            status_code=400,
        )

    request.session["person_id"] = person.id
    return RedirectResponse("/", status_code=303)
