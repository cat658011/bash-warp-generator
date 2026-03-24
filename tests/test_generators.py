"""Tests for configuration generators."""

from __future__ import annotations

from core.generators import (
    AmneziaWGGenerator,
    ClashGenerator,
    GeneratorParams,
    WireGuardGenerator,
    WireSockGenerator,
)

_PARAMS = GeneratorParams(
    private_key="cHJpdmF0ZV9rZXlfYmFzZTY0X2VuY29kZWQ=",
    public_key="cHVibGljX2tleV9iYXNlNjRfZW5jb2RlZA==",
    peer_public_key="cGVlcl9wdWJsaWNfa2V5X2Jhc2U2NA==",
    client_ipv4="172.16.0.2",
    client_ipv6="fd01:db8:1111::2",
    dns_servers=["1.1.1.1", "1.0.0.1"],
    endpoint="162.159.192.1:500",
    allowed_ips=["0.0.0.0/0", "::/0"],
)

_SPLIT_PARAMS = GeneratorParams(
    private_key="cHJpdmF0ZV9rZXlfYmFzZTY0X2VuY29kZWQ=",
    public_key="cHVibGljX2tleV9iYXNlNjRfZW5jb2RlZA==",
    peer_public_key="cGVlcl9wdWJsaWNfa2V5X2Jhc2U2NA==",
    client_ipv4="172.16.0.2",
    client_ipv6="fd01:db8:1111::2",
    dns_servers=["8.8.8.8"],
    endpoint="162.159.193.1:2408",
    allowed_ips=["142.250.0.0/15", "172.217.0.0/16"],
)


# ── WireGuard ─────────────────────────────────────────────────────
class TestWireGuard:
    def test_generates_conf_format(self) -> None:
        content, filename = WireGuardGenerator().generate(_PARAMS)
        assert filename.endswith(".conf")
        assert "[Interface]" in content
        assert "[Peer]" in content

    def test_contains_private_key(self) -> None:
        content, _ = WireGuardGenerator().generate(_PARAMS)
        assert _PARAMS.private_key in content

    def test_contains_peer_key(self) -> None:
        content, _ = WireGuardGenerator().generate(_PARAMS)
        assert _PARAMS.peer_public_key in content

    def test_contains_endpoint(self) -> None:
        content, _ = WireGuardGenerator().generate(_PARAMS)
        assert _PARAMS.endpoint in content

    def test_contains_dns(self) -> None:
        content, _ = WireGuardGenerator().generate(_PARAMS)
        assert "1.1.1.1" in content

    def test_contains_addresses(self) -> None:
        content, _ = WireGuardGenerator().generate(_PARAMS)
        assert _PARAMS.client_ipv4 in content
        assert _PARAMS.client_ipv6 in content

    def test_has_persistent_keepalive(self) -> None:
        content, _ = WireGuardGenerator().generate(_PARAMS)
        assert "PersistentKeepalive = 25" in content


# ── AmneziaWG ─────────────────────────────────────────────────────
class TestAmneziaWG:
    def test_generates_conf_format(self) -> None:
        content, filename = AmneziaWGGenerator().generate(_PARAMS)
        assert filename.endswith(".conf")
        assert "[Interface]" in content

    def test_has_obfuscation_params(self) -> None:
        content, _ = AmneziaWGGenerator().generate(_PARAMS)
        for param in ("Jc =", "Jmin =", "Jmax =", "S1 =", "S2 =", "H1 ="):
            assert param in content

    def test_has_i1_payload(self) -> None:
        content, _ = AmneziaWGGenerator().generate(_PARAMS)
        # I1 payloads are hex strings from warp_params.json
        assert "I1 = " in content
        # Extract the I1 value and verify it's a non-empty hex string
        for line in content.splitlines():
            if line.startswith("I1 = "):
                val = line.removeprefix("I1 = ").strip()
                assert len(val) > 0
                assert all(c in "0123456789abcdef" for c in val)
                break
        else:
            raise AssertionError("I1 line not found")

    def test_deeplink_starts_with_vpn(self) -> None:
        deeplink = AmneziaWGGenerator().generate_deeplink(_PARAMS)
        assert deeplink.startswith("vpn://")

    def test_deeplink_is_valid_base64(self) -> None:
        """The deep-link contains valid base64-encoded JSON."""
        deeplink = AmneziaWGGenerator().generate_deeplink(_PARAMS)
        assert deeplink.startswith("vpn://")
        import base64, json
        payload = base64.b64decode(deeplink[len("vpn://"):])
        data = json.loads(payload)
        assert "containers" in data

    def test_has_persistent_keepalive(self) -> None:
        content, _ = AmneziaWGGenerator().generate(_PARAMS)
        assert "PersistentKeepalive = 25" in content

    def test_address_before_obfuscation(self) -> None:
        """Address and DNS must appear before obfuscation params."""
        content, _ = AmneziaWGGenerator().generate(_PARAMS)
        addr_pos = content.index("Address =")
        dns_pos = content.index("DNS =")
        s1_pos = content.index("S1 =")
        assert addr_pos < s1_pos, "Address must come before S1"
        assert dns_pos < s1_pos, "DNS must come before S1"


# ── Clash ─────────────────────────────────────────────────────────
class TestClash:
    def test_generates_yaml(self) -> None:
        content, filename = ClashGenerator().generate(_PARAMS)
        assert filename.endswith(".yaml")
        assert "proxies:" in content

    def test_full_tunnel_match_rule(self) -> None:
        content, _ = ClashGenerator().generate(_PARAMS)
        assert "MATCH,WARP" in content

    def test_split_tunnel_ip_rules(self) -> None:
        content, _ = ClashGenerator().generate(_SPLIT_PARAMS)
        assert "IP-CIDR,142.250.0.0/15,WARP" in content
        assert "MATCH,DIRECT" in content

    def test_contains_wireguard_proxy(self) -> None:
        content, _ = ClashGenerator().generate(_PARAMS)
        assert "type: wireguard" in content


# ── WireSock ──────────────────────────────────────────────────────
class TestWireSock:
    def test_generates_conf(self) -> None:
        content, filename = WireSockGenerator().generate(_PARAMS)
        assert filename.endswith(".conf")
        assert "[Interface]" in content

    def test_ipv4_only_address(self) -> None:
        content, _ = WireSockGenerator().generate(_PARAMS)
        # WireSock uses IPv4-only addressing
        assert f"{_PARAMS.client_ipv4}/32" in content

    def test_split_tunnel_multiple_allowed(self) -> None:
        content, _ = WireSockGenerator().generate(_SPLIT_PARAMS)
        assert "AllowedIPs = 142.250.0.0/15" in content
        assert "AllowedIPs = 172.217.0.0/16" in content

    def test_has_persistent_keepalive(self) -> None:
        content, _ = WireSockGenerator().generate(_PARAMS)
        assert "PersistentKeepalive = 25" in content
