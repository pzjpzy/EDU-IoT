import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.content_loader import load_yaml
from app.database import get_db
from app.deps import get_session_or_404
from app.models import Finding, ScanResult
from app.schemas import FindingOut, VulnResponse
from app.services.owasp_mapping import derive_findings_from_recon

router = APIRouter(prefix="/api/sessions", tags=["vuln"])

STAGES = load_yaml("stages.yaml")


@router.post("/{session_id}/vuln", response_model=VulnResponse)
def run_vuln(session_id: int, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)

    recon_result = (
        db.query(ScanResult)
        .filter_by(session_id=session.id, stage="recon")
        .order_by(ScanResult.created_at.desc())
        .first()
    )
    if not recon_result:
        raise HTTPException(status_code=400, detail="Run the Recon stage first.")

    ports = json.loads(recon_result.raw_json)["ports"]
    derived = derive_findings_from_recon(ports)

    # Recon-derived findings are recomputed each run. Exploit-derived findings
    # (added later in the guided flow) are left untouched here.
    db.query(Finding).filter(Finding.session_id == session.id, Finding.owasp_id.in_(["I2", "I3", "I5", "I9"])).delete(
        synchronize_session=False
    )
    db.commit()

    findings = []
    for d in derived:
        f = Finding(session_id=session.id, **d)
        db.add(f)
        findings.append(f)
    db.commit()
    for f in findings:
        db.refresh(f)

    return VulnResponse(explanation=STAGES["vuln"], findings=findings)


@router.get("/{session_id}/findings", response_model=list[FindingOut])
def get_findings(session_id: int, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    return db.query(Finding).filter_by(session_id=session.id).all()
