# Simulated Vulnerable CCTV Camera (EduVAPT-IoT target)

A deliberately weak "IoT camera" used as the training target for
EduVAPT-IoT. **Never expose this image on an untrusted or production
network** - every weakness below is intentional.

## Services

| Port | Service | Intentional weakness | OWASP IoT mapping |
|------|---------|----------------------|--------------------|
| 80   | Web admin panel (`web_admin.py`) | Default credentials (`admin/admin`, `admin/1234`, `admin/password`); static unsigned session cookie; `/snapshot.jpg` reachable with **no authentication at all** | I1, I3 |
| 23   | Telnet-style CLI (`telnet_stub.py`) | Plaintext credential prompt, default creds (`admin/admin`, `admin/1234`, `root/root`) | I1, I2 |
| 554  | RTSP-style banner (`rtsp_stub.py`) | Responds to any client with no authentication; plaintext protocol | I2 |

## Self-reporting for the HTB-style task board

Students interact with this target directly using their own tools (nmap,
browser, telnet client) - the EduVAPT-IoT app never scans or exploits it for
them. To let the app auto-detect when a step is actually completed, three
events are self-reported to an internal JSON file (`events.py`) and exposed
at `GET /eduvapt/status` (polled by the backend, not linked from any
student-facing page):

| Event | Triggered by |
|-------|--------------|
| `http_default_login` | Successful `/login` with a default credential |
| `unauth_snapshot_access` | `/snapshot.jpg` fetched without a valid session cookie |
| `telnet_default_login` | Successful Telnet login with a default credential |

Two flags are also embedded for the submission-style tasks:
- `EDUVAPT{d3f4ult_cr3d5_4r3_d4ng3r0us}` - shown on `/live` after HTTP login
- `EDUVAPT{t3ln3t_d3f4ult_cr3d5}` - shown after a successful Telnet login

See `backend/app/content/tasks.yaml` for how these map to the guided task
list.

## Vulnerability toggles (for building variants of this same image)

Every weakness above can be switched off independently via environment
variables, read once at container start (`app/vuln_config.py`):

| Variable | Default | Effect when set to `false` |
|----------|---------|------------------------------|
| `EDUVAPT_HTTP_DEFAULT_CREDS` | `true` | HTTP login only accepts a fixed strong credential instead of the default-creds list |
| `EDUVAPT_SNAPSHOT_UNAUTH` | `true` | `/snapshot.jpg` requires a valid session cookie |
| `EDUVAPT_TELNET_ENABLED` | `true` | Telnet service isn't started at all (port 23 closed) |
| `EDUVAPT_TELNET_DEFAULT_CREDS` | `true` | Telnet only accepts a fixed strong credential instead of the default-creds list |
| `EDUVAPT_RTSP_ENABLED` | `true` | RTSP-style service isn't started at all (port 554 closed) |

The resulting configuration is declared at `GET /eduvapt/profile` (internal
use, polled by the backend when it builds a session's challenge list and
report - see `backend/app/services/target_profile.py`). This is how
EduVAPT-IoT adapts to whichever target variant is actually running, instead
of assuming every weakness is always present.

See [`../target-hardened/`](../target-hardened/) for a ready-made
partially-patched variant built from this same `app/` source.

## Running locally (for development/testing outside GNS3)

```bash
cd target
docker compose up --build
```

This publishes ports 80/23/554 straight onto `localhost`, so a EduVAPT-IoT
session created with target IP `127.0.0.1` will work immediately.

## Replacing the placeholder camera image

A generated placeholder lives at `app/assets/cctv_snapshot.jpg`. To use a
real snapshot, replace that file (keep the same filename) and rebuild the
image.

## Importing into GNS3

See [`../docs/gns3_setup.md`](../docs/gns3_setup.md) for step-by-step
instructions on importing this image as a GNS3 Docker node template and
wiring it into a lab topology.
