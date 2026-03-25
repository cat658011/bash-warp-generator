"""Tests for format → port resolution logic (core/ports.py)."""

from __future__ import annotations

import pytest

from core.ports import FORMATS, FORMAT_PORT_PREFERENCES, resolve_endpoint


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

RELAY_MULTI = ("relay.example.com", [4500, 2408])   # supports both common ports
RELAY_SINGLE_4500 = ("relay.example.com", [4500])   # only supports 4500
RELAY_SINGLE_2408 = ("relay.example.com", [2408])   # only supports 2408
RELAY_EXOTIC = ("relay.example.com", [1701])         # only supports an unusual port


# ---------------------------------------------------------------------------
# FORMATS constant
# ---------------------------------------------------------------------------

class TestFormats:
    def test_contains_all_canonical_ids(self) -> None:
        assert {"wireguard", "amnezia", "wiresock", "clash"} <= FORMATS

    def test_is_frozenset(self) -> None:
        assert isinstance(FORMATS, frozenset)

    def test_format_keys_match_preferences(self) -> None:
        assert set(FORMAT_PORT_PREFERENCES.keys()) == FORMATS


# ---------------------------------------------------------------------------
# resolve_endpoint — preferred port hit
# ---------------------------------------------------------------------------

class TestResolveEndpointPreferred:
    def test_wireguard_prefers_2408_when_available(self) -> None:
        host, ports = RELAY_MULTI
        endpoint = resolve_endpoint("wireguard", host, ports)
        assert endpoint == f"{host}:2408"

    def test_amnezia_prefers_4500_when_available(self) -> None:
        host, ports = RELAY_MULTI
        endpoint = resolve_endpoint("amnezia", host, ports)
        assert endpoint == f"{host}:4500"

    def test_wiresock_prefers_2408_when_available(self) -> None:
        host, ports = RELAY_MULTI
        endpoint = resolve_endpoint("wiresock", host, ports)
        assert endpoint == f"{host}:2408"

    def test_clash_prefers_2408_when_available(self) -> None:
        host, ports = RELAY_MULTI
        endpoint = resolve_endpoint("clash", host, ports)
        assert endpoint == f"{host}:2408"

    def test_returns_only_supported_port(self) -> None:
        host, ports = RELAY_SINGLE_4500
        # wireguard prefers 2408, which is not in [4500], so falls through to 4500
        endpoint = resolve_endpoint("wireguard", host, ports)
        assert endpoint == f"{host}:4500"

    def test_amnezia_gets_2408_when_4500_unavailable(self) -> None:
        host, ports = RELAY_SINGLE_2408
        # amnezia prefers 4500 but only 2408 is available
        endpoint = resolve_endpoint("amnezia", host, ports)
        assert endpoint == f"{host}:2408"


# ---------------------------------------------------------------------------
# resolve_endpoint — fallback behavior
# ---------------------------------------------------------------------------

class TestResolveEndpointFallback:
    def test_falls_back_to_first_port_when_no_preferred_match(self) -> None:
        host, ports = RELAY_EXOTIC
        # 1701 is last in every preference list; all others missing → ports[0]
        endpoint = resolve_endpoint("wireguard", host, ports)
        assert endpoint == f"{host}:1701"

    def test_unknown_format_uses_wireguard_preferences(self) -> None:
        host, ports = RELAY_MULTI
        endpoint = resolve_endpoint("unknown_format", host, ports)
        # Falls back to wireguard prefs: first match in [4500, 2408] is 2408
        assert endpoint == f"{host}:2408"

    def test_empty_string_format_falls_back_gracefully(self) -> None:
        host, ports = RELAY_SINGLE_4500
        endpoint = resolve_endpoint("", host, ports)
        assert ":" in endpoint
        assert endpoint.startswith(host)

    def test_returns_string_with_colon_separator(self) -> None:
        host, ports = RELAY_MULTI
        endpoint = resolve_endpoint("wireguard", host, ports)
        assert endpoint.count(":") == 1
        h, p = endpoint.rsplit(":", 1)
        assert h == host
        assert p.isdigit()


# ---------------------------------------------------------------------------
# resolve_endpoint — endpoint format
# ---------------------------------------------------------------------------

class TestResolveEndpointFormat:
    @pytest.mark.parametrize("fmt", list(FORMATS))
    def test_all_formats_produce_valid_endpoint(self, fmt: str) -> None:
        host, ports = RELAY_MULTI
        endpoint = resolve_endpoint(fmt, host, ports)
        h, p = endpoint.rsplit(":", 1)
        assert h == host
        assert int(p) in ports

    def test_port_in_relay_ports(self) -> None:
        host, ports = RELAY_MULTI
        for fmt in FORMATS:
            endpoint = resolve_endpoint(fmt, host, ports)
            _, port_str = endpoint.rsplit(":", 1)
            assert int(port_str) in ports
