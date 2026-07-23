"""Central configuration for EduVAPT-IoT backend.

Kept as plain module-level constants (rather than a settings library) so a
student reading the code for a viva can find every knob in one place.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Database -----------------------------------------------------------
DATABASE_URL = os.environ.get("EDUVAPT_DATABASE_URL", f"sqlite:///{BASE_DIR}/eduvapt.db")

# --- Lab scope guardrail -------------------------------------------------
# Only these networks may ever be set as a session's target. This is what
# keeps the tool honestly scoped to a student's own isolated lab (GNS3
# topology, Docker target, or loopback) instead of pointing it at anything
# on the internet. Override via EDUVAPT_LAB_CIDRS ("cidr,cidr,...") if an
# educator needs a different lab range.
_DEFAULT_LAB_CIDRS = [
    "127.0.0.0/8",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
]
LAB_CIDRS = [
    c.strip()
    for c in os.environ.get("EDUVAPT_LAB_CIDRS", ",".join(_DEFAULT_LAB_CIDRS)).split(",")
    if c.strip()
]

# --- Reporting --------------------------------------------------------------
REPORT_TITLE = "EduVAPT-IoT Vulnerability Assessment Report"
