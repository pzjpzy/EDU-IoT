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

    scan_results = relationship("ScanResult", back_populates="session", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="session", cascade="all, delete-orphan")
    exploit_attempts = relationship("ExploitAttempt", back_populates="session", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="session", cascade="all, delete-orphan")


class ScanResult(Base):
    """Raw output captured at each guided stage (recon, etc.)."""

    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    stage = Column(String, nullable=False)  # e.g. "recon"
    raw_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("VaptSession", back_populates="scan_results")


class Finding(Base):
    """An OWASP-IoT-mapped vulnerability finding derived from scan data."""

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


class ExploitAttempt(Base):
    """A single guided exploitation attempt (credential try / access check)."""

    __tablename__ = "exploit_attempts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    service = Column(String, nullable=False)  # "http" | "telnet" | "snapshot"
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    success = Column(Boolean, default=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("VaptSession", back_populates="exploit_attempts")


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
