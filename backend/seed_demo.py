"""Seed the database with tagged demo data so the dashboard's analytics strip
(CCTV-scanned-this-month, quiz-accuracy donut, vulnerability bar chart) has
something to show without running full sessions by hand.

Every row hangs off a session whose name starts with "[demo]", so re-running
this script first deletes the previous demo data (ORM cascade removes the
demo sessions' scans, findings, and quiz attempts) and nothing real is touched.

    cd backend
    ./.venv/Scripts/python.exe seed_demo.py        # Windows
    python seed_demo.py                            # anywhere else

Delete it again at any time with:  ./.venv/Scripts/python.exe seed_demo.py --clear
"""
import datetime as dt
import json
import sys

from app.database import Base, SessionLocal, engine
from app.models import Finding, QuizAttempt, ScanRun, VaptSession

Base.metadata.create_all(bind=engine)

DEMO_PREFIX = "[demo]"

# (name, target_ip) - distinct IPs so "CCTV scanned this month" counts them apart.
DEMO_TARGETS = [
    ("[demo] CAM-01 lobby", "127.0.0.1"),
    ("[demo] CAM-02 carpark", "192.168.56.50"),
    ("[demo] CAM-03 entrance", "192.168.56.51"),
    ("[demo] DVR-lab", "10.0.0.20"),
    ("[demo] CAM-04 warehouse", "172.16.5.5"),
]

# Findings scattered across time (days ago) with a severity each - populates the
# day (<=7d), week (<=8w) and month (<=6mo) toggle views.
FINDING_SPREAD = [
    (0, "High"), (0, "Low"), (1, "Medium"), (2, "High"), (3, "Low"),
    (4, "Medium"), (5, "High"), (6, "Low"),
    (9, "High"), (12, "Medium"), (16, "Low"), (20, "High"), (26, "Medium"),
    (34, "Low"), (41, "High"), (52, "Medium"), (63, "High"), (75, "Low"),
    (95, "Medium"), (120, "High"), (150, "Low"), (165, "Medium"),
]

# (pre_score/12, capstone_score/4) attempts -> overall accuracy for the donut.
QUIZ_ATTEMPTS = [("pre", 9, 12), ("capstone", 3, 4), ("pre", 10, 12),
                 ("capstone", 4, 4), ("pre", 8, 12)]


def _clear(db) -> int:
    demo = db.query(VaptSession).filter(VaptSession.name.like(f"{DEMO_PREFIX}%")).all()
    for s in demo:
        db.delete(s)  # ORM cascade removes children
    db.commit()
    return len(demo)


def main() -> None:
    db = SessionLocal()
    try:
        removed = _clear(db)
        if "--clear" in sys.argv:
            print(f"Cleared {removed} demo session(s).")
            return

        now = dt.datetime.utcnow()
        sessions = []
        for i, (name, ip) in enumerate(DEMO_TARGETS):
            s = VaptSession(name=name, target_ip=ip, created_at=now - dt.timedelta(days=3 * i))
            db.add(s)
            sessions.append(s)
        db.commit()
        for s in sessions:
            db.refresh(s)

        # Scans this month across the distinct targets (plus a repeat scan of the
        # first IP to prove the DISTINCT count treats it as one camera).
        for i, s in enumerate(sessions):
            db.add(ScanRun(session_id=s.id, target_ip=s.target_ip, in_scope=True,
                           open_port_count=3, result_json=json.dumps({"summary": "demo"}),
                           created_at=now - dt.timedelta(days=i)))
        db.add(ScanRun(session_id=sessions[0].id, target_ip=sessions[0].target_ip, in_scope=True,
                       open_port_count=3, result_json=json.dumps({"summary": "demo repeat"}),
                       created_at=now - dt.timedelta(days=1)))

        # Findings spread over time, round-robined across the demo sessions.
        owasp = {"High": "I1", "Medium": "I2", "Low": "I5"}
        for j, (days_ago, sev) in enumerate(FINDING_SPREAD):
            s = sessions[j % len(sessions)]
            db.add(Finding(
                session_id=s.id, owasp_id=owasp[sev],
                title=f"[demo] {sev} finding", severity=sev,
                evidence="Seeded demo evidence.", mitigation="Seeded demo mitigation.",
                created_at=now - dt.timedelta(days=days_ago),
            ))

        # Quiz attempts feeding the accuracy donut.
        for k, (phase, score, total) in enumerate(QUIZ_ATTEMPTS):
            s = sessions[k % len(sessions)]
            db.add(QuizAttempt(session_id=s.id, phase=phase, answers_json="[]",
                               score=score, total=total,
                               created_at=now - dt.timedelta(days=k)))

        db.commit()

        correct = sum(a[1] for a in QUIZ_ATTEMPTS)
        tot = sum(a[2] for a in QUIZ_ATTEMPTS)
        print(f"Seeded {len(sessions)} demo sessions, {len(FINDING_SPREAD)} findings, "
              f"{len(QUIZ_ATTEMPTS)} quiz attempts.")
        print(f"Distinct CCTV scanned this month: {len({t[1] for t in DEMO_TARGETS})}")
        print(f"Quiz accuracy: {correct}/{tot} = {round(correct / tot * 100)}%")
    finally:
        db.close()


if __name__ == "__main__":
    main()
