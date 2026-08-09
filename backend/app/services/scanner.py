"""Specialised recon scanner for IoT/CCTV targets (FYP objective 1).

This is the ONE place in EduVAPT-IoT that actually touches the target's
network itself. Everything else in the backend only tracks the progress of
scans/exploits the *student* performs. The scanner exists to satisfy the
"Guided Automation" idea (objective 2): the tool runs an automated recon
sweep, explains in plain language what each discovered service is and why it
matters, and the student then reproduces the same finding by hand in the
task board that follows. Demonstrate, then replicate.

Design goals:
  - Works on a stock Windows 11 student machine with NO admin rights and NO
    extra software: the core is a pure-Python TCP connect scan plus
    application-layer banner grabbing (sockets only).
  - Uses the suggested heavier tools when they ARE available, and degrades
    gracefully when they are not:
      * python-nmap  -> service/version detection (`-sV`) if the Nmap binary
                        is installed and on PATH.
      * Scapy        -> a raw TCP SYN probe for one port, to demonstrate
                        packet-level IoT protocol probing, if Scapy + a raw
                        socket backend (Npcap) are usable.
    Neither is required; their absence just drops an enrichment layer and is
    reported in `engine_notes` so it's visible (and explainable in a viva).
  - Never scans anything outside the configured lab scope: the router calls
    guardrail.assert_in_scope() before this module is ever reached.

The scanner reports *observations* mapped to OWASP IoT categories, not
confirmed exploits. Confirming a weakness (logging in with default creds,
grabbing the flag, etc.) is still the student's job in the task board.
"""
import socket
import time
from concurrent.futures import ThreadPoolExecutor

# Curated port list: the services actually relevant to an IP camera / DVR,
# not a full 65k sweep (that would be slow and pedagogically noisy). Each
# entry maps a well-known port to the protocol a student should expect there.
CCTV_PORTS: dict[int, str] = {
    21: "ftp",
    22: "ssh",
    23: "telnet",
    80: "http",
    443: "https",
    554: "rtsp",
    1935: "rtmp",
    5000: "http",
    8000: "http",
    8080: "http",
    8081: "http",
    8443: "https",
    8554: "rtsp",
    9000: "http",
    34567: "dvrip",   # Xiongmai/"Sofia" DVR control port
    37777: "dahua",   # Dahua device control port
}

CONNECT_TIMEOUT_SECONDS = 0.8
BANNER_TIMEOUT_SECONDS = 1.5
BANNER_MAX_BYTES = 512
MAX_WORKERS = 24

# How each discovered protocol maps to the OWASP IoT Top 5 and what the tool
# should tell the student. `severity_hint` is advisory only (the confirmed
# severity comes from the task the student later completes).
PROTOCOL_INTEL: dict[str, dict] = {
    "telnet": {
        "owasp_id": "I2",
        "severity_hint": "Medium",
        "observation": "Telnet is an unencrypted remote-administration protocol.",
        "why_it_matters": (
            "Anything typed over Telnet - including the admin password - crosses "
            "the network in cleartext and can be read by anyone on the path. It is "
            "exactly the kind of legacy service that should be disabled on a camera."
        ),
        "reproduce": "Confirm it yourself: nmap -p23 <target> and then connect with a telnet client.",
    },
    "rtsp": {
        "owasp_id": "I2",
        "severity_hint": "Medium",
        "observation": "RTSP carries the live video stream, here without transport encryption.",
        "why_it_matters": (
            "An exposed, unencrypted RTSP endpoint can leak the camera's video feed "
            "and reveals the streaming software version to anyone who can reach it."
        ),
        "reproduce": "Reproduce with an OPTIONS request to port 554 and read the Server banner.",
    },
    "http": {
        "owasp_id": "I3",
        "severity_hint": "Low",
        "observation": "An HTTP web admin/ecosystem interface is reachable.",
        "why_it_matters": (
            "The web interface is the primary attack surface of most IP cameras: "
            "default credentials, unauthenticated media endpoints, and weak session "
            "handling all live here."
        ),
        "reproduce": "Reproduce by browsing to the interface and enumerating its login/media paths.",
    },
    "https": {
        "owasp_id": "I3",
        "severity_hint": "Low",
        "observation": "An HTTPS web interface is reachable (encrypted transport).",
        "why_it_matters": (
            "Encrypted transport is the secure choice, but the interface behind it "
            "still needs strong authentication and authorisation checks."
        ),
        "reproduce": "Reproduce by browsing to the interface over HTTPS.",
    },
    "ssh": {
        "owasp_id": "I2",
        "severity_hint": "Low",
        "observation": "SSH is exposed (the encrypted alternative to Telnet).",
        "why_it_matters": (
            "SSH itself is fine; the risk is weak or default credentials behind it. "
            "Its presence alongside Telnet suggests remote management is enabled."
        ),
        "reproduce": "Note the version banner; check whether default credentials are accepted.",
    },
    "ftp": {
        "owasp_id": "I2",
        "severity_hint": "Medium",
        "observation": "FTP is exposed (a legacy, typically unencrypted file service).",
        "why_it_matters": "FTP often ships with anonymous or default access and no encryption.",
        "reproduce": "Check whether anonymous or default credentials are accepted.",
    },
    "dvrip": {
        "owasp_id": "I5",
        "severity_hint": "Medium",
        "observation": "A proprietary DVR control port (Xiongmai-style) is open.",
        "why_it_matters": "Proprietary DVR protocols have a long history of authentication-bypass CVEs.",
        "reproduce": "Identify the device/firmware family; check it against known advisories.",
    },
    "dahua": {
        "owasp_id": "I5",
        "severity_hint": "Medium",
        "observation": "A Dahua-style device control port is open.",
        "why_it_matters": "This vendor control protocol has known authentication-bypass CVEs.",
        "reproduce": "Identify the device/firmware family; check it against known advisories.",
    },
}

