"""Tests for format → port resolution logic (core/ports.py)."""

from __future__ import annotations

import pytest

from core.ports import FORMATS, _AWG_FORMATS, resolve_endpoint


# ---------------------------------------------------------------------------
# Fixtures — ports are [wireguard_port, amneziawg_port]
# ---------------------------------------------------------------------------

RELAY_DUAL = ("relay.example.com", [2408, 4500])   # standard two-port relay
RELAY_SINGLE = ("relay.example.com", [4500])        # single-port relay (fallback)


# ---------------------------------------------------------------------------
# FORMATS / _AWG_FORMATS constants
# ---------------------------------------------------------------------------

class TestFormats:
    def test_contains_all_canonical_ids(self) -> None:
        assert {"wireguard", "amnezia", "wiresock", "clash"} <= FORMATS

    def test_is_frozenset(self) -> None:
        assert isinstance(FORMATS, frozenset)

    def test_awg_formats_subset_of_formats(self) -> None:
        assert _AWG_FORMATS < FORMATS

    def test_wireguard_not_in_awg_formats(self) -> None:
        assert "wireguard" not in _AWG_FORMATS

    def test_awg_formats_contains_expected_ids(self) -> None:
        assert {"amnezia", "wiresock", "clash"} == _AWG_FORMATS


# ---------------------------------------------------------------------------
# resolve_endpoint — index-based port selection
# ---------------------------------------------------------------------------

class TestResolveEndpointIndexBased:
    def test_wireguard_uses_ports0(self) -> None:
        host, ports = RELAY_DUAL
        assert resolve_endpoint("wireguard", host, ports) == f"{host}:{ports[0]}"

    def test_amnezia_uses_ports1(self) -> None:
        host, ports = RELAY_DUAL
        assert resolve_endpoint("amnezia", host, ports) == f"{host}:{ports[1]}"

    def test_wiresock_uses_ports1(self) -> None:
        host, ports = RELAY_DUAL
        assert resolve_endpoint("wiresock", host, ports) == f"{host}:{ports[1]}"

    def test_clash_uses_ports1(self) -> None:
        host, ports = RELAY_DUAL
        assert resolve_endpoint("clash", host, ports) == f"{host}:{ports[1]}"

    def test_wireguard_gets_2408_from_standard_relay(self) -> None:
        host, ports = RELAY_DUAL
        assert resolve_endpoint("wireguard", host, ports) == f"{host}:2408"

    def test_amnezia_gets_4500_from_standard_relay(self) -> None:
        host, ports = RELAY_DUAL
        assert resolve_endpoint("amnezia", host, ports) == f"{host}:4500"


# ---------------------------------------------------------------------------
# resolve_endpoint — fallback behavior (single-port relay)
# ---------------------------------------------------------------------------

class TestResolveEndpointFallback:
    def test_wireguard_single_port_uses_ports0(self) -> None:
        host, ports = RELAY_SINGLE
        assert resolve_endpoint("wireguard", host, ports) == f"{host}:{ports[0]}"

    def test_amnezia_falls_back_to_ports0_when_only_one_port(self) -> None:
        host, ports = RELAY_SINGLE
        assert resolve_endpoint("amnezia", host, ports) == f"{host}:{ports[0]}"

    def test_wiresock_falls_back_to_ports0_when_only_one_port(self) -> None:
        host, ports = RELAY_SINGLE
        assert resolve_endpoint("wiresock", host, ports) == f"{host}:{ports[0]}"

    def test_clash_falls_back_to_ports0_when_only_one_port(self) -> None:
        host, ports = RELAY_SINGLE
        assert resolve_endpoint("clash", host, ports) == f"{host}:{ports[0]}"

    def test_unknown_format_uses_ports0(self) -> None:
        host, ports = RELAY_DUAL
        assert resolve_endpoint("unknown_format", host, ports) == f"{host}:{ports[0]}"

    def test_empty_string_format_uses_ports0(self) -> None:
        host, ports = RELAY_SINGLE
        endpoint = resolve_endpoint("", host, ports)
        assert endpoint == f"{host}:{ports[0]}"


# ---------------------------------------------------------------------------
# resolve_endpoint — output format
# ---------------------------------------------------------------------------

class TestResolveEndpointFormat:
    @pytest.mark.parametrize("fmt", list(FORMATS))
    def test_all_formats_produce_valid_endpoint(self, fmt: str) -> None:
        host, ports = RELAY_DUAL
        endpoint = resolve_endpoint(fmt, host, ports)
        h, p = endpoint.rsplit(":", 1)
        assert h == host
        assert int(p) in ports

    def test_returns_string_with_colon_separator(self) -> None:
        host, ports = RELAY_DUAL
        endpoint = resolve_endpoint("wireguard", host, ports)
        assert endpoint.count(":") == 1
        h, p = endpoint.rsplit(":", 1)
        assert h == host
        assert p.isdigit()
