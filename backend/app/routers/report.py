import json

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.deps import get_session_or_404
from app.models import Finding, QuizAttempt, ScanRun, SessionState
from app.schemas import FindingOut
from app.services import task_engine
from app.services.pdf_report import generate_report

router = APIRouter(prefix="/api/sessions", tags=["report"])


@router.get("/{session_id}/findings", response_model=list[FindingOut])
def get_findings(session_id: int, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    return db.query(Finding).filter_by(session_id=session.id).all()


@router.get("/{session_id}/report")
def get_report(session_id: int, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    severity_rank = {"High": 0, "Medium": 1, "Low": 2}
    findings = db.query(Finding).filter_by(session_id=session.id).all()
    findings.sort(key=lambda f: severity_rank.get(f.severity, 3))
    quiz_attempts = db.query(QuizAttempt).filter_by(session_id=session.id).order_by(QuizAttempt.created_at).all()
    not_applicable = task_engine.not_applicable_findings(session.target_ip)

    latest_scan_row = (
        db.query(ScanRun).filter_by(session_id=session.id).order_by(ScanRun.created_at.desc()).first()
    )
    scan = json.loads(latest_scan_row.result_json) if latest_scan_row else None

    state = db.get(SessionState, session.id)
    capstone_status = state.capstone_status if state else None

    pdf_bytes = generate_report(session, findings, quiz_attempts, not_applicable, scan, capstone_status)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="eduvapt_report_session_{session.id}.pdf"'},
    )
