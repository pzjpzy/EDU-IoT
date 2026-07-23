from fastapi import HTTPException
from sqlalchemy.orm import Session as DBSession

from app.models import VaptSession


def get_session_or_404(session_id: int, db: DBSession) -> VaptSession:
    session = db.get(VaptSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
