"""Vulnerability toggles for this camera image, read once at process start.

Lets the SAME target codebase be built as either the fully-vulnerable
default camera or a partially-hardened variant (see ../../target-hardened),
just by setting different environment variables at container start - no
code duplication between the two.

Exposed to the EduVAPT-IoT backend via GET /eduvapt/profile (see
web_admin.py), which is how the backend's task board adapts its challenge
list to whatever this specific target instance actually has enabled,
without ever having to exploit anything itself to find out.
"""
import os


def _flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


HTTP_DEFAULT_CREDS_VULNERABLE = _flag("EDUVAPT_HTTP_DEFAULT_CREDS", True)
SNAPSHOT_UNAUTH_VULNERABLE = _flag("EDUVAPT_SNAPSHOT_UNAUTH", True)
TELNET_ENABLED = _flag("EDUVAPT_TELNET_ENABLED", True)
TELNET_DEFAULT_CREDS_VULNERABLE = _flag("EDUVAPT_TELNET_DEFAULT_CREDS", True)
RTSP_ENABLED = _flag("EDUVAPT_RTSP_ENABLED", True)

# A fixed, non-default, non-guessable credential used when the "default
# creds" weakness is turned off - the login still works for legitimate use,
# it just isn't exploitable via the well-known defaults list anymore.
HARDENED_HTTP_CREDENTIAL = ("admin", "Str0ngP@ssw0rd!2026")
HARDENED_TELNET_CREDENTIAL = ("admin", "T3lnetH@rden2026")


def profile() -> dict:
    return {
        "http_default_creds_vulnerable": HTTP_DEFAULT_CREDS_VULNERABLE,
        "snapshot_unauth_vulnerable": SNAPSHOT_UNAUTH_VULNERABLE,
        "telnet_enabled": TELNET_ENABLED,
        "telnet_default_creds_vulnerable": TELNET_ENABLED and TELNET_DEFAULT_CREDS_VULNERABLE,
        "rtsp_enabled": RTSP_ENABLED,
    }
