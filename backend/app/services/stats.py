"""Aggregate statistics for the dashboard's analytics strip.

All figures come from existing tables - no new tracking:
  - "CCTV scanned this month" = distinct target IPs among ScanRun rows dated in
    the current calendar month (a target is identified by its IP; scanning the
    same IP repeatedly counts once).
  - Overall quiz accuracy = sum(score)/sum(total) across EVERY QuizAttempt in
    every session (pre-quiz and capstone alike).
  - Vulnerabilities over time = Finding rows bucketed by day/week/month and
    counted per severity, for the stacked bar chart.

Time bucketing is done in Python (small lab-scale data) so it stays portable
across SQLite and any other backend.
"""
import datetime as dt

from sqlalchemy import distinct, func
from sqlalchemy.orm import Session as DBSession

from app.models import Finding, QuizAttempt, ScanRun

SEVERITIES = ("High", "Medium", "Low")
GRANULARITIES = ("day", "week", "month")


def _start_of_month(today: dt.date) -> dt.date:
    return today.replace(day=1)


def overview(db: DBSession) -> dict:
    today = dt.date.today()
    month_start = dt.datetime.combine(_start_of_month(today), dt.time.min)

    cctv_scanned = (
        db.query(func.count(distinct(ScanRun.target_ip)))
        .filter(ScanRun.created_at >= month_start)
        .scalar()
    ) or 0

    correct = db.query(func.coalesce(func.sum(QuizAttempt.score), 0)).scalar() or 0
    total = db.query(func.coalesce(func.sum(QuizAttempt.total), 0)).scalar() or 0
    pct = round(correct / total * 100) if total else 0

    vulns_all_time = db.query(func.count(Finding.id)).scalar() or 0

    return {
        "cctv_scanned_this_month": int(cctv_scanned),
        "quiz_accuracy": {"correct": int(correct), "total": int(total), "pct": pct},
        "vulns_all_time": int(vulns_all_time),
    }


def _buckets(granularity: str) -> list[tuple[tuple, str]]:
    """Ordered (key, label) pairs for the most recent buckets, oldest first."""
    today = dt.date.today()
    out: list[tuple[tuple, str]] = []
    if granularity == "day":
        for i in range(6, -1, -1):
            d = today - dt.timedelta(days=i)
            out.append((("day", d), d.strftime("%a")))
    elif granularity == "week":
        monday = today - dt.timedelta(days=today.weekday())
        for i in range(7, -1, -1):
            wk = monday - dt.timedelta(weeks=i)
            out.append((("week", wk), wk.strftime("%d %b")))
    else:  # month
        y, m = today.year, today.month
        for i in range(5, -1, -1):
            mm, yy = m - i, y
            while mm <= 0:
                mm += 12
                yy -= 1
            first = dt.date(yy, mm, 1)
            out.append((("month", first), first.strftime("%b")))
    return out


def _key(granularity: str, created: dt.datetime) -> tuple:
    d = created.date()
    if granularity == "day":
        return ("day", d)
    if granularity == "week":
        return ("week", d - dt.timedelta(days=d.weekday()))
    return ("month", d.replace(day=1))


def vuln_series(db: DBSession, granularity: str) -> list[dict]:
    if granularity not in GRANULARITIES:
        raise ValueError(f"Unknown granularity '{granularity}'.")
    buckets = _buckets(granularity)
    index = {key: {"bucket": label, "High": 0, "Medium": 0, "Low": 0} for key, label in buckets}
    order = [key for key, _ in buckets]

    for severity, created in db.query(Finding.severity, Finding.created_at).all():
        if created is None or severity not in SEVERITIES:
            continue
        key = _key(granularity, created)
        if key in index:
            index[key][severity] += 1

    return [index[key] for key in order]
