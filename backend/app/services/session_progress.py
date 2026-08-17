"""Read/update per-session UI progress (SessionState) plus the end-of-session
summary the dashboard renders.

Kept as plain helpers so both the sessions router (progress + summary) and the
capstone router (marking how the capstone ended) share one implementation.
"""
from sqlalchemy.orm import Session as DBSession

from app.models import Finding, QuizAttempt, ScanRun, SessionState, VaptSession

SUMMARY_PHASE = 5  # the final "summary/complete" step index
_CAPSTONE_STATUSES = {"completed", "gave_up", "skipped"}


def get_or_create(db: DBSession, session_id: int) -> SessionState:
    state = db.get(SessionState, session_id)
    if state is None:
        state = SessionState(session_id=session_id, furthest_phase=0)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


def bump_phase(db: DBSession, session_id: int, phase: int) -> SessionState:
    """Advance the furthest-reached phase (never rewinds it)."""
    state = get_or_create(db, session_id)
    if phase > state.furthest_phase:
        state.furthest_phase = phase
        db.commit()
    return state


def set_capstone_status(db: DBSession, session_id: int, status: str) -> SessionState:
    if status not in _CAPSTONE_STATUSES:
        raise ValueError(f"Unknown capstone status '{status}'.")
    state = get_or_create(db, session_id)
    state.capstone_status = status
    if SUMMARY_PHASE > state.furthest_phase:
        state.furthest_phase = SUMMARY_PHASE
    db.commit()
    return state


def build_summary(db: DBSession, session: VaptSession) -> dict:
    """The end-of-session dashboard payload: pre-quiz accuracy, vulnerability
    tally by severity, capstone outcome, and how far the student progressed."""
    state = get_or_create(db, session.id)

    pre = (
        db.query(QuizAttempt)
        .filter_by(session_id=session.id, phase="pre")
        .order_by(QuizAttempt.created_at.desc())
        .first()
    )
    pre_quiz = {"score": pre.score, "total": pre.total} if pre else None

    counts = {"High": 0, "Medium": 0, "Low": 0}
    for f in db.query(Finding).filter_by(session_id=session.id).all():
        if f.severity in counts:
            counts[f.severity] += 1
    findings_total = sum(counts.values())

    cap_attempt = db.query(QuizAttempt).filter_by(session_id=session.id, phase="capstone").first()
    if state.capstone_status:
        cap_status = state.capstone_status
    elif cap_attempt:
        cap_status = "in_progress"
    else:
        cap_status = "not_started"
    capstone = {
        "status": cap_status,
        "score": cap_attempt.score if cap_attempt else None,
        "total": cap_attempt.total if cap_attempt else None,
    }

    has_scan = db.query(ScanRun).filter_by(session_id=session.id).first() is not None

    return {
        "furthest_phase": state.furthest_phase,
        "pre_quiz": pre_quiz,
        "recon_done": has_scan,
        "findings_by_severity": counts,
        "findings_total": findings_total,
        "capstone": capstone,
    }
