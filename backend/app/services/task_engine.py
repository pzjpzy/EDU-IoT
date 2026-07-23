"""Drives the HTB/TryHackMe-style guided task board.

Students do the actual scanning/exploitation themselves with their own
tools, against the session's target IP. This engine only tracks progress:

- "auto" tasks are confirmed by polling the target's own `/eduvapt/status`
  endpoint (see target/app/events.py) - the target self-reports when a
  vulnerable action has actually been triggered, so no student input is
  needed.
- "submit" tasks are confirmed by comparing a student-typed answer/flag
  against the accepted value(s), case-insensitively.

Tasks unlock strictly in order. Completing a task also creates a Finding
row (OWASP-mapped) that feeds the session's PDF report.
"""
import datetime

import requests
from sqlalchemy.orm import Session as DBSession

from app.content_loader import load_yaml
from app.models import Finding, TaskProgress, VaptSession
from app.services.owasp_reference import mitigation

TASKS: list[dict] = load_yaml("tasks.yaml")
TASKS_BY_ID = {t["id"]: t for t in TASKS}

TARGET_STATUS_TIMEOUT_SECONDS = 3


class TaskNotFoundError(ValueError):
    pass


class WrongTaskTypeError(ValueError):
    pass


def _progress_map(db: DBSession, session_id: int) -> dict[str, TaskProgress]:
    rows = db.query(TaskProgress).filter_by(session_id=session_id).all()
    return {r.task_id: r for r in rows}


def get_task_list(db: DBSession, session: VaptSession) -> list[dict]:
    progress = _progress_map(db, session.id)
    result = []
    prev_completed = True
    for task in TASKS:
        completed = bool(progress.get(task["id"]) and progress[task["id"]].completed)
        result.append(
            {
                "id": task["id"],
                "title": task["title"],
                "type": task["type"],
                "prompt": task["prompt"],
                "hint": task.get("hint"),
                "owasp_id": task["owasp_id"],
                "completed": completed,
                "locked": (not prev_completed) and not completed,
            }
        )
        prev_completed = completed
    return result


def _complete_task(db: DBSession, session: VaptSession, task: dict) -> None:
    row = db.query(TaskProgress).filter_by(session_id=session.id, task_id=task["id"]).first()
    if row and row.completed:
        return
    if not row:
        row = TaskProgress(session_id=session.id, task_id=task["id"])
        db.add(row)
    row.completed = True
    row.completed_at = datetime.datetime.utcnow()
    db.add(
        Finding(
            session_id=session.id,
            owasp_id=task["owasp_id"],
            title=task["finding_title"],
            severity=task["severity"],
            evidence=task["evidence"],
            mitigation=mitigation(task["owasp_id"]),
        )
    )
    db.commit()


def _is_unlocked(db: DBSession, session: VaptSession, task_id: str) -> bool:
    tasks = get_task_list(db, session)
    return next((t for t in tasks if t["id"] == task_id), {"locked": True})["locked"] is False


def check_auto_task(db: DBSession, session: VaptSession, task_id: str) -> dict:
    task = TASKS_BY_ID.get(task_id)
    if not task:
        raise TaskNotFoundError(task_id)
    if task["type"] != "auto":
        raise WrongTaskTypeError(f"Task {task_id} is not an auto-detected task.")
    if not _is_unlocked(db, session, task_id):
        return {"completed": False, "error": "Complete the previous task first."}

    if task["check_event"] == "__all_previous_complete__":
        idx = TASKS.index(task)
        prior_ids = [t["id"] for t in TASKS[:idx]]
        completed_ids = {
            r.task_id for r in db.query(TaskProgress).filter_by(session_id=session.id, completed=True).all()
        }
        triggered = all(pid in completed_ids for pid in prior_ids)
        if triggered:
            _complete_task(db, session, task)
        return {"completed": triggered}

    try:
        resp = requests.get(
            f"http://{session.target_ip}/eduvapt/status", timeout=TARGET_STATUS_TIMEOUT_SECONDS
        )
        resp.raise_for_status()
        events = resp.json()
    except requests.RequestException as exc:
        return {"completed": False, "error": f"Could not reach target status endpoint: {exc}"}

    triggered = bool(events.get(task["check_event"]))
    if triggered:
        _complete_task(db, session, task)
    return {"completed": triggered}


def submit_answer(db: DBSession, session: VaptSession, task_id: str, answer: str) -> dict:
    task = TASKS_BY_ID.get(task_id)
    if not task:
        raise TaskNotFoundError(task_id)
    if task["type"] != "submit":
        raise WrongTaskTypeError(f"Task {task_id} does not accept submitted answers.")
    if not _is_unlocked(db, session, task_id):
        return {"correct": False, "error": "Complete the previous task first."}

    normalized = answer.strip().lower()
    accepted = {a.strip().lower() for a in task["answer"]}
    correct = normalized in accepted
    if correct:
        _complete_task(db, session, task)
    return {"correct": correct}
