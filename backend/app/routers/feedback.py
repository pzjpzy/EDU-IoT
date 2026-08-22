"""Student feedback submission (the star-rating + suggestion popup shown when
leaving the capstone). Public per-session; reading feedback is admin-only (see
routers/admin.py)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.deps import get_session_or_404
from app.models import Feedback
from app.schemas import FeedbackCreate

router = APIRouter(prefix="/api/sessions", tags=["feedback"])


@router.post("/{session_id}/feedback", status_code=201)
def submit_feedback(session_id: int, payload: FeedbackCreate, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    if not 1 <= payload.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")
    suggestion = (payload.suggestion or "").strip() or None
    db.add(Feedback(session_id=session.id, rating=payload.rating, suggestion=suggestion))
    db.commit()
    return {"ok": True}
