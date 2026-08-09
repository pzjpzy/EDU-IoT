"""The lab-scope guardrail is the safety boundary of the whole tool: it is the
only thing stopping a session (and therefore the scanner) from being pointed
at an arbitrary internet host. These tests lock that behaviour down.
"""
from app.services.guardrail import is_in_scope


def test_loopback_is_in_scope():
    assert is_in_scope("127.0.0.1")


def test_rfc1918_ranges_are_in_scope():
    assert is_in_scope("10.0.0.1")
    assert is_in_scope("172.16.5.4")
    assert is_in_scope("192.168.1.50")


def test_public_ip_is_out_of_scope():
    assert not is_in_scope("8.8.8.8")
    assert not is_in_scope("1.1.1.1")


def test_malformed_input_is_out_of_scope():
    assert not is_in_scope("not-an-ip")
    assert not is_in_scope("")
    assert not is_in_scope("999.999.999.999")
