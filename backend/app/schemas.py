import datetime
from typing import Any, Optional

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


class ExploitAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service: str
    username: Optional[str] = None
    password: Optional[str] = None
    success: bool
    note: Optional[str] = None


class ReconResponse(BaseModel):
    stage: str = "recon"
    explanation: dict[str, Any]
    hosts_discovered: list[str]
    discovery_method: str
    warning: Optional[str] = None
    ports: list[dict[str, Any]]


class VulnResponse(BaseModel):
    stage: str = "vuln"
    explanation: dict[str, Any]
    findings: list[FindingOut]


class ExploitResponse(BaseModel):
    stage: str = "exploit"
    explanation: dict[str, Any]
    attempts: list[ExploitAttemptOut]


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
