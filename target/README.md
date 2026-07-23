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
