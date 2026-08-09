import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    name: str
    target_ip: str


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    target_ip: str
    created_at: datetime.datetime


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owasp_id: str
    title: str
    severity: str
    evidence: str
    mitigation: str


class QuizAnswer(BaseModel):
    question_id: str
    selected_index: int


class QuizSubmit(BaseModel):
    phase: str  # "pre" | "post"
    answers: list[QuizAnswer]


class QuizResult(BaseModel):
    phase: str
    score: int
    total: int
    breakdown: list[dict[str, Any]]


class ScanService(BaseModel):
    port: int
    protocol: str
    banner: str | None = None
    version: str | None = None
    owasp_id: str
    severity_hint: str
    observation: str
    why_it_matters: str
    reproduce: str


class ScanResult(BaseModel):
    target_ip: str
    duration_seconds: float
    ports_scanned: int
    open_ports: list[int]
    services: list[ScanService]
    engine_notes: list[str]
    summary: str


class ScanRequest(BaseModel):
    use_nmap: bool = True
    use_scapy: bool = False
