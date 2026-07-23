from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.deps import get_session_or_404
from app.services import task_engine

router = APIRouter(prefix="/api/sessions", tags=["tasks"])


class AnswerSubmit(BaseModel):
    answer: str


@router.get("/{session_id}/tasks")
def list_tasks(session_id: int, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    return task_engine.get_task_list(db, session)


@router.post("/{session_id}/tasks/{task_id}/check")
def check_task(session_id: int, task_id: str, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    try:
        return task_engine.check_auto_task(db, session, task_id)
    except task_engine.TaskNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown task '{task_id}'.")
    except task_engine.WrongTaskTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{session_id}/tasks/{task_id}/submit")
def submit_task(session_id: int, task_id: str, payload: AnswerSubmit, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    try:
        return task_engine.submit_answer(db, session, task_id, payload.answer)
    except task_engine.TaskNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown task '{task_id}'.")
    except task_engine.WrongTaskTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
