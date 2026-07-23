import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from app.content_loader import load_yaml
from app.database import get_db
from app.deps import get_session_or_404
from app.models import QuizAttempt
from app.schemas import QuizResult, QuizSubmit

router = APIRouter(tags=["quiz"])

QUIZ_BANK = load_yaml("quiz_bank.yaml")
_BY_ID = {q["id"]: q for q in QUIZ_BANK}


@router.get("/api/quiz/questions")
def get_quiz_questions():
    return [{"id": q["id"], "question": q["question"], "options": q["options"]} for q in QUIZ_BANK]


@router.post("/api/sessions/{session_id}/quiz", response_model=QuizResult)
def submit_quiz(session_id: int, payload: QuizSubmit, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)

    breakdown = []
    score = 0
    for ans in payload.answers:
        question = _BY_ID.get(ans.question_id)
        if not question:
            continue
        correct = ans.selected_index == question["answer_index"]
        if correct:
            score += 1
        breakdown.append(
            {
                "question_id": ans.question_id,
                "correct": correct,
                "correct_answer_index": question["answer_index"],
            }
        )

    total = len(QUIZ_BANK)

    db.query(QuizAttempt).filter_by(session_id=session.id, phase=payload.phase).delete()
    db.add(
        QuizAttempt(
            session_id=session.id,
            phase=payload.phase,
            answers_json=json.dumps([a.model_dump() for a in payload.answers]),
            score=score,
            total=total,
        )
    )
    db.commit()

    return QuizResult(phase=payload.phase, score=score, total=total, breakdown=breakdown)


@router.get("/api/sessions/{session_id}/quiz", response_model=list[QuizResult])
def get_quiz_results(session_id: int, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    attempts = db.query(QuizAttempt).filter_by(session_id=session.id).all()
    return [QuizResult(phase=a.phase, score=a.score, total=a.total, breakdown=[]) for a in attempts]
