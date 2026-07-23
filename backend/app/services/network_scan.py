"""Host discovery: Scapy ARP request with a ping-based fallback.

ARP discovery needs raw-socket access (Npcap on Windows, usually requiring
the backend process to run elevated). Rather than fail the whole recon step
when that's unavailable, we fall back to a plain ICMP ping and tell the UI
which method actually worked - itself a small teaching point about privilege
requirements for different scan techniques.
"""
import platform
import subprocess

from app.config import SOCKET_TIMEOUT_SECONDS


def _arp_discover(target_ip: str) -> bool:
    from scapy.all import ARP, Ether, srp  # imported lazily: needs Npcap on Windows

    packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=target_ip)
    answered, _ = srp(packet, timeout=SOCKET_TIMEOUT_SECONDS, verbose=0)
    return len(answered) > 0


def _ping_discover(target_ip: str) -> bool:
    count_flag = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_flag = "-w" if platform.system().lower() == "windows" else "-W"
    timeout_value = "1000" if platform.system().lower() == "windows" else "1"
    try:
        result = subprocess.run(
            ["ping", count_flag, "1", timeout_flag, timeout_value, target_ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=SOCKET_TIMEOUT_SECONDS + 2,
        )
        return result.returncode == 0
    except Exception:
        return False


def discover_host(target_ip: str) -> tuple[bool, str, str | None]:
    """Returns (is_alive, method_used, warning)."""
    try:
        alive = _arp_discover(target_ip)
        if alive:
            return True, "scapy-arp", None
        # ARP doesn't traverse loopback/routed hops the way it does on a
        # local Ethernet segment (e.g. scanning 127.0.0.1, or a target one
        # hop away in GNS3), so a "no reply" doesn't necessarily mean the
        # host is down - double-check with a ping before reporting it dead.
        alive = _ping_discover(target_ip)
        return alive, "scapy-arp+icmp-ping", None
    except Exception as exc:  # noqa: BLE001 - any raw-socket failure falls back
        alive = _ping_discover(target_ip)
        warning = (
            "ARP discovery unavailable (needs Npcap + Administrator privileges "
            f"on Windows): {exc}. Fell back to ICMP ping."
        )
        return alive, "icmp-ping-fallback", warning
