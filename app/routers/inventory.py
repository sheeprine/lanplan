from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_person
from app.config import PARTY_NAME
from app.database import get_db
from app.models import InventoryItem, Person

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/inventory")
def inventory_overview(
    request: Request,
    db: Session = Depends(get_db),
    current_person: Person | None = Depends(get_current_person),
):
    people = db.scalars(select(Person).order_by(Person.name)).all()
    return templates.TemplateResponse(
        request,
        "inventory.html",
        {"party_name": PARTY_NAME, "current_person": current_person, "people": people},
    )


@router.post("/inventory/items")
def add_item(
    request: Request,
    name: str = Form(...),
    category: str = Form("Other"),
    quantity: int = Form(1),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    current_person: Person | None = Depends(get_current_person),
):
    if current_person is None:
        return RedirectResponse("/select-person", status_code=303)

    name = name.strip()
    if name:
        db.add(
            InventoryItem(
                person_id=current_person.id,
                name=name,
                category=(category.strip() or "Other"),
                quantity=max(1, quantity),
                notes=notes.strip(),
            )
        )
        db.commit()
        db.refresh(current_person)

    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            request,
            "partials/inventory_person.html",
            {"person": current_person, "current_person": current_person},
        )
    return RedirectResponse("/inventory", status_code=303)


@router.post("/inventory/items/{item_id}/delete")
def delete_item(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_person: Person | None = Depends(get_current_person),
):
    item = db.get(InventoryItem, item_id)
    if item and current_person and item.person_id == current_person.id:
        db.delete(item)
        db.commit()
        db.refresh(current_person)

    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            request,
            "partials/inventory_person.html",
            {"person": current_person, "current_person": current_person},
        )
    return RedirectResponse("/inventory", status_code=303)
