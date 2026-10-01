from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Person

EXEMPT_PREFIXES = ("/static",)
EXEMPT_PATHS = {"/login", "/select-person"}


def path_requires_auth(path: str) -> bool:
    if path.startswith(EXEMPT_PREFIXES):
        return False
    if path in EXEMPT_PATHS:
        return False
    return True


def path_requires_person(path: str) -> bool:
    return path_requires_auth(path) and path != "/select-person"


def get_current_person(request: Request, db: Session = Depends(get_db)) -> Person | None:
    person_id = request.session.get("person_id")
    if not person_id:
        return None
    return db.get(Person, person_id)
