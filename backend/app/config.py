"""Central configuration for EduVAPT-IoT backend.

Kept as plain module-level constants (rather than a settings library) so a
student reading the code for a viva can find every knob in one place.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Database -----------------------------------------------------------
DATABASE_URL = os.environ.get("EDUVAPT_DATABASE_URL", f"sqlite:///{BASE_DIR}/eduvapt.db")

# --- Lab scope guardrail -------------------------------------------------
# Only these networks may ever be scanned/exploited by this tool. This is
# what keeps the tool honestly scoped to a student's own isolated lab
# (GNS3 topology, Docker target, or loopback) instead of becoming a
# general-purpose scanner. Override via EDUVAPT_LAB_CIDRS ("cidr,cidr,...")
# if an educator needs a different lab range.
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

# --- Scanning -------------------------------------------------------------
# TCP connect scan (-sT) deliberately used instead of a SYN scan (-sS) so the
# backend does not need Administrator/raw-socket privileges to run on
# Windows. -sV (version detection) is deliberately NOT used: it probes ports
# with a long series of protocol-specific tests, and the intentionally
# minimal target stubs (telnet/RTSP) don't reply the way -sV expects, which
# makes it hang for minutes per port. Instead, nmap's built-in port->service
# name table gives us the service name instantly, and our own
# services/banner_grab.py does the actual "identify what's really running"
# probe for the ports this project cares about - which is a more honest
# teaching moment about how banner grabbing works anyway.
NMAP_TOP_PORTS = 100
NMAP_ARGS = f"-sT --top-ports {NMAP_TOP_PORTS} -T4 --host-timeout 20s"
SOCKET_TIMEOUT_SECONDS = 3

# --- Guided default-credential exploitation demo --------------------------
# Small, transparent, on-screen wordlist used for the guided "weak/default
# credentials" teaching step. Intentionally not a large real-world list --
# the point is to demonstrate the concept, not to be a brute-force tool.
DEFAULT_CREDENTIALS = [
    ("admin", "admin"),
    ("admin", "1234"),
    ("admin", "password"),
    ("root", "root"),
    ("root", "12345"),
    ("user", "user"),
]

# --- Reporting --------------------------------------------------------------
REPORT_TITLE = "EduVAPT-IoT Vulnerability Assessment Report"
