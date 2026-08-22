import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database import Base


class VaptSession(Base):
    """One guided VAPT walkthrough against one target IP."""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    target_ip = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    findings = relationship("Finding", back_populates="session", cascade="all, delete-orphan")
    task_progress = relationship("TaskProgress", back_populates="session", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="session", cascade="all, delete-orphan")
    scan_runs = relationship("ScanRun", back_populates="session", cascade="all, delete-orphan")
    state = relationship("SessionState", back_populates="session", uselist=False, cascade="all, delete-orphan")


class TaskProgress(Base):
    """Per-session completion state for one entry in content/tasks.yaml."""

    __tablename__ = "task_progress"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    task_id = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    session = relationship("VaptSession", back_populates="task_progress")


class Finding(Base):
    """An OWASP-IoT-mapped vulnerability finding, created when a task completes."""

    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    owasp_id = Column(String, nullable=False)  # e.g. "I1"
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # Low / Medium / High
    evidence = Column(Text, nullable=False)
    mitigation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("VaptSession", back_populates="findings")


class ScanRun(Base):
    """One automated recon scan the tool ran against the session's target.

    Kept as an audit trail (target + time + in-scope decision) so the
    "authorised lab target only" claim is evidenced, and so the latest scan's
    result can be folded into the PDF report. The full structured result is
    stored as JSON rather than normalised, since it's only ever read back
    whole for display/reporting.
    """

    __tablename__ = "scan_runs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    target_ip = Column(String, nullable=False)
    in_scope = Column(Boolean, nullable=False)
    open_port_count = Column(Integer, nullable=False, default=0)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("VaptSession", back_populates="scan_runs")


class Feedback(Base):
    """A post-session rating (1-5 stars) + optional suggestion, collected when
    the student leaves the capstone for the summary. Kept independent of the
    session (session_id is nullable and nulled, not cascaded, on session
    delete) so feedback survives for the admin panel even if a session is
    removed."""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    rating = Column(Integer, nullable=False)  # 1-5
    suggestion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SessionState(Base):
    """Per-session UI progress so the guided flow survives a page reload.

    `furthest_phase` is the highest wizard step the student has reached
    (0=Pre-Quiz ... 4=Capstone, 5=Summary/complete); the stepper lets them
    jump back to any phase up to it. `capstone_status` records how the
    capstone ended - completed, given up part-way, or skipped - which the
    end-of-session summary and report distinguish. A separate table (rather
    than columns on VaptSession) so it's created cleanly by create_all with
    no migration of existing sessions.
    """

    __tablename__ = "session_state"

    session_id = Column(Integer, ForeignKey("sessions.id"), primary_key=True)
    furthest_phase = Column(Integer, nullable=False, default=0)
    capstone_status = Column(String, nullable=True)  # completed | gave_up | skipped

    session = relationship("VaptSession", back_populates="state")


class QuizAttempt(Base):
    """A pre- or post-session learning-effectiveness quiz attempt."""

    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    phase = Column(String, nullable=False)  # "pre" | "post"
    answers_json = Column(Text, nullable=False)
    score = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("VaptSession", back_populates="quiz_attempts")
