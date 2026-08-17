"""Capstone-engine tests: adaptive objective filtering against the capstone
target's profile, unguided all-unlocked behaviour, flag validation, no report
Findings created, and the score recorded as a QuizAttempt(phase="capstone").
fetch_profile is monkeypatched so no capstone target needs to be running.
"""
from app.models import Finding, QuizAttempt
from app.services import capstone_engine

# The default capstone mix (capstone/docker-compose.yml): HTTP default creds
# FIXED, everything else still vulnerable.
CAPSTONE_PROFILE = {
    "http_default_creds_vulnerable": False,
    "snapshot_unauth_vulnerable": True,
    "telnet_enabled": True,
    "telnet_default_creds_vulnerable": True,
    "rtsp_enabled": True,
}

CAP_IP = "127.0.0.2"


def _ids(objs):
    return [o["id"] for o in objs]


def test_applicable_drops_fixed_http_objectives():
    ids = _ids(capstone_engine._applicable(CAPSTONE_PROFILE))
    # HTTP default-cred path is fixed on the capstone target...
    assert "cap-http-login" not in ids
    assert "cap-http-flag" not in ids
    # ...but the remaining weaknesses are all present.
    assert "cap-snapshot" in ids
    assert "cap-telnet-login" in ids
    assert "cap-telnet-flag" in ids
    assert "cap-rtsp" in ids


def test_board_objectives_carry_no_hints(sample_session, db, monkeypatch):
    monkeypatch.setattr(capstone_engine, "fetch_profile", lambda ip: (CAPSTONE_PROFILE, None))
    board = capstone_engine.get_board(db, sample_session, CAP_IP)
    assert board["total"] == 4
    assert board["score"] == 0
    # Unguided: only the goal is exposed, never concept/hint/prompt.
    for obj in board["objectives"]:
        assert set(obj.keys()) == {"id", "title", "type", "owasp_id", "completed"}


def test_correct_flag_scores_without_creating_a_finding(sample_session, db, monkeypatch):
    monkeypatch.setattr(capstone_engine, "fetch_profile", lambda ip: (CAPSTONE_PROFILE, None))

    wrong = capstone_engine.submit(db, sample_session, CAP_IP, "cap-rtsp", "nope")
    assert wrong["correct"] is False

    right = capstone_engine.submit(db, sample_session, CAP_IP, "cap-rtsp", "IoT-Cam-RTSP")
    assert right["correct"] is True

    # The capstone measures learning; it must NOT pollute the pentest report.
    assert db.query(Finding).filter_by(session_id=sample_session.id).count() == 0

    # Score is persisted as a QuizAttempt(phase="capstone") for the report.
    attempt = db.query(QuizAttempt).filter_by(session_id=sample_session.id, phase="capstone").first()
    assert attempt is not None
    assert attempt.score == 1
    assert attempt.total == 4


def test_objective_not_applicable_is_rejected(sample_session, db, monkeypatch):
    monkeypatch.setattr(capstone_engine, "fetch_profile", lambda ip: (CAPSTONE_PROFILE, None))
    # cap-http-flag doesn't apply (HTTP creds fixed on this target).
    try:
        capstone_engine.submit(db, sample_session, CAP_IP, "cap-http-flag", "whatever")
    except capstone_engine.ObjectiveNotApplicableError:
        pass
    else:
        raise AssertionError("expected ObjectiveNotApplicableError")
