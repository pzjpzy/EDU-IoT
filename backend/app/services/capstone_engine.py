"""Capstone challenge engine - the unguided final assessment that replaces
the post-session quiz.

Where services/task_engine.py drives the *guided* room (ordered tasks, with
concept text and hints, each completion creating an OWASP-mapped report
Finding), the capstone is the opposite by design:

  - It runs against a SECOND target IP the student hasn't been walked through
    (the same camera image with a different weakness mix - see
    capstone/docker-compose.yml), passed in per request.
  - Every applicable objective is unlocked at once and exposes only a
    one-line goal: no ordering, no hints, no concept panels.
  - Completing an objective creates NO Finding - the capstone doesn't feed
    the pentest report; it measures whether the student can independently
    reproduce what they learned.
  - The number of objectives completed is recorded as a QuizAttempt with
    phase="capstone", which is the learning-effectiveness signal objective 4
    needs and which the PDF report already renders generically.

Which objectives apply is still adaptive: each objective's `requires` list is
checked against the capstone target's self-declared profile, exactly like the
guided board, so this one content file fits any weakness mix.

Progress is persisted in TaskProgress under "cap:"-prefixed task ids so it
never collides with the guided run's rows for the same session.
"""
import datetime
import json

import requests
from sqlalchemy.orm import Session as DBSession

from app.content_loader import load_yaml
from app.models import QuizAttempt, TaskProgress, VaptSession
from app.services.target_profile import fetch_profile

OBJECTIVES: list[dict] = load_yaml("capstone.yaml")
OBJECTIVES_BY_ID = {o["id"]: o for o in OBJECTIVES}

TARGET_STATUS_TIMEOUT_SECONDS = 3
_PREFIX = "cap:"  # namespaces capstone progress rows apart from guided ones


class ObjectiveNotFoundError(ValueError):
    pass


class WrongObjectiveTypeError(ValueError):
    pass


class ObjectiveNotApplicableError(ValueError):
    pass


def _applicable(profile: dict) -> list[dict]:
    return [o for o in OBJECTIVES if all(profile.get(flag, False) for flag in o.get("requires", []))]


def _completed_ids(db: DBSession, session_id: int) -> set[str]:
    rows = db.query(TaskProgress).filter_by(session_id=session_id, completed=True).all()
    return {r.task_id[len(_PREFIX):] for r in rows if r.task_id.startswith(_PREFIX)}


def _mark_complete(db: DBSession, session: VaptSession, obj_id: str) -> None:
    pid = _PREFIX + obj_id
    row = db.query(TaskProgress).filter_by(session_id=session.id, task_id=pid).first()
    if row and row.completed:
        return
    if not row:
        row = TaskProgress(session_id=session.id, task_id=pid)
        db.add(row)
    row.completed = True
    row.completed_at = datetime.datetime.utcnow()
    # The session uses autoflush=False, so flush the new/updated row now to
    # make it visible to the score recompute that reads it back immediately.
    db.flush()


def _sync_score(db: DBSession, session: VaptSession, applicable: list[dict]) -> tuple[int, int]:
    """Recompute the capstone score from persisted progress and store it as a
    single QuizAttempt(phase="capstone") so the report picks it up. Only
    objectives that both apply to this target and are completed count."""
    applicable_ids = {o["id"] for o in applicable}
    done = _completed_ids(db, session.id) & applicable_ids
    score, total = len(done), len(applicable_ids)
    db.query(QuizAttempt).filter_by(session_id=session.id, phase="capstone").delete()
    db.add(
        QuizAttempt(
            session_id=session.id,
            phase="capstone",
            answers_json=json.dumps(sorted(done)),
            score=score,
            total=total,
        )
    )
    db.commit()
    return score, total


def get_board(db: DBSession, session: VaptSession, capstone_ip: str) -> dict:
    profile, warning = fetch_profile(capstone_ip)
    applicable = _applicable(profile)
    done = _completed_ids(db, session.id)
    score, total = _sync_score(db, session, applicable)
    objectives = [
        {
            "id": o["id"],
            "title": o["title"],
            "type": o["type"],
            "owasp_id": o["owasp_id"],
            "completed": o["id"] in done,
        }
        for o in applicable
    ]
    return {
        "objectives": objectives,
        "profile": profile,
        "warning": warning,
        "score": score,
        "total": total,
    }


def _require_applicable(session_ip_profile: dict, obj_id: str) -> dict:
    applicable = _applicable(session_ip_profile)
    obj = next((o for o in applicable if o["id"] == obj_id), None)
    if obj is None:
        raise ObjectiveNotApplicableError(
            f"Objective '{obj_id}' doesn't apply to the capstone target (the relevant weakness isn't present)."
        )
    return obj


def check(db: DBSession, session: VaptSession, capstone_ip: str, obj_id: str) -> dict:
    obj = OBJECTIVES_BY_ID.get(obj_id)
    if not obj:
        raise ObjectiveNotFoundError(obj_id)
    if obj["type"] != "auto":
        raise WrongObjectiveTypeError(f"Objective {obj_id} is not an auto-detected objective.")

    profile, _ = fetch_profile(capstone_ip)
    _require_applicable(profile, obj_id)

    try:
        resp = requests.get(
            f"http://{capstone_ip}/eduvapt/status", timeout=TARGET_STATUS_TIMEOUT_SECONDS
        )
        resp.raise_for_status()
        events = resp.json()
    except requests.RequestException as exc:
        return {"completed": False, "error": f"Could not reach capstone target status endpoint: {exc}"}

    triggered = bool(events.get(obj["check_event"]))
    if triggered:
        _mark_complete(db, session, obj_id)
        _sync_score(db, session, _applicable(profile))
    return {"completed": triggered}


def submit(db: DBSession, session: VaptSession, capstone_ip: str, obj_id: str, answer: str) -> dict:
    obj = OBJECTIVES_BY_ID.get(obj_id)
    if not obj:
        raise ObjectiveNotFoundError(obj_id)
    if obj["type"] != "submit":
        raise WrongObjectiveTypeError(f"Objective {obj_id} does not accept a submitted answer.")

    profile, _ = fetch_profile(capstone_ip)
    _require_applicable(profile, obj_id)

    normalized = answer.strip().lower()
    accepted = {a.strip().lower() for a in obj["answer"]}
    correct = normalized in accepted
    if correct:
        _mark_complete(db, session, obj_id)
        _sync_score(db, session, _applicable(profile))
    return {"correct": correct}
