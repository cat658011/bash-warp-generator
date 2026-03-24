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
        assert dns.name
        assert len(dns.servers) > 0


def test_relay_servers_loaded() -> None:
    configs = load_configs()
    assert len(configs.relay_servers) > 0
    for relay in configs.relay_servers:
        assert isinstance(relay, RelayServer)
        assert relay.name
        assert relay.endpoint


def test_routing_services_loaded() -> None:
    configs = load_configs()
    assert len(configs.routing_services) > 0
    for svc in configs.routing_services:
        assert isinstance(svc, RoutingService)
        assert svc.name
        assert len(svc.routes) > 0


def test_first_routing_service_is_full_tunnel() -> None:
    configs = load_configs()
    full = configs.routing_services[0]
    assert "0.0.0.0/0" in full.routes
    assert "::/0" in full.routes