_GENERIC_INTEL = {
    "owasp_id": "I2",
    "severity_hint": "Low",
    "observation": "An unexpected network service is exposed.",
    "why_it_matters": "Every extra exposed service widens the attack surface of the device.",
    "reproduce": "Fingerprint the service and decide whether it should be running at all.",
}


def _connect_scan_port(target_ip: str, port: int) -> bool:
    """Pure-socket TCP connect check. Works everywhere, no privileges needed."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(CONNECT_TIMEOUT_SECONDS)
        try:
            return sock.connect_ex((target_ip, port)) == 0
        except OSError:
            return False


def _grab_banner(target_ip: str, port: int, expected: str) -> str | None:
    """Application-layer banner grab, protocol-aware for the services a camera
    exposes. Returns a trimmed, single-line banner string or None."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(BANNER_TIMEOUT_SECONDS)
            sock.connect((target_ip, port))

            if expected in ("http", "https"):
                probe = f"GET / HTTP/1.0\r\nHost: {target_ip}\r\n\r\n"
                sock.sendall(probe.encode())
            elif expected == "rtsp":
                probe = f"OPTIONS rtsp://{target_ip}:{port}/ RTSP/1.0\r\nCSeq: 1\r\n\r\n"
                sock.sendall(probe.encode())
            # telnet / ssh / ftp: the server speaks first, just read.

            data = sock.recv(BANNER_MAX_BYTES)
            if not data:
                return None
            text = data.decode("latin-1", errors="replace")
            return _summarise_banner(text, expected)
    except OSError:
        return None


