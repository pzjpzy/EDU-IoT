"""Feedback + admin panel: submission validation, feedback surviving session
deletion (so the admin still sees it), admin login, and token-gated reads.
"""
import pytest

from app.models import Feedback, VaptSession
from app.routers.feedback import submit_feedback
from app.routers.sessions import delete_session
from app.schemas import FeedbackCreate
from app.services import admin_auth


def test_submit_feedback_stores_rating_and_suggestion(sample_session, db):
    submit_feedback(sample_session.id, FeedbackCreate(rating=4, suggestion="  nice  "), db)
    fb = db.query(Feedback).filter_by(session_id=sample_session.id).first()
    assert fb.rating == 4
    assert fb.suggestion == "nice"  # trimmed


def test_out_of_range_rating_rejected(sample_session, db):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        submit_feedback(sample_session.id, FeedbackCreate(rating=6), db)
    assert exc.value.status_code == 400


def test_feedback_survives_session_delete(db):
    s = VaptSession(name="temp", target_ip="127.0.0.1")
    db.add(s)
    db.commit()
    db.refresh(s)
    submit_feedback(s.id, FeedbackCreate(rating=5, suggestion="keep me"), db)

    delete_session(s.id, db)

    fb = db.query(Feedback).filter_by(suggestion="keep me").first()
    assert fb is not None  # not cascade-deleted
    assert fb.session_id is None  # detached from the removed session


def test_admin_login_and_token_gate(monkeypatch):
    monkeypatch.setattr(admin_auth, "ADMIN_PASSWORD", "letmein")
    with pytest.raises(PermissionError):
        admin_auth.login("wrong")
    token = admin_auth.login("letmein")

    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        admin_auth.require_admin(authorization=None)
    with pytest.raises(HTTPException):
        admin_auth.require_admin(authorization="Bearer not-a-real-token")
    # A valid token passes (returns None, raises nothing).
    assert admin_auth.require_admin(authorization=f"Bearer {token}") is None
