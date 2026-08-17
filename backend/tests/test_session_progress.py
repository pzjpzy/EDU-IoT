"""Session-progress tests: furthest-phase never rewinds, capstone status
validation, and the end-of-session summary payload (quiz accuracy,
vulnerability tally by severity, capstone outcome).
"""
import pytest

from app.models import Finding, QuizAttempt
from app.services import session_progress as sp


def test_bump_phase_only_moves_forward(sample_session, db):
    sp.bump_phase(db, sample_session.id, 3)
    sp.bump_phase(db, sample_session.id, 1)  # must not rewind
    state = sp.get_or_create(db, sample_session.id)
    assert state.furthest_phase == 3


def test_capstone_status_validated_and_advances(sample_session, db):
    with pytest.raises(ValueError):
        sp.set_capstone_status(db, sample_session.id, "bogus")
    state = sp.set_capstone_status(db, sample_session.id, "gave_up")
    assert state.capstone_status == "gave_up"
    assert state.furthest_phase == sp.SUMMARY_PHASE  # ending the capstone reaches the summary


def test_summary_tallies_quiz_and_findings(sample_session, db):
    db.add(QuizAttempt(session_id=sample_session.id, phase="pre", answers_json="[]", score=4, total=6))
    db.add(Finding(session_id=sample_session.id, owasp_id="I1", title="a", severity="High", evidence="e", mitigation="m"))
    db.add(Finding(session_id=sample_session.id, owasp_id="I3", title="b", severity="Low", evidence="e", mitigation="m"))
    db.add(QuizAttempt(session_id=sample_session.id, phase="capstone", answers_json="[]", score=2, total=4))
    db.commit()

    summary = sp.build_summary(db, sample_session)
    assert summary["pre_quiz"] == {"score": 4, "total": 6}
    assert summary["findings_by_severity"] == {"High": 1, "Medium": 0, "Low": 1}
    assert summary["findings_total"] == 2
    assert summary["capstone"]["score"] == 2 and summary["capstone"]["total"] == 4
    # No explicit status set yet, but a capstone attempt exists -> in progress.
    assert summary["capstone"]["status"] == "in_progress"


def test_summary_defaults_on_empty_session(sample_session, db):
    summary = sp.build_summary(db, sample_session)
    assert summary["furthest_phase"] == 0
    assert summary["pre_quiz"] is None
    assert summary["findings_total"] == 0
    assert summary["capstone"]["status"] == "not_started"
