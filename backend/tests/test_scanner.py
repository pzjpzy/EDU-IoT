"""Scanner unit tests. Kept hermetic: the only network activity is against an
ephemeral loopback listener the test itself opens, so nothing external is ever
contacted.
"""
import socket

from app.services import scanner


def test_connect_scan_detects_open_port():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    try:
        assert scanner._connect_scan_port("127.0.0.1", port) is True
    finally:
        srv.close()


def test_connect_scan_detects_closed_port():
    # Bind then immediately close to get a port that is almost certainly free.
    tmp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tmp.bind(("127.0.0.1", 0))
    port = tmp.getsockname()[1]
    tmp.close()
    assert scanner._connect_scan_port("127.0.0.1", port) is False


def test_summarise_banner_prefers_server_header():
    raw = "HTTP/1.0 200 OK\r\nServer: IoT-Cam/1.0\r\nContent-Type: text/html\r\n\r\n"
    assert scanner._summarise_banner(raw, "http") == "Server: IoT-Cam/1.0"


def test_summarise_banner_falls_back_to_first_line():
    raw = "220 IoT-Cam FTP ready\r\n"
    assert scanner._summarise_banner(raw, "ftp") == "220 IoT-Cam FTP ready"


def test_intel_maps_known_and_unknown_protocols():
    assert scanner._intel_for("telnet")["owasp_id"] == "I2"
    assert scanner._intel_for("http")["owasp_id"] == "I3"
    # Anything not in the table gets the generic fallback intel.
    assert scanner._intel_for("weird-proto") is scanner._GENERIC_INTEL


def test_run_scan_shape_against_no_services():
    # A port that nothing is listening on -> a well-formed, empty result.
    result = scanner.run_scan("127.0.0.1", use_nmap=False, use_scapy=False)
    assert result["target_ip"] == "127.0.0.1"
    assert isinstance(result["open_ports"], list)
    assert isinstance(result["services"], list)
    assert "socket:" in result["engine_notes"][0]
    assert "nmap: disabled" in " ".join(result["engine_notes"])
