"""Admin panel API: password login + reading all submitted feedback.

The panel UI lives at /admin in the frontend; these endpoints back it. All
reads are gated by the admin bearer token (see services/admin_auth.py)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.models import Feedback
from app.schemas import AdminLogin, FeedbackOut
from app.services import admin_auth

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/login")
def admin_login(payload: AdminLogin):
    try:
        token = admin_auth.login(payload.password)
    except PermissionError:
        raise HTTPException(status_code=401, detail="Invalid admin password.")
    return {"token": token}


@router.get("/feedback", response_model=list[FeedbackOut], dependencies=[Depends(admin_auth.require_admin)])
def list_feedback(db: DBSession = Depends(get_db)):
    return db.query(Feedback).order_by(Feedback.created_at.desc()).all()
