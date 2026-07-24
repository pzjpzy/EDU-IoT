# EduVAPT-IoT

A guided, Hack The Box-style VAPT lab that teaches students IoT/CCTV network
security. Students do the hacking themselves - with their own Nmap, browser,
and Telnet/netcat - against a live simulated camera; the platform guides
them through an ordered set of tasks and tracks progress automatically.
Final year project (FYP).

## What's here

- `backend/` - FastAPI JSON API: an ordered task/challenge engine
  (`content/tasks.yaml`), OWASP IoT Top 5 mapping, ReportLab PDF reporting,
  and a pre/post learning-effectiveness quiz. It never scans or exploits
  anything itself - it only tracks progress.
- `frontend/` - React + Vite + TypeScript + Tailwind SPA implementing the
  guided flow (Pre-Quiz -> Challenges -> Report -> Post-Quiz), with a
  Hack The Box-style task board (locked/active/completed tasks, live
  auto-detected progress, and flag/answer submission).
- `target/` - A deliberately vulnerable simulated IP camera (Docker image):
  weak-credential HTTP admin panel, Telnet stub, and an unauthenticated
  RTSP-style banner service. Self-reports triggered vulnerabilities to the
  backend (`/eduvapt/status`) so tasks can auto-complete with no student
  input. Importable into GNS3 as a Docker node.
- `target-hardened/` - A second target variant, built from the same
  `target/app/` source with some weaknesses fixed (see its README). The
  target self-declares which weaknesses it actually has via
  `GET /eduvapt/profile`; the backend reads that to adapt the challenge
  list and report to whatever's really present - no hardcoded assumptions.
- `docs/gns3_setup.md` - How to wire the target into a GNS3 lab topology.

The tool only ever lets a session target a configured lab IP range (loopback
+ RFC1918 by default) - see `backend/app/config.py`.

## How task completion works

Each entry in `backend/app/content/tasks.yaml` is one of:
- **`auto`** - the target itself notices the vulnerable action (e.g. a
  successful default-credential login) and reports it; the frontend polls
  every few seconds and the task completes with no typing required.
- **`submit`** - the student types an answer or flag (found by actually
  interacting with the target) which the backend validates.

Tasks unlock strictly in order. Completing one creates an OWASP-mapped
Finding that feeds the session's PDF report.

## Quickstart (local, no GNS3 needed)

Requires: Python 3.11+, Node 18+, Docker Desktop. (Nmap and a Telnet client
are only needed on whichever machine the *student* uses to attack the
target - the backend itself has no scanning dependencies.)

**1. Start the simulated camera target**

```bash
#Please change directory to the location of EDU-IoT first 
cd target
docker compose up --build -d
```

**2. Start the backend**

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
#if uvicorn is not working use line below
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

**3. Start the frontend**

```bash
cd frontend
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
npm install
npm run dev
```

Open http://localhost:5173, accept the scope disclaimer, and create a new
session with target IP `127.0.0.1`. Then use your own Nmap/browser/Telnet
client against `127.0.0.1` to work through the tasks.

## Using a GNS3 lab instead of the local Docker target

See [`docs/gns3_setup.md`](docs/gns3_setup.md) for importing `target/` as a
GNS3 Docker node and wiring a topology around it. EduVAPT-IoT itself doesn't
care where the target lives - point a session at whatever IP the camera ends
up with.

## Replacing the placeholder camera image

`target/app/assets/cctv_snapshot.jpg` is a generated placeholder. Drop in a
real snapshot at that path (same filename) and rebuild the target image.
