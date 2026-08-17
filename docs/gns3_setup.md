# Wiring the Simulated Camera into a GNS3 Lab (VirtualBox, Windows 11 Home)

A click-by-click guide for running the `target/` vulnerable camera as a **Docker
node inside GNS3**, on a Windows 11 Home machine where Docker Desktop / WSL2
already holds the CPU's virtualization (so VMware's nested-virtualization option
fails and Hyper-V Manager isn't available). We use **VirtualBox** to host the
GNS3 VM, which sidesteps both problems.

This reflects a setup that was actually brought up and made to work. Two steps
are easy to miss and produce failures that look like something else entirely —
**promiscuous mode** (Part 2c) and **where you test from** (Part 8). If you skip
nothing else, don't skip those.

If you get stuck, jump to [Troubleshooting](#troubleshooting) at the bottom.

---

## 0. The big picture (read this first)

There are **three layers**, and most confusion comes from mixing them up:

```
┌─ YOUR WINDOWS HOST  192.168.56.1 ───────────────────────────────┐
│                                                                  │
│   GNS3 GUI  ─────────────(control)────────────┐                  │
│   EduVAPT backend + frontend                  │                  │
│     ├ recon scan ──────────────────┐          │                  │
│     ├ GET /eduvapt/profile ────────┤          │                  │
│     └ GET /eduvapt/status ─────────┤          │                  │
│                                    │          │                  │
│        host-only network 192.168.56.0/24      │                  │
│                                    ▼          ▼                  │
│   ┌─ GNS3 VM (a Linux VM, run by VirtualBox) ───────────────┐    │
│   │   eth0 = NAT (internet)   eth1 = host-only (e.g. .102)  │    │
│   │   • runs the GNS3 *server*                              │    │
│   │   • has its OWN Docker engine (separate from Docker      │   │
│   │     Desktop!) that actually runs your camera container   │   │
│   │                                                          │   │
│   │   ┌─ Your topology ─────────────────────────────────┐   │   │
│   │   │  [eduvapt-camera .50] ──── [Cloud → eth1]        │   │   │
│   │   └──────────────────────────────────────────────────┘   │   │
│   └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

Key things this diagram tells you:

1. **The GNS3 GUI you click is on Windows; the GNS3 *server* is inside the GNS3
   VM.** They talk over a **host-only network** (that's why GNS3 insists the VM
   has a host-only adapter — see Part 2c).
2. **The GNS3 VM has its own Docker**, completely separate from your Docker
   Desktop. An image you built with `docker build` on Windows is **invisible**
   to it. This is a common trip-up, and Part 4 handles it.
3. **The camera container lives inside the GNS3 VM.** For your Windows-hosted
   EduVAPT backend to reach it, we bridge the topology out to the same host-only
   network via a **Cloud node** (Part 6).

### What the backend actually requires

Everything below exists to satisfy three things in the code:

- The recon scanner ([`../backend/app/services/scanner.py`](../backend/app/services/scanner.py))
  opens plain TCP connections from **Windows** to the camera.
- The task board reads `http://<target>/eduvapt/profile` on every load
  ([`../backend/app/services/target_profile.py`](../backend/app/services/target_profile.py)).
- Auto-detected tasks poll `http://<target>/eduvapt/status`
  ([`../backend/app/services/task_engine.py`](../backend/app/services/task_engine.py)).

Both endpoints are **port 80, hardcoded**. If Windows can't reach the camera on
port 80 you don't get an error — the board silently assumes every weakness
exists and auto tasks never complete. That's why Part 8 matters.

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

This is the whole reason we switched away from VMware: the Docker camera node
does **not** need nested virtualization, and VirtualBox doesn't force it on.

### 2c. Set up the two network adapters

This is what your "must have a host-only adapter" message is about. The GNS3 VM
needs **two** virtual network cards — two is enough; you do not need a third.

**First, create a host-only network** (once): VirtualBox → **File → Tools →
Network Manager** → **Host-only Networks** tab → if the list is empty, click
**Create**. This makes an adapter on `192.168.56.0/24` with DHCP enabled. Leave
it as-is. Your Windows host will be `192.168.56.1` on this network.

**Then, on the GNS3 VM → Settings → Network:**

| Adapter | Attached to | Advanced | Purpose |
|---------|-------------|----------|---------|
| **Adapter 1** | **NAT** | default | Gives the GNS3 VM internet — needed so it can pull Docker base images when you build the camera. |
| **Adapter 2** | **Host-only Adapter** → select the one from above | **Promiscuous Mode: `Allow All`** | The private link the GNS3 GUI uses to reach the VM, *and* the wire your topology bridges onto. |

**Use `virtio-net` as the adapter type for both adapters.**

Tick **"Enable Network Adapter"** on both. Click **OK**.

> ### Promiscuous Mode is mandatory, not optional
>
> The Cloud node doesn't create a Linux bridge — it runs **ubridge**, which
> injects your topology's frames onto Adapter 2 using the *camera's* MAC
> address, not the adapter's. With VirtualBox's default `Deny`, every reply
> addressed to the camera is dropped before it ever reaches ubridge.
>
> The failure mode is nasty because nothing reports an error: nodes go green,
> `docker ps` looks perfect, the container is healthy — and the camera is simply
> unreachable from Windows.
>
> This setting requires a **full VM power-off and start** from the VirtualBox
> manager. Rebooting from inside the guest does not reapply it.

### 2d. Boot it once

Double-click the GNS3 VM in VirtualBox to start it. After a minute a blue text
console appears showing something like:

```
GNS3 VM
Version: 2.x.x
KVM support available: False        <- fine, we don't need it
IP: 192.168.56.102
```

**Write down that IP** (yours may differ). Login (if needed) is user `gns3`,
password `gns3`. Leave the VM running.

> "KVM support available: False" is expected and OK — that only limits QEMU
> nodes, not Docker nodes.

That address comes from VirtualBox's DHCP server, whose pool starts at `.101`
(the DHCP server itself sits at `.100`). So when you pick a static address for
the camera in Part 7, choose something **below `.100`** to stay clear of the
pool.

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

Remember from Part 0: the GNS3 VM has its **own** Docker, so the image has to
exist *there*. Two ways.

**Option A — ship the image you already built.** Needs no internet in the VM and
guarantees identical bits to the target you tested locally. From PowerShell on
Windows (replace the IP with your VM's from step 2d):

```powershell
docker save eduvapt-camera:latest | ssh gns3@192.168.56.102 "docker load"
```

If you haven't built it locally yet, run `cd target && docker build -t eduvapt-camera .`
first.

**Option B — build inside the VM.** Copy the folder over and build there:

```powershell
scp -r "C:\Users\user\Videos\EDU-IoT\target" gns3@192.168.56.102:/home/gns3/target
```

Then `ssh gns3@192.168.56.102` and, **inside the VM's shell**:

```bash
cd ~/target
docker build -t eduvapt-camera .
```

(Windows 10/11 has `scp`/`ssh` built in. Password is `gns3`.) This pulls a Python
base image over the NAT adapter, so the VM needs working internet — if the pull
hangs, check Adapter 1 is set to NAT.

Either way, confirm inside the VM:

```bash
docker images | grep eduvapt-camera
```

---

## 5. Register the camera as a GNS3 Docker template

In GNS3: **Edit → Preferences → Docker containers → New**.

- **Server**: choose **Run this Docker container on the GNS3 VM**
- **Image name**: `eduvapt-camera:latest`
- **Adapters**: `1`
- **Start command**: leave blank — GNS3 prepends `/gns3/init.sh` to the image's
  `ENTRYPOINT`, so [`../target/entrypoint.sh`](../target/entrypoint.sh) still
  runs and starts the web, Telnet and RTSP services
- **Console type**: `telnet`

Finish. A new **eduvapt-camera** template appears in the node list on the left.

⚠️ That console type is GNS3's *node shell*, on a GNS3-assigned port. It is
**not** the camera's own Telnet service on port 23 — students still attack port
23 over the network. Different things, same word.

### Bonus: the hardened variant needs no second image

`target-hardened/` builds a byte-identical image to `target/` — only the
environment variables differ (see [`../target/app/vuln_config.py`](../target/app/vuln_config.py)).
So duplicate the template (right-click → **Duplicate**), name it
`eduvapt-camera-hardened`, and paste into its **Environment** box:

```
EDUVAPT_HTTP_DEFAULT_CREDS=false
EDUVAPT_SNAPSHOT_UNAUTH=false
EDUVAPT_TELNET_ENABLED=true
EDUVAPT_TELNET_DEFAULT_CREDS=true
EDUVAPT_RTSP_ENABLED=false
```

The backend adapts on its own — a shorter challenge list, plus a "tested but not
found" section in the report. A two-scenario lab for free.

---

## 6. Build the topology

Drag just **two** nodes onto the canvas:

1. **eduvapt-camera** (your template)
2. **Cloud** (built-in, under "End devices" / the cloud icon)

**Wire them:** camera `eth0` → Cloud. Use the cable/link tool (the connector icon
on the left toolbar), click a node, pick its port, click the next node.

```
[eduvapt-camera] --- [Cloud → host-only]
```

You *can* put an Ethernet switch between them, but with a single node it adds
nothing: GNS3's built-in switch runs inside **Dynamips**, adding an emulated
process and two UDP tunnels to the path (and noticeable CPU load on a VM without
KVM). Fewer components, fewer things to debug.

(If you later want to run both camera variants at once, you *will* need a switch
— a Cloud port takes one link only. See [Part 11](#11-optional-run-both-camera-variants-side-by-side).)

**Point the Cloud at the host-only network** — this is what lets your Windows
host reach the camera. Right-click the **Cloud → Configure → Ethernet
interfaces** tab → pick the interface carrying the host-only address → **Add**
→ OK.

To be sure which one that is, run `ip -br addr show` in the VM and choose the
interface holding `192.168.56.x` (usually `eth1`). **Go by the address, not the
number.** If it isn't listed, tick **"Show special Ethernet interfaces"** in the
same dialog.

Right-click empty canvas → **Start all nodes**. The camera node's icon turns
green.

---

## 7. Give the camera a persistent static IP

GNS3 Docker nodes boot with **no IPv4 address at all** — there is no DHCP client
in the image. You have to assign one.

Do it through GNS3 so it survives restarts: right-click the **eduvapt-camera**
node → **Configure** → **Network configuration** tab. Replace the commented-out
sample with:

```
auto eth0
iface eth0 inet static
    address 192.168.56.50
    netmask 255.255.255.0
```

Then **stop and start the node** — the file is applied at container start, so
editing it while the node is running does nothing.

Notes:

- **No `gateway` line.** Windows is at `192.168.56.1` on the same `/24`, so this
  is all layer 2; a gateway pointing at something nonexistent just slows boot.
- Ordinary spaces work for the indented lines. Tabs are not required.
- Pick an address **below `.100`** to stay out of VirtualBox's DHCP pool.

Confirm it applied:

```bash
docker exec $(docker ps -q --filter name=eduvapt) /gns3/bin/busybox ip addr show
```

You want an `inet 192.168.56.50/24` line on `eth0`.

### Why that command looks so strange

Two things worth knowing before you try the obvious alternatives:

- **The image has no `ip` or `ifconfig`.** `python:3.12-slim` ships with neither
  `iproute2` nor `net-tools`. GNS3 mounts a static busybox that provides them,
  but only the container's main process gets `/gns3/bin` on its `PATH` — a
  `docker exec` shell does not. Hence the full path.
- **Setting the address by hand doesn't stick.** `ip addr add ... dev eth0` works
  for a quick test, but GNS3 tears down and recreates the container's network
  namespace on every node restart, so it's gone the next time you start the
  node. Fine for debugging; never leave a lab depending on it.

---

## 8. Verify — from Windows, never from the GNS3 VM

> ### The single most misleading thing in this setup
>
> **You cannot ping the camera from the GNS3 VM.** Not because anything is
> broken — it is architecturally impossible.
>
> ubridge injects the topology's frames onto the host-only adapter through a
> **raw socket**, which transmits straight out the wire and bypasses the VM's own
> IP stack. The VM's kernel never *receives* those frames, so it never answers
> them. In the other direction, a VirtualBox host-only switch won't send a frame
> back out the port it arrived on.
>
> So `ping 192.168.56.50` from the VM returns `Destination Host Unreachable` on a
> perfectly working lab. Testing from there will send you chasing faults that
> don't exist.

Your **Windows host** is a different device on that switch — and it's the one
that matters anyway, since that's where the backend runs. From PowerShell:

```powershell
ping 192.168.56.50
```

Then the check that actually matters:

```powershell
curl.exe http://192.168.56.50/eduvapt/profile
```

Use `curl.exe`, not `curl` — in PowerShell, bare `curl` is an alias for
`Invoke-WebRequest` and takes different arguments. You should get five flags:

```json
{"http_default_creds_vulnerable":true,"rtsp_enabled":true,"snapshot_unauth_vulnerable":true,"telnet_default_creds_vulnerable":true,"telnet_enabled":true}
```

That response proves the entire chain: bridge, IP, and the exact HTTP path the
backend depends on. Also confirm the other two ports:

```powershell
Test-NetConnection -ComputerName 192.168.56.50 -Port 23
```

### The one legitimate VM-side test

If you do need to debug from the VM, watch frames *arrive* from the topology. In
one SSH session:

```bash
sudo tcpdump -i eth1 -n arp
```

In another, make the container talk:

```bash
docker exec $(docker ps -q --filter name=eduvapt) /gns3/bin/busybox ping -c 3 192.168.56.1
```

ARP requests with a `02:42:...` source MAC (the container's) appearing on `eth1`
prove the data path works. You will **not** see the VM reply to them — see the
box above. That's expected, not a fault.

---

## 9. Point EduVAPT-IoT at the camera

Start the tool as usual (backend on :8000, frontend on :5173 — see
[`docker_local_setup.md`](docker_local_setup.md) for the details). In the
dashboard, create a **new session** with **Target IP = `192.168.56.50`**
(whatever you assigned).

`192.168.56.0/24` is inside the default `LAB_CIDRS` (RFC1918) in
[`../backend/app/config.py`](../backend/app/config.py), so the scope guardrail
allows it with no changes. Run the **Recon** step — the automated scan will now
enumerate the camera *inside your GNS3 topology*, and everything downstream
(tasks, report) works identically.

Two things to confirm on the task board: **no warning banner** about the target's
vulnerability profile, and recon finding **ports 80, 23 and 554**.

> Don't use GNS3's built-in **NAT** node instead of a Cloud. Its
> `192.168.122.0/24` is RFC1918 so it passes the scope guardrail, but Windows has
> no route to it — the session gets created and then fails at everything.

---

## 10. Reset between runs

Unlike the throwaway `docker compose` container, a GNS3 node keeps its recorded
events ([`../target/app/events.py`](../target/app/events.py)) across stop/start,
so the next student would start with the auto tasks already completed:

```powershell
curl.exe -X POST http://192.168.56.50/eduvapt/reset
```

---

## 11. Optional: run both camera variants side by side

The vulnerable and hardened cameras both listen on ports 80/23/554, so with
`docker compose` you can only run **one at a time**. In GNS3 each node has its
own IP, so that conflict disappears — you can run both simultaneously and
demonstrate the adaptive task board live: a full challenge list against one
target, a shorter one plus a "tested but not found" report section against the
other.

```
[camera .50] ──┐
               ├── [Switch] ── [Cloud → eth1]
[hardened .51] ┘
```

No second image is needed — see the bonus note in Part 5.

### 11a. Duplicate the template

**Edit → Preferences → Docker containers** → select `eduvapt-camera` → **Copy** →
**Edit** the copy:

- **Name**: `eduvapt-camera-hardened`
- **Environment**:
  ```
  EDUVAPT_HTTP_DEFAULT_CREDS=false
  EDUVAPT_SNAPSHOT_UNAUTH=false
  EDUVAPT_TELNET_ENABLED=true
  EDUVAPT_TELNET_DEFAULT_CREDS=true
  EDUVAPT_RTSP_ENABLED=false
  ```

Leave everything else alone: image `eduvapt-camera:latest`, server **GNS3 VM**,
Adapters `1`, start command blank, console `telnet`.

One `KEY=VALUE` per line, no quotes, no spaces around `=`. Values are parsed by
`_flag()` in [`../target/app/vuln_config.py`](../target/app/vuln_config.py),
which accepts `1`/`true`/`yes`/`on` — anything else reads as false.

> Environment can also be set per-node (right-click node → **Configure**).
> Note that changing a *template's* environment does **not** propagate to nodes
> already created from it, so create the node after editing the template.

### 11b. Rework the topology

A Cloud port takes one link only, so the switch is genuinely required here:

1. Delete the existing camera → Cloud link.
2. Drag on an **Ethernet switch** and the **eduvapt-camera-hardened** template.
3. Wire: camera `eth0` → switch, hardened `eth0` → switch, switch → Cloud `eth1`.

Promiscuous Mode `Allow All` (Part 2c) already covers this — it isn't per-MAC, so
any number of nodes works with no further changes.

### 11c. Address the new node

Right-click the hardened node → **Configure → Network configuration**:

```
auto eth0
iface eth0 inet static
    address 192.168.56.51
    netmask 255.255.255.0
```

Keep it below `.100`, and never reuse an address — two nodes answering the same
ARP produces baffling intermittent behaviour. Start (or restart) the node.

### 11d. Telling the two containers apart

`--filter name=eduvapt` now matches both, so it stops being safe:

```bash
docker ps --format "{{.ID}}  {{.Names}}"
```

Use the specific container ID for any per-node command from here on.

### 11e. Verify the environment actually applied

This is the step that matters. From Windows:

```powershell
curl.exe http://192.168.56.51/eduvapt/profile
```

Expected:

```json
{"http_default_creds_vulnerable":false,"rtsp_enabled":false,"snapshot_unauth_vulnerable":false,"telnet_default_creds_vulnerable":true,"telnet_enabled":true}
```

**If it returns all `true`, the Environment never reached the container.** This
failure impersonates success — the node runs, the endpoint answers, and you're
quietly running two identical vulnerable cameras. Check with:

```bash
docker exec <hardened-container-id> env | grep EDUVAPT
```

An empty result means the env is on the template but not this node: recreate the
node, or set Environment on the node directly and restart it.

Confirm RTSP is genuinely gone too — `EDUVAPT_RTSP_ENABLED=false` stops
[`../target/entrypoint.sh`](../target/entrypoint.sh) from launching it at all:

```powershell
Test-NetConnection -ComputerName 192.168.56.51 -Port 554
```

That must **fail**, while the same test against `.50` succeeds.

### 11f. Run both

Create one EduVAPT session per IP. Against `.51` you get a shorter board — the
RTSP and HTTP default-credential tasks drop out via each task's `requires` list
in [`../backend/app/content/tasks.yaml`](../backend/app/content/tasks.yaml),
Telnet stays, and the report gains a "tested but not found" section.

Run the vulnerable target first so the contrast is obvious. If two containers
plus Dynamips drag on a KVM-less VM, bump the GNS3 VM to 3–4 vCPUs.

---

## Troubleshooting

### Things that look broken but aren't

Don't chase any of these — all are normal:

- **No `veth-*` interface on the VM.** GNS3 creates a **tap** device and moves it
  *into* the container's network namespace, so it correctly never appears in the
  VM's `ip -br link`. Confirm from inside the container:
  `cat /sys/class/net/eth0/iflink` returns the same number as `eth0`'s own index
  — which is what a tap looks like, and what a veth would not.
- **`ping` from the GNS3 VM fails.** Expected — see Part 8.
- **ubridge is running but nothing works.** ubridge starting proves nothing on
  its own. In the GNS3 VM it already has the capabilities it needs
  (`getcap /usr/bin/ubridge` → `cap_net_admin,cap_net_raw=eip`).
- **`docker0` and `virbr0` show as DOWN.** Unrelated to your topology. GNS3 wires
  containers itself and never uses Docker's default bridge; `virbr0` belongs to
  the built-in NAT node.
- **`gns3server[...]: No configuration file could be found or read`** in
  `journalctl`. A benign startup warning.

### Real problems

**Windows can't reach the camera, but the container looks healthy.**
In order of likelihood: (1) Promiscuous Mode isn't `Allow All`, or was changed
without a full VM power-off; (2) the Cloud is bound to the NAT interface instead
of the host-only one; (3) `eth0` in the container has no IPv4 address.

**`eth0` has no address after a restart.**
The Network configuration wasn't saved, or the node wasn't stopped and started
after saving. Check what actually landed in the container:
```bash
docker exec $(docker ps -q --filter name=eduvapt) cat /etc/network/interfaces
```
If it still shows only the commented-out sample, your GUI edit never reached it.

**`sendto: Network is unreachable` when pinging from inside the container.**
No IPv4 address on `eth0`, so there's no route and the packet never leaves. Fix
the address — this is not a bridging problem.

**The task board warns it couldn't read the target's vulnerability profile.**
Windows can't reach port 80. The board falls back to assuming every weakness
exists, and auto tasks will never complete. Re-run the Part 8 checks.

**The GNS3 VM won't start in VirtualBox / errors about VT-x.**
Confirm you ran the `dism` command in Part 1.2 and rebooted. A "turtle" icon on
the running VM just means VirtualBox is in the slower Hyper-V-coexistence mode,
which is fine for one Docker node.

**Servers Summary shows the GNS3 VM red, not green.**
The GUI can't reach the server. Check the VM is actually running, Adapter 2 is
Host-only, and you can `ping 192.168.56.102` from Windows.

**GNS3 says the image `eduvapt-camera:latest` can't be found.**
You built it in Docker Desktop, not in the GNS3 VM. Redo Part 4 and verify with
`docker images` in the VM's shell.

**The `docker build` inside the VM can't download the base image.**
Adapter 1 must be NAT (internet). Check `ping 8.8.8.8` works inside the VM — or
use Option A in Part 4, which needs no internet at all.

**Seeing the actual error.**
`journalctl -u gns3` only records service start/stop, not node wiring. To see
what GNS3 really does when a node starts, run the server in the foreground on
the VM:
```bash
sudo systemctl stop gns3 && gns3server --debug
```
Reconnect the GUI, start the node, and read the output. `Ctrl+C` and
`sudo systemctl start gns3` when you're done.

**If GNS3 networking just won't cooperate and you're short on time.**
The tool itself doesn't care where the camera runs. Fall back to the local Docker
target (see [`docker_local_setup.md`](docker_local_setup.md)), point a session at
`127.0.0.1`, and present the GNS3 topology **diagram** as your network-design
artifact in the report. Nothing about EduVAPT changes — only the target's
location does.