def _summarise_banner(text: str, expected: str) -> str | None:
    """Pull the single most useful line out of a raw banner/response."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None
    if expected in ("http", "https", "rtsp"):
        # Prefer the Server: header; fall back to the status line.
        server = next((ln for ln in lines if ln.lower().startswith("server:")), None)
        return (server or lines[0])[:200]
    return lines[0][:200]


def _nmap_versions(target_ip: str, ports: list[int]) -> tuple[dict[int, str], str]:
    """Optional -sV enrichment via python-nmap. Returns ({port: 'name product
    version'}, note). Silently degrades if python-nmap or the Nmap binary is
    unavailable."""
    if not ports:
        return {}, "nmap: skipped (no open ports)"
    try:
        import nmap  # python-nmap; needs the Nmap binary on PATH
    except ImportError:
        return {}, "nmap: python-nmap not installed (socket scan used instead)"
    try:
        scanner = nmap.PortScanner()
        port_arg = ",".join(str(p) for p in ports)
        scanner.scan(hosts=target_ip, ports=port_arg, arguments="-sV -Pn -T4")
        versions: dict[int, str] = {}
        for host in scanner.all_hosts():
            for proto in scanner[host].all_protocols():
                for port, info in scanner[host][proto].items():
                    parts = [info.get("name", ""), info.get("product", ""), info.get("version", "")]
                    label = " ".join(p for p in parts if p).strip()
                    if label:
                        versions[int(port)] = label
        return versions, f"nmap: -sV completed on {len(versions)} port(s)"
    except Exception as exc:  # nmap.PortScannerError, OSError, etc.
        return {}, f"nmap: unavailable ({type(exc).__name__}) - socket scan used instead"


def _scapy_syn_probe(target_ip: str, port: int) -> str:
    """Optional packet-level demonstration: craft a raw TCP SYN with Scapy and
    report whether a SYN/ACK came back. Purely educational (shows IoT protocol
    probing at the packet layer, per objective 1); the connect scan above is
    what the results actually rely on. Needs Scapy + Npcap and usually admin,
    so this is wrapped to never break a scan when it can't run."""
    try:
        from scapy.all import IP, TCP, sr1  # noqa: N811
    except Exception:
        return "scapy: not installed (packet-level probe skipped)"
    try:
        pkt = IP(dst=target_ip) / TCP(dport=port, flags="S")
        resp = sr1(pkt, timeout=2, verbose=0)
        if resp is not None and resp.haslayer(TCP) and resp[TCP].flags & 0x12 == 0x12:
            return f"scapy: SYN/ACK from port {port} (packet-level probe confirmed open)"
        return f"scapy: no SYN/ACK from port {port} at the packet layer"
    except PermissionError:
        return "scapy: needs raw-socket privileges/Npcap (packet-level probe skipped)"
    except Exception as exc:
        return f"scapy: unavailable ({type(exc).__name__}) - packet-level probe skipped"


def _intel_for(protocol: str) -> dict:
    return PROTOCOL_INTEL.get(protocol, _GENERIC_INTEL)


def run_scan(target_ip: str, use_nmap: bool = True, use_scapy: bool = False) -> dict:
    """Run the recon sweep and return a structured, teachable result.

    Assumes the caller has already enforced lab scope. `use_scapy` defaults
    off because it typically needs elevated privileges; the UI can offer it as
    an opt-in "packet-level demo"."""
    started = time.time()
    ports = list(CCTV_PORTS.keys())

    # 1. Fast parallel TCP connect scan (the reliable core).
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        open_flags = list(pool.map(lambda p: _connect_scan_port(target_ip, p), ports))
    open_ports = [p for p, is_open in zip(ports, open_flags) if is_open]

    # 2. Banner grab each open port (also parallel).
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        banners = list(pool.map(lambda p: _grab_banner(target_ip, p, CCTV_PORTS[p]), open_ports))
    banner_by_port = dict(zip(open_ports, banners))

    # 3. Optional enrichment layers.
    engine_notes = [f"socket: TCP connect scan of {len(ports)} curated CCTV ports"]
    versions: dict[int, str] = {}
    if use_nmap:
        versions, nmap_note = _nmap_versions(target_ip, open_ports)
        engine_notes.append(nmap_note)
    else:
        engine_notes.append("nmap: disabled for this run")
    if use_scapy and open_ports:
        engine_notes.append(_scapy_syn_probe(target_ip, open_ports[0]))
    elif use_scapy:
        engine_notes.append("scapy: skipped (no open ports)")

    # 4. Assemble per-port results + OWASP-mapped narration.
    services = []
    for port in open_ports:
        protocol = CCTV_PORTS[port]
        intel = _intel_for(protocol)
        services.append(
            {
                "port": port,
                "protocol": protocol,
                "banner": banner_by_port.get(port),
                "version": versions.get(port),
                "owasp_id": intel["owasp_id"],
                "severity_hint": intel["severity_hint"],
                "observation": intel["observation"],
                "why_it_matters": intel["why_it_matters"],
                "reproduce": intel["reproduce"],
            }
        )

    summary = (
        f"Found {len(open_ports)} open service(s) on {target_ip}. "
        "Each is explained below; you'll confirm the exploitable ones yourself "
        "in the guided tasks."
        if open_ports
        else f"No open CCTV/IoT services responded on {target_ip}. "
        "Check the target is running and reachable from this machine."
    )

    return {
        "target_ip": target_ip,
        "duration_seconds": round(time.time() - started, 2),
        "ports_scanned": len(ports),
        "open_ports": open_ports,
        "services": services,
        "engine_notes": engine_notes,
        "summary": summary,
    }
