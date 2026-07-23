import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.content_loader import load_yaml
from app.database import get_db
from app.deps import get_session_or_404
from app.models import ScanResult
from app.schemas import ReconResponse
from app.services.banner_grab import grab_banner
from app.services.guardrail import assert_in_scope
from app.services.network_scan import discover_host
from app.services.nmap_scan import NmapUnavailableError, scan_ports

router = APIRouter(prefix="/api/sessions", tags=["recon"])

STAGES = load_yaml("stages.yaml")

_BANNER_PORTS = {23, 80, 554, 8080}


@router.post("/{session_id}/recon", response_model=ReconResponse)
def run_recon(session_id: int, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    assert_in_scope(session.target_ip)

    alive, method, warning = discover_host(session.target_ip)

    try:
        ports = scan_ports(session.target_ip)
    except NmapUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    for port_info in ports:
        if port_info["port"] in _BANNER_PORTS and port_info["state"] == "open":
            banner = grab_banner(session.target_ip, port_info["port"])
            if banner:
                port_info["banner"] = banner[:300]

    db.query(ScanResult).filter_by(session_id=session.id, stage="recon").delete()
    db.add(
        ScanResult(
            session_id=session.id,
            stage="recon",
            raw_json=json.dumps({"alive": alive, "discovery_method": method, "warning": warning, "ports": ports}),
        )
    )
    db.commit()

    return ReconResponse(
        explanation=STAGES["recon"],
        hosts_discovered=[session.target_ip] if alive else [],
        discovery_method=method,
        warning=warning,
        ports=ports,
    )


@router.get("/{session_id}/recon", response_model=ReconResponse)
def get_recon(session_id: int, db: DBSession = Depends(get_db)):
    session = get_session_or_404(session_id, db)
    result = (
        db.query(ScanResult)
        .filter_by(session_id=session.id, stage="recon")
        .order_by(ScanResult.created_at.desc())
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Recon has not been run yet for this session.")
    data = json.loads(result.raw_json)
    return ReconResponse(
        explanation=STAGES["recon"],
        hosts_discovered=[session.target_ip] if data["alive"] else [],
        discovery_method=data["discovery_method"],
        warning=data.get("warning"),
        ports=data["ports"],
    )
