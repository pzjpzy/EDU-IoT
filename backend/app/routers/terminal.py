"""In-browser terminal: a real PowerShell process per WebSocket connection,
piped through a Windows pseudo-console (ConPTY via pywinpty) so interactive
tools like Nmap and the Windows Telnet client render correctly (colors,
in-place progress updates, line editing).

This intentionally gives a full, unrestricted shell - for the single-student
local lab this project targets, that's just a browser tab controlling the
student's own machine (no more capability than a normal terminal window
already gives them). If this ever became a shared multi-student deployment,
each session would need to run inside its own isolated container instead of
spawning a shell directly on a shared host.
"""
import asyncio
import json
import os

from fastapi import APIRouter, WebSocket

router = APIRouter()

SHELL_CMD = "powershell.exe -NoLogo"
READ_CHUNK_SIZE = 4096
HEARTBEAT_INTERVAL_SECONDS = 15

# The backend process's own environment doesn't necessarily have Nmap's
# install directory on PATH (the official Windows installer doesn't always
# add it, and a service/venv process can inherit a stripped-down PATH even
# when a normal interactive shell has the right one) - same issue this
# project already hit with python-nmap. Guarantee it's there for the spawned
# shell too, so `nmap` just works without the student having to fix PATH.
_EXTRA_PATH_DIRS = [
    r"C:\Program Files (x86)\Nmap",
    r"C:\Program Files\Nmap",
]


def _build_env() -> dict:
    env = os.environ.copy()
    extra = [d for d in _EXTRA_PATH_DIRS if os.path.isdir(d)]
    if extra:
        env["PATH"] = os.pathsep.join([env.get("PATH", ""), *extra])
    return env


def _spawn_pty(cols: int, rows: int):
    from winpty import PtyProcess  # Windows-only; imported lazily

    return PtyProcess.spawn(SHELL_CMD, dimensions=(rows, cols), env=_build_env())


def _blocking_read(pty) -> str | None:
    try:
        data = pty.read(READ_CHUNK_SIZE)
        return data or None
    except EOFError:
        return None


@router.websocket("/ws/terminal")
async def terminal_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    loop = asyncio.get_event_loop()
    pty = await loop.run_in_executor(None, _spawn_pty, 80, 24)

    async def pump_output() -> None:
        while True:
            data = await loop.run_in_executor(None, _blocking_read, pty)
            if data is None:
                await websocket.send_json({"type": "exit"})
                return
            await websocket.send_json({"type": "output", "data": data})

    async def pump_input() -> None:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            if msg.get("type") == "input":
                pty.write(msg["data"])
            elif msg.get("type") == "resize":
                pty.setwinsize(int(msg.get("rows", 24)), int(msg.get("cols", 80)))

    async def heartbeat() -> None:
        # A dead/half-closed connection (browser crash, network drop, or a
        # client-side close that happens before the handshake even
        # finished) doesn't always deliver a close frame the server can
        # detect via receive_text(). Periodically writing something forces
        # an error promptly once the socket is actually gone, instead of
        # leaking the PTY/shell process forever waiting for a message that
        # will never arrive.
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
            await websocket.send_json({"type": "ping"})

    tasks = [asyncio.create_task(c) for c in (pump_output(), pump_input(), heartbeat())]
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for t in tasks:
            t.cancel()
        try:
            pty.terminate(force=True)
        except Exception:
            pass
        try:
            await websocket.close()
        except Exception:
            pass
