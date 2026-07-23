"""Lab-scope guardrail.

Every scan/exploit endpoint must call `assert_in_scope` before touching the
network. This keeps the tool honestly scoped to the student's own isolated
lab (loopback, Docker target, or a GNS3-hosted RFC1918 network) instead of
becoming a general-purpose network scanner.
"""
import ipaddress

from fastapi import HTTPException

from app.config import LAB_CIDRS

_NETWORKS = [ipaddress.ip_network(c) for c in LAB_CIDRS]


def is_in_scope(target_ip: str) -> bool:
    try:
        ip = ipaddress.ip_address(target_ip)
    except ValueError:
        return False
    return any(ip in net for net in _NETWORKS)


def assert_in_scope(target_ip: str) -> None:
    if not is_in_scope(target_ip):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Target '{target_ip}' is outside the configured lab scope "
                f"({', '.join(LAB_CIDRS)}). EduVAPT-IoT only operates against "
                "your authorised lab network (e.g. a GNS3 topology or the "
                "bundled Docker target). Update EDUVAPT_LAB_CIDRS if your "
                "lab genuinely uses a different range."
            ),
        )
