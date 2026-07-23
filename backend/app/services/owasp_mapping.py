"""Rule-based mapper: turns recon/exploit facts into OWASP-IoT-mapped
findings with a severity, evidence, and mitigation.

This is intentionally a small, readable set of if/else rules rather than a
generic scoring engine - the point for the FYP is that the mapping logic is
transparent and explainable to a student, not that it is exhaustive.
"""
import os

import yaml

_CONTENT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content")

with open(os.path.join(_CONTENT_DIR, "owasp_top5.yaml"), encoding="utf-8") as f:
    OWASP_TOP5 = yaml.safe_load(f)


def _mitigation(owasp_id: str) -> str:
    return OWASP_TOP5[owasp_id]["mitigation"].strip()


def derive_findings_from_recon(ports: list[dict]) -> list[dict]:
    findings: list[dict] = []
    open_ports = {p["port"]: p for p in ports if p.get("state") == "open"}

    if not open_ports:
        return findings

    findings.append(
        {
            "owasp_id": "I9",
            "title": "Device exposes network services with no visible hardening",
            "severity": "Low",
            "evidence": f"Open ports detected: {sorted(open_ports.keys())}.",
            "mitigation": _mitigation("I9"),
        }
    )

    if 23 in open_ports:
        findings.append(
            {
                "owasp_id": "I2",
                "title": "Telnet (unencrypted remote administration) is exposed",
                "severity": "Medium",
                "evidence": "Port 23/tcp is open and responding to Telnet-style negotiation.",
                "mitigation": _mitigation("I2"),
            }
        )

    if 554 in open_ports:
        findings.append(
            {
                "owasp_id": "I2",
                "title": "RTSP video streaming service is exposed unencrypted",
                "severity": "Medium",
                "evidence": "Port 554/tcp is open and responds to RTSP OPTIONS/DESCRIBE requests.",
                "mitigation": _mitigation("I2"),
            }
        )

    for http_port in (80, 8080):
        if http_port in open_ports:
            banner = open_ports[http_port].get("banner", "")
            findings.append(
                {
                    "owasp_id": "I3",
                    "title": "Web-based admin/ecosystem interface is reachable",
                    "severity": "Low",
                    "evidence": f"Port {http_port}/tcp is open serving an HTTP interface. Banner: {banner or 'n/a'}",
                    "mitigation": _mitigation("I3"),
                }
            )

    unidentified = [p for p in open_ports.values() if not p.get("version")]
    if unidentified:
        findings.append(
            {
                "owasp_id": "I5",
                "title": "Service versions could not be positively identified",
                "severity": "Low",
                "evidence": (
                    "No version banner returned for: "
                    + ", ".join(f"{p['port']}/{p['protocol']} ({p['service']})" for p in unidentified)
                    + ". Unidentified/unadvertised versions make it harder to confirm patch status."
                ),
                "mitigation": _mitigation("I5"),
            }
        )

    return findings


def derive_findings_from_exploit(attempts: list[dict], snapshot_check: dict) -> list[dict]:
    findings: list[dict] = []

    for attempt in attempts:
        if attempt.get("success"):
            findings.append(
                {
                    "owasp_id": "I1",
                    "title": f"Default credentials accepted on {attempt['service']} service",
                    "severity": "High",
                    "evidence": (
                        f"Successfully authenticated to the {attempt['service']} service using "
                        f"username='{attempt['username']}', password='{attempt['password']}'."
                    ),
                    "mitigation": _mitigation("I1"),
                }
            )

    if snapshot_check.get("success"):
        findings.append(
            {
                "owasp_id": "I3",
                "title": "Live camera feed accessible without any authentication",
                "severity": "High",
                "evidence": snapshot_check.get("note", ""),
                "mitigation": _mitigation("I3"),
            }
        )

    return findings
