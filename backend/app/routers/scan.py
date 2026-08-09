"""Automated recon scan endpoints (FYP objective 1 + the "automation" half of
objective 2).

The heavy lifting is in services/scanner.py; this router's job is to enforce
lab scope BEFORE any packet is sent, run the scan in the threadpool (the
scanner is blocking socket I/O), persist an audit/report record, and hand
back a structured result the frontend Recon step can narrate.
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.deps import get_session_or_404
from app.models import ScanRun
from app.schemas import ScanRequest, ScanResult
from app.services import scanner
from app.services.guardrail import assert_in_scope

router = APIRouter(prefix="/api/sessions", tags=["scan"])


@router.post("/{session_id}/scan", response_model=ScanResult)
def run_scan(session_id: int, payload: ScanRequest | None = None, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    # Hard gate: this is the only endpoint that emits traffic to the target,
    # so the scope check lives here and raises 403 before scanner runs.
    assert_in_scope(session.target_ip)

    opts = payload or ScanRequest()
    result = scanner.run_scan(session.target_ip, use_nmap=opts.use_nmap, use_scapy=opts.use_scapy)

    db.add(
        ScanRun(
            session_id=session.id,
            target_ip=session.target_ip,
            in_scope=True,
            open_port_count=len(result["open_ports"]),
            result_json=json.dumps(result),
        )
    )
    db.commit()
    return result


@router.get("/{session_id}/scan", response_model=ScanResult)
def get_latest_scan(session_id: int, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    run = (
        db.query(ScanRun)
        .filter_by(session_id=session.id)
        .order_by(ScanRun.created_at.desc())
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="No scan has been run for this session yet.")
    return json.loads(run.result_json)
