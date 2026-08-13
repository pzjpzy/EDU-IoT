# Running EduVAPT-IoT Locally with Docker (no GNS3)

The simplest way to get the whole lab working: the vulnerable camera runs as a
Docker container publishing its ports onto `localhost`, and you attack it at
`127.0.0.1` with your own tools. No virtual machines, no topology, no
networking to configure.

This is the recommended path for development, for marking/demoing, and as the
fallback if the GNS3 lab misbehaves. Nothing about EduVAPT-IoT changes between
the two - only where the camera lives. For the topology version, see
[`gns3_setup.md`](gns3_setup.md).

---

## 0. The big picture (read this first)

Three processes, all on your Windows machine:

```
┌─ YOUR WINDOWS HOST ──────────────────────────────────────────────┐
│                                                                   │
│  frontend (Vite dev server)  http://localhost:5173                │
│        │  fetch / WebSocket                                       │
│        ▼                                                          │
│  backend (FastAPI + uvicorn)  http://127.0.0.1:8000               │
│        │                                                          │
│        ├── recon scan ─────────► 127.0.0.1  ports 21..37777       │
│        ├── GET /eduvapt/profile ► 127.0.0.1:80                    │
│        ├── GET /eduvapt/status ─► 127.0.0.1:80                    │
│        └── spawns PowerShell (the in-browser terminal)            │
│                                                                   │
│  ┌─ Docker Desktop ───────────────────────────────────────────┐   │
│  │  eduvapt-camera container                                  │   │
│  │    :80  web admin + snapshot     ──published──► 127.0.0.1  │   │
│  │    :23  Telnet-style CLI         ──published──► 127.0.0.1  │   │
│  │    :554 RTSP-style banner        ──published──► 127.0.0.1  │   │
│  └────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

Two things worth knowing up front:

1. **Only the camera is containerised.** The backend is not, and shouldn't be:
   [`../backend/app/routers/terminal.py`](../backend/app/routers/terminal.py)
   spawns a real `powershell.exe` through a Windows pseudo-console (`pywinpty`)
   to power the in-browser terminal. That only works when the backend runs
   natively on Windows.
2. **`127.0.0.1` is inside the default lab scope** (`127.0.0.0/8` in
   [`../backend/app/config.py`](../backend/app/config.py)), so the scope
   guardrail lets sessions through with no configuration.

---

## 1. Prerequisites

| Needed | For | Required? |
|--------|-----|-----------|
| **Docker Desktop** | running the camera container | Yes |
| **Python 3.11+** | the backend | Yes |
| **Node 18+** | the frontend | Yes |
| **Nmap** (Windows installer) | *your* port-scanning task, and `-sV` enrichment in the automated scan | Recommended |
| **A Telnet or raw-TCP client** | the Telnet tasks | Yes (see below) |
| **Npcap + admin rights** | the optional Scapy packet-level probe | No |

The backend itself has **no scanning dependencies** - its recon sweep is pure
Python sockets ([`../backend/app/services/scanner.py`](../backend/app/services/scanner.py)).
Nmap and Scapy are enrichment layers only; when they're missing the scan still
runs and simply says so in its `engine_notes`.

For the Telnet tasks you need *something* that speaks raw TCP. Easiest options:

- **`ncat`** - ships with the Nmap installer, so you probably already have it.
- **Windows Telnet client** - not installed by default. Enable it with, in an
  Administrator PowerShell:
  ```bash
  dism /online /Enable-Feature /FeatureName:TelnetClient
  ```
- **PuTTY** in Telnet mode.

All three work: the target's Telnet stub implements the NVT server-side echo
and IAC handling that real Telnet clients expect
([`../target/app/telnet_stub.py`](../target/app/telnet_stub.py)).

---

## 2. Start the camera

From the repo root:

```bash
cd target
docker compose up --build -d
```

The `--build` is only needed the first time (and after you change anything in
`target/app/`). Confirm it came up:

```bash
docker compose ps
```

You want `eduvapt-camera` with state `running` and ports `80`, `23`, `554`
published. See [`../target/README.md`](../target/README.md) for the full list
of what's intentionally weak in it.

> **Port 80 already in use?** That's the most common failure here, and Docker
> will refuse to start with a bind error. Usually it's IIS or the "World Wide
> Web Publishing Service". Find the culprit with
> `Get-NetTCPConnection -LocalPort 80 -State Listen`, then either stop that
> service or see [Troubleshooting](#troubleshooting) for remapping the port.

---

## 3. Start the backend

```bash
cd backend
python -m venv .venv
```

Activate it and install:

```bash
.\.venv\Scripts\Activate.ps1
```

```bash
pip install -r requirements.txt
```

If PowerShell blocks the activation script, run
`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` once,
then try again.

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

If `uvicorn` isn't on your PATH, call it through the venv's Python instead:

```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Leave this window running. Check it in a browser at
<http://127.0.0.1:8000/api/health> - you should get `{"status":"ok"}`. The
interactive API docs are at <http://127.0.0.1:8000/docs>.

