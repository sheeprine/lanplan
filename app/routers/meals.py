from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_person
from app.config import PARTY_NAME
from app.database import get_db
from app.models import Meal, Person

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/meals")
def list_meals(
    request: Request,
    db: Session = Depends(get_db),
    current_person: Person | None = Depends(get_current_person),
):
    meals = db.scalars(select(Meal).order_by(Meal.start)).all()
    return templates.TemplateResponse(
        request,
        "meals.html",
        {"party_name": PARTY_NAME, "current_person": current_person, "meals": meals},
    )


@router.post("/meals")
def create_meal(
    name: str = Form(...),
    start: str = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    name = name.strip()
    try:
        start_dt = datetime.fromisoformat(start)
    except ValueError:
        return RedirectResponse("/meals", status_code=303)

    if name:
        db.add(Meal(name=name, start=start_dt, notes=notes.strip()))
        db.commit()
    return RedirectResponse("/meals", status_code=303)


@router.post("/meals/{meal_id}/delete")
def delete_meal(meal_id: int, db: Session = Depends(get_db)):
    meal = db.get(Meal, meal_id)
    if meal:
        db.delete(meal)
        db.commit()
    return RedirectResponse("/meals", status_code=303)


@router.post("/meals/{meal_id}/cook")
def toggle_cook(
    meal_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_person: Person | None = Depends(get_current_person),
):
    meal = db.get(Meal, meal_id)
    if meal is None or current_person is None:
        return RedirectResponse("/meals", status_code=303)

    if meal.cook_id == current_person.id:
        meal.cook_id = None
    elif meal.cook_id is None:
        meal.cook_id = current_person.id
    db.commit()
    db.refresh(meal)

    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            request, "partials/meal_card.html", {"meal": meal, "current_person": current_person}
        )
    return RedirectResponse("/meals", status_code=303)


@router.post("/meals/{meal_id}/clean")
def toggle_cleaner(
    meal_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_person: Person | None = Depends(get_current_person),
):
    meal = db.get(Meal, meal_id)
    if meal is None or current_person is None:
        return RedirectResponse("/meals", status_code=303)

    if meal.cleaner_id == current_person.id:
        meal.cleaner_id = None
    elif meal.cleaner_id is None:
        meal.cleaner_id = current_person.id
    db.commit()
    db.refresh(meal)

    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            request, "partials/meal_card.html", {"meal": meal, "current_person": current_person}
        )
    return RedirectResponse("/meals", status_code=303)


@router.post("/meals/{meal_id}/toggle")
def toggle_attendee(
    meal_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_person: Person | None = Depends(get_current_person),
):
    meal = db.get(Meal, meal_id)
    if meal is None or current_person is None:
        return RedirectResponse("/meals", status_code=303)

    if current_person in meal.attendees:
        meal.attendees.remove(current_person)
    else:
        meal.attendees.append(current_person)
    db.commit()
    db.refresh(meal)

    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            request, "partials/meal_card.html", {"meal": meal, "current_person": current_person}
        )
    return RedirectResponse("/meals", status_code=303)
