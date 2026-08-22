"""Dashboard stats: distinct-target CCTV count (same IP counts once), global
quiz accuracy, all-time vuln count, and severity bucketing per granularity.
"""
import datetime as dt

import pytest

from app.models import Finding, QuizAttempt, ScanRun, VaptSession
from app.services import stats


@pytest.fixture
def demo_session(db):
    s = VaptSession(name="stats-test", target_ip="127.0.0.1")
    db.add(s)
    db.commit()
    db.refresh(s)
    yield s
    db.delete(s)
    db.commit()


def test_cctv_scanned_counts_distinct_ips(demo_session, db):
    now = dt.datetime.utcnow()
    # Same IP scanned twice = one camera; a second IP = a second camera.
    db.add(ScanRun(session_id=demo_session.id, target_ip="127.0.0.1", in_scope=True,
                   open_port_count=1, result_json="{}", created_at=now))
    db.add(ScanRun(session_id=demo_session.id, target_ip="127.0.0.1", in_scope=True,
                   open_port_count=1, result_json="{}", created_at=now))
    db.add(ScanRun(session_id=demo_session.id, target_ip="192.168.56.50", in_scope=True,
                   open_port_count=1, result_json="{}", created_at=now))
    db.commit()
    assert stats.overview(db)["cctv_scanned_this_month"] == 2


def test_quiz_accuracy_is_global_sum(demo_session, db):
    db.add(QuizAttempt(session_id=demo_session.id, phase="pre", answers_json="[]", score=9, total=12))
    db.add(QuizAttempt(session_id=demo_session.id, phase="capstone", answers_json="[]", score=3, total=4))
    db.commit()
    acc = stats.overview(db)["quiz_accuracy"]
    assert acc["correct"] == 12 and acc["total"] == 16
    assert acc["pct"] == 75


def test_vuln_series_buckets_by_severity(demo_session, db):
    now = dt.datetime.utcnow()
    db.add(Finding(session_id=demo_session.id, owasp_id="I1", title="a", severity="High",
                   evidence="e", mitigation="m", created_at=now))
    db.add(Finding(session_id=demo_session.id, owasp_id="I2", title="b", severity="High",
                   evidence="e", mitigation="m", created_at=now))
    db.add(Finding(session_id=demo_session.id, owasp_id="I5", title="c", severity="Low",
                   evidence="e", mitigation="m", created_at=now))
    db.commit()
    series = stats.vuln_series(db, "day")
    assert len(series) == 7  # last 7 days
    today = series[-1]
    assert today["High"] == 2 and today["Low"] == 1 and today["Medium"] == 0


def test_unknown_granularity_rejected(db):
    with pytest.raises(ValueError):
        stats.vuln_series(db, "century")
