"""Task-engine tests: the adaptive filtering (a hardened target gets a shorter
board), strict in-order locking, and answer validation. fetch_profile is
monkeypatched so no target needs to be running.
"""
from app.models import Finding, TaskProgress
from app.services import task_engine

FULL_PROFILE = {
    "http_default_creds_vulnerable": True,
    "snapshot_unauth_vulnerable": True,
    "telnet_enabled": True,
    "telnet_default_creds_vulnerable": True,
    "rtsp_enabled": True,
}

NO_TELNET_PROFILE = {**FULL_PROFILE, "telnet_enabled": False, "telnet_default_creds_vulnerable": False}


def _ids(tasks):
    return [t["id"] for t in tasks]


def test_full_profile_includes_every_weakness():
    ids = _ids(task_engine._applicable_tasks(FULL_PROFILE))
    assert "recon-telnet-port" in ids
    assert "telnet-default-creds" in ids
    assert "rtsp-banner" in ids
    assert "pattern-recognition" in ids


def test_hardened_target_drops_the_fixed_tasks():
    ids = _ids(task_engine._applicable_tasks(NO_TELNET_PROFILE))
    # Telnet weaknesses are gone...
    assert "recon-telnet-port" not in ids
    assert "telnet-default-creds" not in ids
    assert "telnet-flag" not in ids
    # ...but the still-present weaknesses remain.
    assert "recon-rtsp-port" in ids
    assert "http-default-creds" in ids


def test_first_task_unlocked_rest_locked(sample_session, db, monkeypatch):
    monkeypatch.setattr(task_engine, "fetch_profile", lambda ip: (FULL_PROFILE, None))
    board = task_engine.get_board(db, sample_session)
    assert board["tasks"][0]["locked"] is False
    assert board["tasks"][1]["locked"] is True


def test_correct_answer_completes_task_and_creates_finding(sample_session, db, monkeypatch):
    monkeypatch.setattr(task_engine, "fetch_profile", lambda ip: (FULL_PROFILE, None))

    wrong = task_engine.submit_answer(db, sample_session, "recon-telnet-port", "80")
    assert wrong["correct"] is False

    right = task_engine.submit_answer(db, sample_session, "recon-telnet-port", "23")
    assert right["correct"] is True

    progress = db.query(TaskProgress).filter_by(session_id=sample_session.id, task_id="recon-telnet-port").first()
    assert progress is not None and progress.completed is True

    finding = db.query(Finding).filter_by(session_id=sample_session.id, owasp_id="I2").first()
    assert finding is not None
    assert finding.mitigation  # OWASP mitigation text was attached


def test_locked_task_rejects_answer(sample_session, db, monkeypatch):
    monkeypatch.setattr(task_engine, "fetch_profile", lambda ip: (FULL_PROFILE, None))
    # Second task is locked until the first completes.
    res = task_engine.submit_answer(db, sample_session, "recon-rtsp-port", "554")
    assert res["correct"] is False
    assert "previous task" in res["error"].lower()
