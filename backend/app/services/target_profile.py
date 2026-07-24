"""Reads a target's self-declared vulnerability profile.

The backend never scans or exploits a target to work out which weaknesses
it has - see target/app/vuln_config.py and its GET /eduvapt/profile
endpoint, which the target declares about itself. This just fetches and
validates that declaration, falling back to "assume everything is present"
for targets that don't expose it at all (e.g. an un-instrumented device),
which keeps behaviour identical to before this feature existed.
"""
import requests

PROFILE_TIMEOUT_SECONDS = 3

DEFAULT_PROFILE = {
    "http_default_creds_vulnerable": True,
    "snapshot_unauth_vulnerable": True,
    "telnet_enabled": True,
    "telnet_default_creds_vulnerable": True,
    "rtsp_enabled": True,
}


def fetch_profile(target_ip: str) -> tuple[dict, str | None]:
    """Returns (profile, warning). `warning` is set when the target's
    profile couldn't be read, in which case every task is treated as
    applicable (the original, pre-adaptive behaviour)."""
    try:
        resp = requests.get(f"http://{target_ip}/eduvapt/profile", timeout=PROFILE_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
        profile = dict(DEFAULT_PROFILE)
        profile.update({k: bool(v) for k, v in data.items() if k in DEFAULT_PROFILE})
        return profile, None
    except requests.RequestException as exc:
        return dict(DEFAULT_PROFILE), (
            f"Could not read the target's vulnerability profile ({exc}); assuming every challenge applies."
        )
