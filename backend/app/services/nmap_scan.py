"""Nmap-backed port/service scan.

Uses a TCP connect scan (-sT) rather than a SYN scan (-sS) deliberately: it
does not require Administrator/raw-socket privileges, so the guided flow
works out of the box on a student's Windows machine as long as the Nmap
binary itself is installed and on PATH.
"""
import nmap

from app.config import NMAP_ARGS

# python-nmap only checks PATH by default. The official Windows Nmap
# installer does not always add itself to PATH, so we also check its two
# common install locations rather than forcing every student to edit their
# environment variables manually.
_WINDOWS_NMAP_LOCATIONS = (
    "nmap",
    r"C:\Program Files (x86)\Nmap\nmap.exe",
    r"C:\Program Files\Nmap\nmap.exe",
)


class NmapUnavailableError(RuntimeError):
    pass


def scan_ports(target_ip: str) -> list[dict]:
    try:
        scanner = nmap.PortScanner(nmap_search_path=_WINDOWS_NMAP_LOCATIONS)
    except nmap.PortScannerError as exc:
        raise NmapUnavailableError(
            "Nmap executable not found. Install Nmap (with Npcap) and ensure "
            "it is on your system PATH."
        ) from exc

    scanner.scan(hosts=target_ip, arguments=NMAP_ARGS)

    ports: list[dict] = []
    if target_ip in scanner.all_hosts():
        host_data = scanner[target_ip]
        for proto in host_data.all_protocols():
            for port, pdata in host_data[proto].items():
                ports.append(
                    {
                        "port": int(port),
                        "protocol": proto,
                        "state": pdata.get("state"),
                        "service": pdata.get("name") or "unknown",
                        "product": pdata.get("product") or "",
                        "version": pdata.get("version") or "",
                        "banner": " ".join(
                            p for p in [pdata.get("product"), pdata.get("version")] if p
                        ),
                    }
                )
    return sorted(ports, key=lambda p: p["port"])