The SQLite database is created automatically at `backend/eduvapt.db`.

---

## 4. Start the frontend

In a **second** terminal:

```bash
cd frontend
npm install
```

```bash
npm run dev
```

Open <http://localhost:5173>.

> **Keep it on port 5173.** The backend's CORS policy explicitly allows only
> `http://localhost:5173` and `http://127.0.0.1:5173`
> ([`../backend/app/main.py`](../backend/app/main.py)). If Vite grabs a
> different port because 5173 is taken, every API call will fail with a CORS
> error in the browser console.

---

## 5. Verify the wiring before you start

Worth 30 seconds, because two of these failures are silent rather than loud.
In a third terminal:

```bash
Test-NetConnection 127.0.0.1 -Port 80
```

Repeat for `-Port 23` and `-Port 554`. All three should report
`TcpTestSucceeded : True`.

Then check the endpoint the task board depends on:

```bash
curl.exe http://127.0.0.1/eduvapt/profile
```

Use `curl.exe`, not `curl` - in PowerShell, bare `curl` is an alias for
`Invoke-WebRequest` and takes different arguments.

You should get all five flags as `true`:

```json
{"http_default_creds_vulnerable":true,"rtsp_enabled":true,"snapshot_unauth_vulnerable":true,"telnet_default_creds_vulnerable":true,"telnet_enabled":true}
```

**Why this one matters:** the backend reads this profile to decide which
challenges apply to your target
([`../backend/app/services/target_profile.py`](../backend/app/services/target_profile.py)).
If it can't reach it, nothing errors out - the board just falls back to
"assume every weakness exists" and shows a warning banner. Catching that here
is much easier than debugging it three tasks in.

---

## 6. Run a session

1. Open <http://localhost:5173> and accept the authorised-use disclaimer.
2. On the dashboard, give the session a name and leave **Target IP** as
   `127.0.0.1`.
3. **Start guided session.**

The flow is Pre-Quiz → Recon → Challenges → Report → Post-Quiz.

**Recon** runs the automated sweep and narrates each finding. Expect exactly
**three open ports** - 80, 23 and 554. That's not the scanner being shy: those
are the only ports the container publishes, and the scanner checks a curated
list of 16 CCTV/DVR-relevant ports rather than all 65535. Read `engine_notes`
in the result to see which enrichment layers actually ran.

**Challenges** is where you do the work yourself, with your own tools, against
`127.0.0.1`. Two kinds of task:

- **`submit`** - you type an answer or flag and the backend checks it.
- **`auto`** - the *target* notices you triggered the weakness and self-reports
  it; the page polls and the task completes on its own, with nothing to type.

You can use any terminal you like, or the **in-browser terminal panel**, which
is a real PowerShell session on your machine - it even force-adds the standard
Nmap install directories to `PATH`, so `nmap` works there whether or not the
installer set it up globally.

Two tasks trip people up:

- **The unauthenticated snapshot.** You must request
  `http://127.0.0.1/snapshot.jpg` with **no session cookie**. If you already
  logged into the admin panel in that browser, you're holding a
  `session=authenticated` cookie and the target will correctly decide this
  *wasn't* an unauthenticated access, so the task won't complete. Use a
  private/incognito window ([`../target/app/web_admin.py`](../target/app/web_admin.py)).
- **The RTSP banner.** Port 554 only replies *after* it receives something, so
  connecting and waiting shows nothing. Send an OPTIONS request:
  ```bash
  (echo "OPTIONS rtsp://127.0.0.1:554/ RTSP/1.0"; echo "CSeq: 1"; echo "") | ncat 127.0.0.1 554
  ```

