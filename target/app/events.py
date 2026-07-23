"""Shared "has this vulnerability been triggered yet?" state.

web_admin.py, telnet_stub.py, and rtsp_stub.py each run as their own OS
process (see entrypoint.sh), so they can't share a Python in-memory dict.
Instead they read/write a small JSON file. This is a single-student lab
container with very low event frequency, so a plain read-modify-write
(no file locking) is an acceptable simplification - not something to
harden further for this teaching tool.
"""
import json
import os

_PATH = "/tmp/eduvapt_events.json"

_DEFAULT_EVENTS = {
    "http_default_login": False,
    "unauth_snapshot_access": False,
    "telnet_default_login": False,
}


def _read() -> dict:
    if not os.path.exists(_PATH):
        return dict(_DEFAULT_EVENTS)
    try:
        with open(_PATH, encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(_DEFAULT_EVENTS)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_EVENTS)


def mark(event: str) -> None:
    data = _read()
    data[event] = True
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)


def get_all() -> dict:
    return _read()


def reset() -> None:
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(dict(_DEFAULT_EVENTS), f)
