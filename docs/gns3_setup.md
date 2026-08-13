# Wiring the Simulated Camera into a GNS3 Lab (VirtualBox, Windows 11 Home)

This is a detailed, click-by-click guide for running the `target/` vulnerable
camera as a **Docker node inside GNS3**, on a Windows 11 Home machine where
Docker Desktop / WSL2 already holds the CPU's virtualization (so VMware's
nested-virtualization option fails and Hyper-V Manager isn't available). We use
**VirtualBox** to host the GNS3 VM, which sidesteps both problems.

If you get stuck, jump to [Troubleshooting](#troubleshooting) at the bottom.

---

## 0. The big picture (read this first)

There are **three layers**, and most confusion comes from mixing them up:

```
┌─ YOUR WINDOWS HOST ─────────────────────────────────────────────┐
│                                                                  │
│   GNS3 GUI  ─────────────(control)────────────┐                  │
│   EduVAPT backend + frontend ─────(scan)────┐  │                  │
│                                             │  │                  │
│        host-only network 192.168.56.0/24    │  │                  │
│                                             ▼  ▼                  │
│   ┌─ GNS3 VM (a Linux VM, run by VirtualBox) ───────────────┐    │
│   │   • runs the GNS3 *server*                               │    │
│   │   • has its OWN Docker engine (separate from Docker      │    │
│   │     Desktop!) that actually runs your camera container   │    │
│   │                                                          │    │
│   │   ┌─ Your topology ──────────────────────────────────┐  │    │
│   │   │  [eduvapt-camera] ─ [Switch] ─ [Cloud→host-only]  │  │    │
│   │   └───────────────────────────────────────────────────┘  │  │
│   └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

Key things this diagram tells you:

1. **The GNS3 GUI you click is on Windows; the GNS3 *server* is inside the GNS3
   VM.** They talk over a **host-only network** (that's why GNS3 insists the VM
   has a host-only adapter — see Part 2).
2. **The GNS3 VM has its own Docker**, completely separate from your Docker
   Desktop. An image you built with `docker build` on Windows is **invisible**
   to it. This is the single most common trip-up, and Part 4 handles it.
3. **The camera container lives inside the GNS3 VM.** For your Windows-hosted
   EduVAPT scanner to reach it, we bridge the topology out to the same
   host-only network via a **Cloud node** (Part 6).

---

## 1. Install the software (one-time)

Install these, in order:

1. **VirtualBox** (7.x) + the **VirtualBox Extension Pack** — <https://www.virtualbox.org>
2. **Enable "Windows Hypervisor Platform"** so VirtualBox can coexist with the
   Hyper-V/WSL2 that Docker Desktop uses. Open PowerShell **as Administrator**:
   ```powershell
   dism.exe /Online /Enable-Feature:HypervisorPlatform /All /NoRestart
   ```
   Then **reboot**.
3. **GNS3** for Windows — the desktop installer from <https://gns3.com>. During
   its installer you can *uncheck* the bundled Wireshark/SolarWinds extras;
   you only need GNS3 itself. When it asks about the GNS3 VM, you can skip that
   part here — we import it manually in Part 2.
4. **The GNS3 VM for VirtualBox** — on the GNS3 download page choose the
   **VirtualBox** version (a `.zip` that contains a `.ova` file), matching your
   installed GNS3 version. Unzip it.

> You do **not** need to uninstall Docker Desktop. The camera you run in GNS3 is
> a *separate* copy from the `docker compose` one; just don't run both against
> the same session at once.

---

## 2. Import and configure the GNS3 VM in VirtualBox

### 2a. Import it

VirtualBox → **File → Import Appliance** → pick the `.ova` you unzipped → keep
defaults → **Finish**. You'll now see a **"GNS3 VM"** entry in VirtualBox.

### 2b. Do NOT enable nested virtualization

Select the GNS3 VM → **Settings → System → Processor** tab → make sure
**"Enable Nested VT-x/AMD-V" is UNCHECKED** (it may be greyed out — that's
fine). Give it **2 CPUs** and **2048–4096 MB RAM** (System → Motherboard).

This is the whole reason we switched away from VMware: Docker camera node
does **not** need nested virtualization, and VirtualBox doesn't force it on.

### 2c. Set up the two network adapters

This is what your "must have a host-only adapter" message is about. The GNS3 VM
needs **two** virtual network cards:

**First, create a host-only network** (once): VirtualBox → **File → Tools →
Network Manager** → **Host-only Networks** tab → if the list is empty, click
**Create**. This makes an adapter on `192.168.56.0/24` with DHCP enabled. Leave
it as-is.

**Then, on the GNS3 VM → Settings → Network:**

| Adapter | Attached to | Purpose |
|---------|-------------|---------|
| **Adapter 1** | **NAT** | Gives the GNS3 VM internet — needed so it can pull Docker base images when you build the camera. |
| **Adapter 2** | **Host-only Adapter** → select the one from above | The private link the GNS3 GUI (and later your scanner) uses to reach the VM. |
**use virtio-net as adapter type for both adapter**
Tick **"Enable Network Adapter"** on both. Click **OK**.

### 2d. Boot it once

Double-click the GNS3 VM in VirtualBox to start it. After a minute a blue text
console appears showing something like:

```
GNS3 VM
Version: 2.x.x
KVM support available: False        <- fine, we don't need it
IP: 192.168.56.101
```

**Write down that IP** (`192.168.56.101` in this example — yours may differ).
Login (if needed) is user `gns3`, password `gns3`. Leave the VM running.

> "KVM support available: False" is expected and OK — that only limits QEMU
> nodes, not Docker nodes.

---

## 3. Connect the GNS3 GUI to the VM

Open GNS3 (the Windows app). If the setup wizard appears: choose **"Run
appliances in a virtual machine"** → **VirtualBox** → select **"GNS3 VM"**.

If no wizard: **Edit → Preferences → GNS3 VM** → tick **Enable the GNS3 VM** →
Virtualization engine **VirtualBox** → VM name **GNS3 VM** → OK.

Look at the **Servers Summary** panel (bottom-right of the GNS3 window). Within
a minute the **GNS3 VM** entry should turn **green**. Green = the GUI is talking
to the server inside the VM. If it stays red, see Troubleshooting.

---

## 4. Get the camera image into the GNS3 VM's Docker (the important part)

Remember from Part 0: the GNS3 VM has its **own** Docker. We must build the
`eduvapt-camera` image *inside* the VM. The easiest way is to copy the `target/`
folder into the VM over SSH and build it there.

From a **PowerShell window on Windows** (replace the IP with your VM's from
step 2d):

```powershell
scp -r "C:\Users\user\Videos\EDU-IoT\target" gns3@192.168.56.101:/home/gns3/target
```

(Windows 10/11 has `scp`/`ssh` built in. Password is `gns3`.)

Then log into the VM and build:

```powershell
ssh gns3@192.168.56.101
```

Now, **inside the VM's shell**:

```bash
cd ~/target
docker build -t eduvapt-camera .
docker images | grep eduvapt-camera     # confirm it's there
```

The build pulls a Python base image over the NAT adapter (Adapter 1), so the VM
needs working internet — if the pull hangs, check Adapter 1 is set to NAT.

Type `exit` to leave the SSH session. The image now lives in the GNS3 VM's
Docker, which is exactly where GNS3 looks for it.

---

## 5. Register the camera as a GNS3 Docker template

In GNS3: **Edit → Preferences → Docker containers → New**.

- **Server**: choose **Run this Docker container on the GNS3 VM**
- **Image name**: `eduvapt-camera:latest`
- **Adapters**: `1`
- **Start command**: leave blank (the image's own `entrypoint.sh` starts the
  web, Telnet and RTSP services)
- **Console type**: `telnet` (lets you open the node's shell if you need to set
  its IP by hand later)

Finish. A new **eduvapt-camera** template appears in the node list on the left.

---

## 6. Build the topology

Drag these three nodes onto the canvas:

1. **eduvapt-camera** (your template)
2. **Ethernet switch** (built-in, under "Switches" / the switch icon)
3. **Cloud** (built-in, under "End devices" / the cloud icon)

**Wire them:** camera → switch, and switch → cloud. Use the cable/link tool
(the connector icon on the left toolbar), click a node, pick its port, click the
next node.

**Point the Cloud at the host-only network** (this is what lets your Windows
host reach the camera): right-click the **Cloud → Configure → Ethernet
interfaces** tab → in the dropdown pick the interface that corresponds to the
**host-only** network (often shown as `eth1`, or by its `192.168.56.x` name) →
**Add** → OK.

```
[eduvapt-camera] --- [Ethernet switch] --- [Cloud → host-only]
```

Right-click empty canvas → **Start all nodes**. The camera node's icon turns
green.

---

## 7. Give the camera an IP, and verify from Windows

The camera container has no DHCP client, so give it a static address on the
host-only subnet. Right-click the **eduvapt-camera** node → **Console** (opens a
shell inside the container) and run:

docker ps
docker exec -u root -it <container_name_or_id> /bin/bash

```bash
ip addr add 192.168.56.50/24 dev eth0
ip link set eth0 up
```

(Pick any free `192.168.56.x` that isn't `.1`, the DHCP range `.100+`, or the
GNS3 VM's own address.)

Now, from **PowerShell on Windows**, confirm your host can reach it:

```powershell
Test-NetConnection -ComputerName 192.168.56.50 -Port 80
```

`TcpTestSucceeded : True` means you're done — the camera is reachable from the
host exactly like any other lab target.

---

## 8. Point EduVAPT-IoT at the camera

Start the tool as usual (backend on :8000, frontend on :5173). In the dashboard,
create a **new session** with **Target IP = `192.168.56.50`** (whatever you
assigned).

`192.168.56.0/24` is inside the default `LAB_CIDRS` (RFC1918) in
[`../backend/app/config.py`](../backend/app/config.py), so the scope guardrail
allows it with no changes. Run the **Recon** step — the automated scan will now
enumerate the camera *inside your GNS3 topology*, and everything downstream
(tasks, report) works identically.

---

## Troubleshooting

**The GNS3 VM won't start in VirtualBox / errors about VT-x.**
Confirm you ran the `dism` command in Part 1.2 and rebooted. You'll likely see a
"turtle" icon on the running VM — that just means VirtualBox is running in the
slower Hyper-V-coexistence mode, which is fine for one Docker node. If it still
refuses to boot a 64-bit VM, your host's virtualization is fully locked by
Docker Desktop; use the **remote GNS3 server** fallback (a spare PC or a small
cloud Linux VM running `gns3server`) — ask and I'll write that up.

**Servers Summary shows the GNS3 VM red, not green.**
The GUI can't reach the server. Check: the VM is actually running in VirtualBox;
Adapter 2 is Host-only; and you can `ping 192.168.56.101` from Windows. If ping
fails, the host-only adapter wasn't created or wasn't attached (Part 2c).

**GNS3 says the image `eduvapt-camera:latest` can't be found.**
You built it in Docker Desktop, not in the GNS3 VM. Redo Part 4 — build it
*inside* the VM over SSH. Verify with `docker images` in the VM's shell.

**`Test-NetConnection` fails even though the node is green.**
Almost always the Cloud node isn't bound to the host-only interface (Part 6), or
the camera's static IP is on the wrong subnet. Re-check both are `192.168.56.x`.
Open the camera console and run `ip addr` to confirm the address stuck.

**The `docker build` inside the VM can't download the base image.**
Adapter 1 must be NAT (internet). Check `ping 8.8.8.8` works inside the VM.

**If GNS3 networking just won't cooperate and you're short on time.**
The tool itself doesn't care where the camera runs. Fall back to
`cd target && docker compose up --build -d` (see
[`../target/README.md`](../target/README.md)), point a session at `127.0.0.1`,
and present the GNS3 topology **diagram** as your network-design artifact in the
report. Nothing about EduVAPT changes — only the target's location does.
```
