"""Tests for configuration loading."""

from __future__ import annotations

from core.config import BotConfigs, DnsServer, RelayServer, RoutingService, load_configs


def test_load_configs_returns_bot_configs() -> None:
    configs = load_configs()
    assert isinstance(configs, BotConfigs)


def test_dns_servers_loaded() -> None:
    configs = load_configs()
    assert len(configs.dns_servers) > 0
    for dns in configs.dns_servers:
        assert isinstance(dns, DnsServer)
        assert dns.id
        assert len(dns.servers) > 0


def test_relay_servers_loaded() -> None:
    configs = load_configs()
    assert len(configs.relay_servers) > 0
    for relay in configs.relay_servers:
        assert isinstance(relay, RelayServer)
        assert relay.id
        assert relay.endpoint
        # Endpoints should be host-only (no port)
        assert ":" not in relay.endpoint


def test_routing_services_loaded() -> None:
    configs = load_configs()
    assert len(configs.routing_services) > 0
    for svc in configs.routing_services:
        assert isinstance(svc, RoutingService)
        assert svc.id
        assert len(svc.routes) > 0


def test_first_routing_service_is_full_tunnel() -> None:
    configs = load_configs()
    full = configs.routing_services[0]
    assert "0.0.0.0/0" in full.routes
    assert "::/0" in full.routes


def test_endpoint_ports_loaded() -> None:
    configs = load_configs()
    assert len(configs.endpoint_ports) > 0
    for fmt in ("wireguard", "amnezia", "clash", "wiresock"):
        assert fmt in configs.endpoint_ports
        assert isinstance(configs.endpoint_ports[fmt], int)


def test_resolve_endpoint_combines_host_and_port() -> None:
    configs = load_configs()
    relay = configs.relay_servers[0]
    endpoint = configs.resolve_endpoint(relay, "wireguard")
    assert endpoint == f"{relay.endpoint}:{configs.endpoint_ports['wireguard']}"


def test_resolve_endpoint_uses_format_port() -> None:
    """Each format should get its own port."""
    configs = load_configs()
    relay = configs.relay_servers[0]
    wg = configs.resolve_endpoint(relay, "wireguard")
    awg = configs.resolve_endpoint(relay, "amnezia")
    # Ports for different formats should differ (per endpoint_ports.json config)
    wg_port = int(wg.rsplit(":", 1)[1])
    awg_port = int(awg.rsplit(":", 1)[1])
    assert wg_port == configs.endpoint_ports["wireguard"]
    assert awg_port == configs.endpoint_ports["amnezia"]
