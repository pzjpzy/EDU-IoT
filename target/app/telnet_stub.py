"""Intentionally vulnerable Telnet-style admin CLI stub (OWASP I1 / I2).

Real Telnet is unencrypted and commonly left enabled with default creds on
cheap IoT devices - this reproduces just enough of that behaviour (a
username/password prompt over plaintext TCP) for the guided exploitation
stage to demonstrate the concept, without needing a full Telnet protocol
implementation.
"""
import socket
import threading

VALID_CREDENTIALS = {
    ("admin", "admin"),
    ("admin", "1234"),
    ("root", "root"),
}


def handle_client(conn: socket.socket) -> None:
    try:
        conn.settimeout(10)
        conn.sendall(b"IoT-Cam Telnet CLI\r\nUsername: ")
        username = conn.recv(256).decode(errors="replace").strip()
        conn.sendall(b"Password: ")
        password = conn.recv(256).decode(errors="replace").strip()
        if (username, password) in VALID_CREDENTIALS:
            conn.sendall(b"Welcome to IoT-Cam CLI\r\ncamera> ")
        else:
            conn.sendall(b"Login incorrect\r\n")
    except OSError:
        pass
    finally:
        conn.close()


def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 23))
    server.listen(20)
    while True:
        conn, _ = server.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    main()
