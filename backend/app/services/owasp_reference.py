"""Lookup helper over the OWASP IoT Top 5 reference content (mitigation text
keyed by category), used when a completed task is turned into a Finding.
"""
import os

import yaml

_CONTENT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content")

with open(os.path.join(_CONTENT_DIR, "owasp_top5.yaml"), encoding="utf-8") as f:
    OWASP_TOP5 = yaml.safe_load(f)


def mitigation(owasp_id: str) -> str:
    return OWASP_TOP5[owasp_id]["mitigation"].strip()
