"""Configuration loading and management."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIGS_DIR = Path(__file__).resolve().parent.parent / "configs"


@dataclass(frozen=True)
class DnsServer:
    """A selectable DNS server option."""

    id: str
    servers: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RelayServer:
    """A selectable relay / endpoint option."""

    id: str
    endpoint: str = ""


@dataclass(frozen=True)
class RoutingService:
    """A selectable service with IP routes for split-tunnelling."""

    id: str
    routes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BotConfigs:
    """Aggregated configuration loaded from JSON files."""

    dns_servers: list[DnsServer] = field(default_factory=list)
    relay_servers: list[RelayServer] = field(default_factory=list)
    routing_services: list[RoutingService] = field(default_factory=list)


def _load_json(filename: str) -> Any:
    """Read and parse a JSON file from the configs directory."""
    path = CONFIGS_DIR / filename
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_configs() -> BotConfigs:
    """Load all configuration files and return a ``BotConfigs`` instance."""
    dns_data = _load_json("dns_servers.json")
    relay_data = _load_json("relay_servers.json")
    routing_data = _load_json("routing_services.json")

    return BotConfigs(
        dns_servers=[DnsServer(**entry) for entry in dns_data],
        relay_servers=[RelayServer(**entry) for entry in relay_data],
        routing_services=[RoutingService(**entry) for entry in routing_data],
    )
