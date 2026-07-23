# EduVAPT-IoT

A guided and automated Vulnerability Assessment and Penetration Testing
(VAPT) tool that teaches students IoT/CCTV network security through a
step-by-step walkthrough against a simulated vulnerable camera - final year
project (FYP).

## What's here

- `backend/` - FastAPI JSON API: reconnaissance (Scapy + Nmap), OWASP IoT
  Top 5 vulnerability mapping, guided default-credential exploitation,
  ReportLab PDF reporting, and a pre/post learning-effectiveness quiz.
- `frontend/` - React + Vite + TypeScript + Tailwind SPA implementing the
  guided wizard (Pre-Quiz -> Recon -> Vulnerability ID -> Exploitation ->
  Report -> Post-Quiz).
- `target/` - A deliberately vulnerable simulated IP camera (Docker image):
  weak-credential HTTP admin panel, Telnet stub, and an unauthenticated
  RTSP-style banner service. Importable into GNS3 as a Docker node.
- `docs/gns3_setup.md` - How to wire the target into a GNS3 lab topology.

The tool only ever operates against targets inside a configured lab IP range
(loopback + RFC1918 by default) - see `backend/app/config.py`.

## Quickstart (local, no GNS3 needed)

Requires: Python 3.11+, Node 18+, Docker Desktop, Nmap (with Npcap) on
Windows.

**1. Start the simulated camera target**

```bash
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
```

**3. Start the frontend**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, accept the scope disclaimer, and create a new
session with target IP `127.0.0.1`.

## Using a GNS3 lab instead of the local Docker target

See [`docs/gns3_setup.md`](docs/gns3_setup.md) for importing `target/` as a
GNS3 Docker node and wiring a topology around it. EduVAPT-IoT itself doesn't
care where the target lives - point a session at whatever IP the camera ends
up with.

## Replacing the placeholder camera image

`target/app/assets/cctv_snapshot.jpg` is a generated placeholder. Drop in a
real snapshot at that path (same filename) and rebuild the target image.
