"""Intentionally vulnerable Telnet-style admin CLI stub (OWASP I1 / I2).

Real Telnet is unencrypted and commonly left enabled with default creds on
cheap IoT devices - this reproduces just enough of that behaviour (a
username/password prompt over plaintext TCP) for the guided task board to
demonstrate the concept, without needing a full Telnet protocol
implementation. A successful login self-reports via events.py so the
backend can auto-detect task completion.

Real Telnet clients (telnet.exe, PuTTY in Telnet mode) default to the NVT
character-at-a-time mode: every keystroke is sent to the server the instant
it's typed, rather than buffered locally into a line. That means a single
recv() can return just the first character - so input has to be accumulated
byte-by-byte until a line terminator, not read in one shot. NVT mode also
expects the *server* to echo typed characters back (the client does not
echo locally), so without that this looks "broken" - typing appears to do
nothing until Enter. Both are handled below with minimal telnet framing
(discarding IAC negotiation bytes, not attempting to reply to them).
"""
import socket
import threading

import events

VALID_CREDENTIALS = {
    ("admin", "admin"),
    ("admin", "1234"),
    ("root", "root"),
}

FLAG_TELNET_LOGIN = "EDUVAPT{t3ln3t_d3f4ult_cr3d5}"

IAC = 0xFF


def read_line(conn: socket.socket, echo_char: bytes | None = None) -> str:
    """Accumulate bytes up to a newline, echoing each character back like a
    real Telnet server (NVT mode expects the server to echo, not the
    client). `echo_char` overrides what's echoed (e.g. b"*" for a password);
    None echoes the typed byte itself.
    """
    buf = bytearray()
    while True:
        chunk = conn.recv(1)
        if not chunk:
            break
        b = chunk[0]
        if b == IAC:
            # Telnet negotiation command (IAC + verb + option) - discard the
            # next two bytes and don't attempt to negotiate back.
            conn.recv(2)
            continue
        if b == 0x0A:  # \n ends the line (a preceding \r, if any, is dropped below)
            conn.sendall(b"\r\n")
            break
        if b == 0x0D:  # bare \r - ignore, wait for the \n
            continue
        if b in (0x08, 0x7F):  # backspace / delete - basic line editing
            if buf:
                buf.pop()
                conn.sendall(b"\b \b")
            continue
        buf.append(b)
        conn.sendall(echo_char if echo_char is not None else chunk)
    return bytes(buf).decode(errors="replace").strip()


def handle_client(conn: socket.socket) -> None:
    try:
        conn.settimeout(60)
        conn.sendall(b"IoT-Cam Telnet CLI\r\nUsername: ")
        username = read_line(conn)
        conn.sendall(b"Password: ")
        password = read_line(conn, echo_char=b"*")
        if (username, password) in VALID_CREDENTIALS:
            events.mark("telnet_default_login")
            conn.sendall(f"Welcome to IoT-Cam CLI\r\nFLAG: {FLAG_TELNET_LOGIN}\r\ncamera> ".encode())
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
