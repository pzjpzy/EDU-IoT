# Partially-Hardened CCTV Camera Variant

A second EduVAPT-IoT target: the **same simulated camera codebase** as
[`../target/`](../target/), built with a different vulnerability preset to
represent a device that's had some (but not all) common weaknesses fixed.

## What's fixed vs. left vulnerable here

| Weakness | Status in this variant |
|----------|------------------------|
| HTTP admin default credentials (OWASP I1) | **Fixed** - login requires a strong, non-default credential |
| Snapshot endpoint auth bypass (OWASP I3) | **Fixed** - `/snapshot.jpg` now requires a valid session |
| RTSP-style service exposure (OWASP I2) | **Fixed** - service disabled, port 554 closed |
| Telnet default credentials (OWASP I1 / I2) | **Still vulnerable** - default creds still work on port 23 |

This intentionally leaves one real weakness in place rather than shipping a
fully-patched device, since a partially-hardened target is a much more
realistic teaching scenario than "everything is broken" or "everything is
fixed."

## Why a separate Dockerfile instead of just different config

This is a genuinely separate image (its own Dockerfile, its own
`docker-compose.yml`, importable into GNS3 as its own node template
alongside the original camera) - but it builds from the exact same
`target/app/` source rather than a duplicated copy, so the two variants can
never drift out of sync. Only the environment variables differ; see
[`target/app/vuln_config.py`](../target/app/vuln_config.py) for the full
list of togglable weaknesses.

## How EduVAPT-IoT knows what's different

The backend never scans or exploits anything to figure out which
weaknesses this target has - it just reads `GET /eduvapt/profile` (a small
internal endpoint the target itself exposes, declaring its own
configuration) and filters the guided challenge list and PDF report to
match. Point a session at this container exactly like the original one; the
task board will automatically show fewer, different challenges, and the
report will note which OWASP categories were checked but not present.

## Running locally

```bash
docker compose -f target-hardened/docker-compose.yml up --build -d
```

Uses the same ports (80/23/554) as `../target/`, so stop that one first if
it's running:

```bash
docker compose -f target/docker-compose.yml down
docker compose -f target-hardened/docker-compose.yml up --build -d
```
