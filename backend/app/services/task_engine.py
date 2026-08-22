"""Drives the HTB/TryHackMe-style guided task board.

Students do the actual scanning/exploitation themselves with their own
tools, against the session's target IP. This engine only tracks progress:

- "auto" tasks are confirmed by polling the target's own `/eduvapt/status`
  endpoint (see target/app/events.py) - the target self-reports when a
  vulnerable action has actually been triggered, so no student input is
  needed.
- "submit" tasks are confirmed by comparing a student-typed answer/flag
  against the accepted value(s), case-insensitively.

Which tasks even apply is itself adaptive: each task's `requires` list
(content/tasks.yaml) names target-profile flags that must all be true (see
target/app/vuln_config.py + services/target_profile.py). A target that's
had some weaknesses fixed - e.g. target-hardened/ - simply gets a shorter,
different task board and report, without any code here needing to know
about specific target variants.

Tasks unlock strictly in order within the applicable set. Completing a task
also creates a Finding row (OWASP-mapped) that feeds the session's PDF
report.
"""
import datetime

import requests
from sqlalchemy.orm import Session as DBSession

from app.content_loader import load_yaml
from app.models import Finding, TaskProgress, VaptSession
from app.services.owasp_reference import mitigation
from app.services.target_profile import fetch_profile

TASKS: list[dict] = load_yaml("tasks.yaml")
TASKS_BY_ID = {t["id"]: t for t in TASKS}

TARGET_STATUS_TIMEOUT_SECONDS = 3


class TaskNotFoundError(ValueError):
    pass


class WrongTaskTypeError(ValueError):
    pass


class TaskNotApplicableError(ValueError):
    pass


def _applicable_tasks(profile: dict) -> list[dict]:
    filtered = [t for t in TASKS if all(profile.get(flag, False) for flag in t.get("requires", []))]
    # The wrap-up task is only meaningful if at least one real weakness was
    # found - drop it too on a (hypothetically) fully-hardened target.
    if all(t["id"] == "pattern-recognition" for t in filtered):
        return []
    return filtered


def _progress_map(db: DBSession, session_id: int) -> dict[str, TaskProgress]:
    rows = db.query(TaskProgress).filter_by(session_id=session_id).all()
    return {r.task_id: r for r in rows}


def _task_states(db: DBSession, session: VaptSession, applicable: list[dict]) -> list[dict]:
    """Each applicable task plus its completed/locked state, in order."""
    progress = _progress_map(db, session.id)
    states = []
    prev_completed = True
    for task in applicable:
        completed = bool(progress.get(task["id"]) and progress[task["id"]].completed)
        states.append({"task": task, "completed": completed, "locked": (not prev_completed) and not completed})
        prev_completed = completed
    return states


def get_board(db: DBSession, session: VaptSession) -> dict:
    profile, warning = fetch_profile(session.target_ip)
    applicable = _applicable_tasks(profile)
    states = _task_states(db, session, applicable)

    tasks = [
        {
            "id": s["task"]["id"],
            "title": f"Task {i + 1} - {s['task']['title']}",
            "type": s["task"]["type"],
            "concept": s["task"].get("concept"),
            "prompt": s["task"]["prompt"],
            "hint": s["task"].get("hint"),
            "owasp_id": s["task"]["owasp_id"],
            "completed": s["completed"],
            "locked": s["locked"],
        }
        for i, s in enumerate(states)
    ]
    return {"tasks": tasks, "profile": profile, "warning": warning}


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


def _lookup_applicable(db: DBSession, session: VaptSession, task_id: str) -> dict:
    """Raises TaskNotApplicableError if the task doesn't apply to this
    session's target at all, else returns its current {task, completed,
    locked} state."""
    profile, _ = fetch_profile(session.target_ip)
    applicable = _applicable_tasks(profile)
    states = _task_states(db, session, applicable)
    state = next((s for s in states if s["task"]["id"] == task_id), None)
    if state is None:
        raise TaskNotApplicableError(
            f"Task '{task_id}' doesn't apply to this target (the relevant weakness isn't present)."
        )
    return state


def check_auto_task(db: DBSession, session: VaptSession, task_id: str) -> dict:
    task = TASKS_BY_ID.get(task_id)
    if not task:
        raise TaskNotFoundError(task_id)
    if task["type"] != "auto":
        raise WrongTaskTypeError(f"Task {task_id} is not an auto-detected task.")

    state = _lookup_applicable(db, session, task_id)
    if state["locked"]:
        return {"completed": False, "error": "Complete the previous task first."}

    if task["check_event"] == "__all_previous_complete__":
        profile, _ = fetch_profile(session.target_ip)
        applicable_ids = [t["id"] for t in _applicable_tasks(profile) if t["id"] != task_id]
        completed_ids = {
            r.task_id for r in db.query(TaskProgress).filter_by(session_id=session.id, completed=True).all()
        }
        triggered = all(tid in completed_ids for tid in applicable_ids)
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

    state = _lookup_applicable(db, session, task_id)
    if state["locked"]:
        return {"correct": False, "error": "Complete the previous task first."}

    normalized = answer.strip().lower()
    accepted = {a.strip().lower() for a in task["answer"]}
    correct = normalized in accepted
    if correct:
        _complete_task(db, session, task)
    return {"correct": correct}


def challenge_accuracy(db: DBSession, session: VaptSession) -> tuple[int, int]:
    """(completed, total) for the guided challenges that apply to this target -
    the "with guidance" figure the report compares against the unguided
    capstone. Capstone progress rows (cap:-prefixed) are naturally excluded
    because their ids never appear in the applicable task set."""
    profile, _ = fetch_profile(session.target_ip)
    applicable_ids = {t["id"] for t in _applicable_tasks(profile)}
    if not applicable_ids:
        return 0, 0
    completed = {
        r.task_id
        for r in db.query(TaskProgress).filter_by(session_id=session.id, completed=True).all()
    }
    return len(applicable_ids & completed), len(applicable_ids)


def not_applicable_findings(target_ip: str) -> list[dict]:
    """Tasks that don't apply to this target - i.e. weaknesses that were
    checked for but aren't present - for the report's "tested but not
    found" section."""
    profile, _ = fetch_profile(target_ip)
    applicable_ids = {t["id"] for t in _applicable_tasks(profile)}
    seen_owasp_titles = set()
    result = []
    for task in TASKS:
        if task["id"] in applicable_ids:
            continue
        key = (task["owasp_id"], task["finding_title"])
        if key in seen_owasp_titles:
            continue
        seen_owasp_titles.add(key)
        result.append({"owasp_id": task["owasp_id"], "title": task["finding_title"]})
    return result
