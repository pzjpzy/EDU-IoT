"""Intentionally exposed, unauthenticated RTSP-style banner responder (OWASP I2).

Only reproduces enough of the RTSP handshake (an OPTIONS/DESCRIBE-style
banner reply) for banner-grabbing and Nmap service detection to identify the
service and for the guided flow to flag it as an insecure, unauthenticated
network service. No real video is streamed - the teaching point is the
exposure of the service itself, not the stream content.
"""
import socket
import threading

BANNER_RESPONSE = (
    "RTSP/1.0 200 OK\r\n"
    "CSeq: 1\r\n"
    "Public: OPTIONS, DESCRIBE, SETUP, PLAY, TEARDOWN\r\n"
    "Server: IoT-Cam-RTSP/1.0 (insecure-demo, unauthenticated)\r\n"
    "\r\n"
)


def handle_client(conn: socket.socket) -> None:
    try:
        conn.settimeout(5)
        conn.recv(1024)
        conn.sendall(BANNER_RESPONSE.encode())
    except OSError:
        pass
    finally:
        conn.close()


def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 554))
    server.listen(20)
    while True:
        conn, _ = server.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    main()
