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