The final task completes automatically once everything above it is done, and
the **Report** step generates a PDF from the findings each completed task
produced.

---

## 7. Switching to the hardened target

`target-hardened/` is the same image with some weaknesses switched off, which
makes the task board and report adapt automatically - fewer challenges, plus a
"tested but not found" section in the report. It's a strong thing to show
alongside the vulnerable run.

Both variants bind the same ports, so **stop the first one before starting the
second**:

```bash
docker compose -f target/docker-compose.yml down
```

```bash
docker compose -f target-hardened/docker-compose.yml up --build -d
```

Run both commands from the repo root. Create a **new session** afterwards
rather than reusing the old one, so the board is rebuilt against the new
profile. Verify the switch took effect:

```bash
curl.exe http://127.0.0.1/eduvapt/profile
```

`http_default_creds_vulnerable`, `snapshot_unauth_vulnerable` and
`rtsp_enabled` should now be `false`. Telnet is deliberately left vulnerable,
so there's still something to find - the point is *partial* remediation, not a
fully patched device. See
[`../target-hardened/README.md`](../target-hardened/README.md).

To go back, `down` the hardened one and `up` `target/` again.

---

## 8. Resetting between runs

The camera records triggered events in a file inside the container
([`../target/app/events.py`](../target/app/events.py)). That state **survives a
container restart**, so a second student on the same container would find the
auto tasks already satisfied. Clear it with:

```bash
curl.exe -X POST http://127.0.0.1/eduvapt/reset
```

To reset EduVAPT's own side (sessions, findings, quiz results), stop the
backend and delete `backend/eduvapt.db`; it's recreated empty on the next
start. Or just create a new session - old ones are kept and listed on the
dashboard.

---

## 9. Shutting down

Stop the backend and frontend with `Ctrl+C` in their terminals, then:

```bash
docker compose -f target/docker-compose.yml down
```

`down` removes the container, which also discards the recorded events - so the
next `up` starts clean. Use `docker compose stop`/`start` instead if you want
to keep progress across a break.

---

## Troubleshooting

**`docker compose up` fails with a port bind error.**
Something on your machine already owns 80, 23 or 554. Identify it with
`Get-NetTCPConnection -LocalPort 80 -State Listen` and stop that service. If
you can't free the port, you can remap the *host* side in
`target/docker-compose.yml` (e.g. `"8080:80"`) - but be aware the backend
hardcodes port 80 when reading `/eduvapt/profile` and `/eduvapt/status`, so the
auto-detected tasks and the adaptive board will stop working. Freeing port 80
is much less trouble than remapping it.

**The task board shows a warning about the target's vulnerability profile.**
The backend couldn't reach `http://127.0.0.1/eduvapt/profile`, so it's assuming
every weakness applies. The container isn't running, or port 80 isn't
published. Re-run the check in Part 5.

**An `auto` task never completes even though the exploit worked.**
First confirm the target actually recorded it:
```bash
curl.exe http://127.0.0.1/eduvapt/status
```
If the relevant event is `false`, the target genuinely didn't see the trigger -
for the snapshot task, that almost always means you had a session cookie (use
incognito). If it's `true` but the task stays locked, complete the task above
it first: tasks unlock strictly in order.

**Every API call fails with a CORS error.**
The frontend isn't on port 5173. Stop whatever took the port and restart
`npm run dev`. (Alternatively set `VITE_API_BASE`, but fixing the port is
simpler.)

**The scan reports `nmap: python-nmap not installed` or `nmap: unavailable`.**
Expected and harmless - you lose `-sV` version detection, nothing else. Install
Nmap and make sure `C:\Program Files (x86)\Nmap` is on the backend process's
PATH if you want it. Restart the backend after installing.

**The Scapy probe says it needs raw-socket privileges.**
Also expected. It's an opt-in packet-level demonstration needing Npcap and
admin rights; the connect scan is what the results actually rely on.

**The in-browser terminal doesn't open.**
It needs `pywinpty`, which only installs on Windows. Confirm you're running the
backend natively on Windows (not in WSL or a container) and that
`pip install -r requirements.txt` completed without errors.

**Nothing at all responds on 127.0.0.1.**
Check Docker Desktop is actually running, then `docker compose ps` from
`target/`, then `docker compose logs` to see whether the container crashed on
startup.
