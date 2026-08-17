"""Capstone challenge endpoints - the unguided final assessment that replaces
the post-session quiz.

The capstone target is a SECOND camera (a different weakness mix of the same
image) that the student attacks with no step-by-step guidance. Its IP is
supplied in the request body, not stored on the session, so this stays a
thin, migration-free addition. Like the guided scan endpoint, the scope
guardrail is enforced here before anything touches that IP.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.deps import get_session_or_404
from app.schemas import CapstoneAnswer, CapstoneRequest, CapstoneStatusUpdate
from app.services import capstone_engine, session_progress
from app.services.guardrail import assert_in_scope

router = APIRouter(prefix="/api/sessions", tags=["capstone"])


@router.post("/{session_id}/capstone/board")
def capstone_board(session_id: int, payload: CapstoneRequest, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    assert_in_scope(payload.capstone_target_ip)
    return capstone_engine.get_board(db, session, payload.capstone_target_ip)


@router.post("/{session_id}/capstone/{obj_id}/check")
def capstone_check(session_id: int, obj_id: str, payload: CapstoneRequest, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    assert_in_scope(payload.capstone_target_ip)
    try:
        return capstone_engine.check(db, session, payload.capstone_target_ip, obj_id)
    except capstone_engine.ObjectiveNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown objective '{obj_id}'.")
    except (capstone_engine.ObjectiveNotApplicableError, capstone_engine.WrongObjectiveTypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{session_id}/capstone/{obj_id}/submit")
def capstone_submit(session_id: int, obj_id: str, payload: CapstoneAnswer, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    assert_in_scope(payload.capstone_target_ip)
    try:
        return capstone_engine.submit(db, session, payload.capstone_target_ip, obj_id, payload.answer)
    except capstone_engine.ObjectiveNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown objective '{obj_id}'.")
    except (capstone_engine.ObjectiveNotApplicableError, capstone_engine.WrongObjectiveTypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{session_id}/capstone/status")
def capstone_status(session_id: int, payload: CapstoneStatusUpdate, db: DBSession = Depends(get_db)):
    """Record how the capstone ended: completed, gave_up (partial score kept),
    or skipped (not attempted). Needs no target contact, so it's not scope-gated."""
    session = get_session_or_404(session_id, db)
    try:
        state = session_progress.set_capstone_status(db, session.id, payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"capstone_status": state.capstone_status}
