"""Manual raw-socket banner grabbing.

Nmap's -sV already guesses services, but part of the educational value here
is showing students *how* that guess is made: open a TCP socket, send a
minimal protocol probe, and read back whatever the service volunteers about
itself. Used to enrich recon results for the ports students most need to
understand (HTTP admin panel, Telnet, the RTSP stub).
"""
import socket

from app.config import SOCKET_TIMEOUT_SECONDS


def _probe(ip: str, port: int, payload: bytes | None) -> str | None:
    try:
        with socket.create_connection((ip, port), timeout=SOCKET_TIMEOUT_SECONDS) as sock:
            sock.settimeout(SOCKET_TIMEOUT_SECONDS)
            if payload:
                sock.sendall(payload)
            data = sock.recv(1024)
            return data.decode(errors="replace").strip()
    except Exception:
        return None


def grab_banner(ip: str, port: int) -> str | None:
    if port == 80 or port == 8080:
        return _probe(ip, port, b"GET / HTTP/1.0\r\nHost: %b\r\n\r\n" % ip.encode())
    if port == 554:
        return _probe(ip, port, b"OPTIONS rtsp://%b:%d/ RTSP/1.0\r\nCSeq: 1\r\n\r\n" % (ip.encode(), port))
    if port == 23:
        return _probe(ip, port, None)
    return _probe(ip, port, None)
