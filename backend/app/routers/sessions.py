from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.deps import get_session_or_404
from app.models import VaptSession
from app.schemas import SessionCreate, SessionOut
from app.services.guardrail import is_in_scope

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut)
def create_session(payload: SessionCreate, db: DBSession = Depends(get_db)):
    if not is_in_scope(payload.target_ip):
        raise HTTPException(
            status_code=403,
            detail="Target IP is outside the configured lab scope. Point this at your GNS3/Docker lab target.",
        )
    session = VaptSession(name=payload.name, target_ip=payload.target_ip)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("", response_model=list[SessionOut])
def list_sessions(db: DBSession = Depends(get_db)):
    return db.query(VaptSession).order_by(VaptSession.created_at.desc()).all()


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: int, db: DBSession = Depends(get_db)):
    return get_session_or_404(session_id, db)


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: int, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    db.delete(session)
    db.commit()
