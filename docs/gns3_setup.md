# Wiring the Simulated Camera into a GNS3 Lab

This walks through importing the `target/` Docker image into GNS3 as the
"vulnerable IoT camera" node in a lab topology, and getting EduVAPT-IoT
(running natively on your Windows host) able to reach it.

GNS3's Docker-node support and host-networking behaviour vary a bit by
version/setup, so treat the exact click-path as approximate for your
installed version - the underlying steps (build image, import as template,
wire a NAT/cloud node for host reachability) stay the same.

## 1. Build the image

```bash
cd target
docker build -t eduvapt-camera .
```

If your GNS3 server is the **GNS3 VM** (the usual setup on Windows - a
VirtualBox/VMware appliance that GNS3 Desktop drives), Docker templates need
to exist inside *that* VM's Docker, not just your Windows Docker Desktop.
Either:

- Build the image directly on the GNS3 VM (SSH into it and run the same
  `docker build` there, after copying over the `target/` folder), or
- If GNS3 is configured to use **your local machine** as the server (Edit >
  Preferences > Server, "Local server" pointing at Docker Desktop), the image
  you just built with Docker Desktop is already visible to it.

## 2. Add it as a Docker node template

In GNS3: **Edit > Preferences > Docker containers > New**.

- Image name: `eduvapt-camera:latest`
- Adapters: 1
- Start command: leave default (the image's own `ENTRYPOINT` runs
  `entrypoint.sh`, which starts all three services)
- Console type: `none` or `telnet` (there's no interactive console needed;
  the point of the node is its network services, not a shell)

Finish the wizard, then drag the new **eduvapt-camera** template from the
node list onto your topology canvas.

## 3. Wire the topology

A minimal lab:

```
[eduvapt-camera] --- [Switch] --- [NAT node]
```

- Add a **Switch** node and connect the camera node to it.
- Add GNS3's built-in **NAT** node (cloud icon in the node list) and connect
  it to the same switch. The NAT node is what gives devices in the topology
  - and your host machine - a shared reachable network, the same mechanism
  GNS3 normally uses to give lab devices internet access.

Start all three nodes (right-click canvas > Start all).

## 4. Get the camera's IP and confirm host reachability

The camera container runs a plain Linux userspace with no DHCP client
running by default in this image, so it will **not** automatically pick up
an address from the NAT node. Two options:

- **Static IP (simplest)**: open the camera node's console (or `docker exec`
  into it if it's running on a Docker server you can reach) and assign an
  address on the NAT node's subnet, e.g.:
  ```bash
  ip addr add 192.168.122.50/24 dev eth0
  ip route add default via 192.168.122.1
  ```
  (Check the NAT node's actual subnet first - right-click it in GNS3 >
  "Node information".)
- **Add a DHCP server node** from GNS3's node list on the same switch if you'd
  rather the camera get an address automatically.

From a terminal on your Windows host, confirm reachability:

```powershell
Test-NetConnection -ComputerName 192.168.122.50 -Port 80
```

If that succeeds, EduVAPT-IoT (running natively on Windows, not inside GNS3)
can reach it exactly like any other lab target.

## 5. Point EduVAPT-IoT at it

In the EduVAPT-IoT dashboard, create a new session with **Target IP** set to
whatever address you assigned the camera (e.g. `192.168.122.50`). The
guardrail in `backend/app/config.py` (`LAB_CIDRS`) already allows the full
RFC1918 range by default, so a typical GNS3 NAT subnet should be in-scope
without any changes.

## If host reachability doesn't work out of the box

GNS3-VM networking setups differ enough (VirtualBox host-only adapters,
VMware bridged mode, WSL2-backed "local server" mode, etc.) that step 4 is
the part most likely to need adjusting for your specific machine. If
`Test-NetConnection` fails, the fastest fallback for demoing/grading the tool
itself is the plain `docker compose up` route documented in
[`../target/README.md`](../target/README.md), which needs no GNS3 networking
at all - and you still get to show the GNS3 topology diagram as the network
design artifact for your report. Happy to debug the specific GNS3 networking
setup together once you've tried it on your machine.
