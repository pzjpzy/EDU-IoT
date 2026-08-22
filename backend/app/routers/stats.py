"""Dashboard analytics endpoints. Read-only aggregates over existing tables;
see services/stats.py for how each figure is derived."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.services import stats

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
def get_overview(db: DBSession = Depends(get_db)):
    return stats.overview(db)


@router.get("/vulnerabilities")
def get_vulnerabilities(granularity: str = "week", db: DBSession = Depends(get_db)):
    try:
        return stats.vuln_series(db, granularity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
