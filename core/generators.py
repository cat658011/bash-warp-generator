"""Configuration generators for WireGuard, AmneziaWG, Clash, and WireSock."""

from __future__ import annotations

import base64
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

# ---------------------------------------------------------------------------
# Load AmneziaWG parameters from shared config
# ---------------------------------------------------------------------------
_CONFIGS_DIR = Path(__file__).resolve().parent.parent / "configs"


def _load_warp_params() -> dict:
    path = _CONFIGS_DIR / "warp_params.json"
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


_WARP_PARAMS = _load_warp_params()
_AMNEZIA_CONF = _WARP_PARAMS["amnezia"]

_AMNEZIA_JC = _AMNEZIA_CONF["Jc"]
_AMNEZIA_JMIN = _AMNEZIA_CONF["Jmin"]
_AMNEZIA_JMAX = _AMNEZIA_CONF["Jmax"]
_AMNEZIA_S1 = _AMNEZIA_CONF["S1"]
_AMNEZIA_S2 = _AMNEZIA_CONF["S2"]
_AMNEZIA_H1 = _AMNEZIA_CONF["H1"]
_AMNEZIA_H2 = _AMNEZIA_CONF["H2"]
_AMNEZIA_H3 = _AMNEZIA_CONF["H3"]
_AMNEZIA_H4 = _AMNEZIA_CONF["H4"]

_I1_PAYLOADS: list[str] = _WARP_PARAMS["i1_payloads"]


def _random_i1() -> str:
    """Return a randomly selected I1 obfuscation payload."""
    return random.choice(_I1_PAYLOADS)


@dataclass(frozen=True)
class GeneratorParams:
    """Common parameters passed to every generator."""

    private_key: str
    public_key: str
    peer_public_key: str
    client_ipv4: str
    client_ipv6: str
    dns_servers: list[str] = field(default_factory=list)
    endpoint: str = "162.159.192.1:500"
    allowed_ips: list[str] = field(default_factory=lambda: ["0.0.0.0/0", "::/0"])
    mtu: int = 0

    def __post_init__(self) -> None:
        if self.mtu == 0:
            object.__setattr__(self, "mtu", _WARP_PARAMS.get("mtu", 1280))


class ConfigGenerator(Protocol):
    """Interface that every config generator must satisfy."""

    def generate(self, params: GeneratorParams) -> tuple[str, str]:
        """Return ``(config_text, filename)``."""
        ...


# ---------------------------------------------------------------------------
# WireGuard
# ---------------------------------------------------------------------------
class WireGuardGenerator:
    """Standard WireGuard configuration."""

    def generate(self, params: GeneratorParams) -> tuple[str, str]:
        dns = ", ".join(params.dns_servers)
        allowed = ", ".join(params.allowed_ips)
        config = (
            "[Interface]\n"
            f"PrivateKey = {params.private_key}\n"
            f"Address = {params.client_ipv4}/32, {params.client_ipv6}/128\n"
            f"DNS = {dns}\n"
            f"MTU = {params.mtu}\n"
            "\n"
            "[Peer]\n"
            f"PublicKey = {params.peer_public_key}\n"
            f"AllowedIPs = {allowed}\n"
            f"Endpoint = {params.endpoint}\n"
        )
        return config, "warp-wireguard.conf"


# ---------------------------------------------------------------------------
# AmneziaWG
# ---------------------------------------------------------------------------


class AmneziaWGGenerator:
    """AmneziaWG configuration with obfuscation parameters."""

    def generate(self, params: GeneratorParams) -> tuple[str, str]:
        dns = ", ".join(params.dns_servers)
        allowed = ", ".join(params.allowed_ips)
        i1 = _random_i1()
        config = (
            "[Interface]\n"
            f"PrivateKey = {params.private_key}\n"
            f"S1 = {_AMNEZIA_S1}\n"
            f"S2 = {_AMNEZIA_S2}\n"
            f"Jc = {_AMNEZIA_JC}\n"
            f"Jmin = {_AMNEZIA_JMIN}\n"
            f"Jmax = {_AMNEZIA_JMAX}\n"
            f"H1 = {_AMNEZIA_H1}\n"
            f"H2 = {_AMNEZIA_H2}\n"
            f"H3 = {_AMNEZIA_H3}\n"
            f"H4 = {_AMNEZIA_H4}\n"
            f"MTU = {params.mtu}\n"
            f"I1 = {i1}\n"
            f"Address = {params.client_ipv4}, {params.client_ipv6}\n"
            f"DNS = {dns}\n"
            "\n"
            "[Peer]\n"
            f"PublicKey = {params.peer_public_key}\n"
            f"AllowedIPs = {allowed}\n"
            f"Endpoint = {params.endpoint}\n"
        )
        return config, "warp-amnezia.conf"

    def generate_deeplink(self, params: GeneratorParams) -> str:
        """Return an ``vpn://…`` deep-link importable by AmneziaVPN."""
        conf_text, _ = self.generate(params)
        host, port = params.endpoint.rsplit(":", 1)

        awg_json = {
            "H1": str(_AMNEZIA_H1),
            "H2": str(_AMNEZIA_H2),
            "H3": str(_AMNEZIA_H3),
            "H4": str(_AMNEZIA_H4),
            "Jc": str(_AMNEZIA_JC),
            "Jmax": str(_AMNEZIA_JMAX),
            "Jmin": str(_AMNEZIA_JMIN),
            "S1": str(_AMNEZIA_S1),
            "S2": str(_AMNEZIA_S2),
            "allowed_ips": params.allowed_ips,
            "client_ip": f"{params.client_ipv4}, {params.client_ipv6}",
            "client_priv_key": params.private_key,
            "config": conf_text.replace("\n", "\r\n"),
            "hostName": host,
            "mtu": params.mtu,
            "port": int(port),
            "server_pub_key": params.peer_public_key,
        }

        container = {
            "containers": [
                {
                    "container": "amnezia-awg",
                    "awg": {
                        "isThirdPartyConfig": True,
                        "last_config": json.dumps(awg_json, separators=(",", ":")),
                        "port": port,
                        "transport_proto": "udp",
                    },
                }
            ],
            "defaultContainer": "amnezia-awg",
            "description": "Cloudflare WARP",
            "hostName": host,
        }

        encoded = base64.b64encode(
            json.dumps(container, separators=(",", ":")).encode()
        ).decode()
        return f"vpn://{encoded}"


# ---------------------------------------------------------------------------
# Clash
# ---------------------------------------------------------------------------
class ClashGenerator:
    """Clash proxy configuration (YAML)."""

    def generate(self, params: GeneratorParams) -> tuple[str, str]:
        host, port = params.endpoint.rsplit(":", 1)
        dns_lines = "\n".join(f"      - {s}" for s in params.dns_servers)
        full_tunnel = "0.0.0.0/0" in params.allowed_ips

        if full_tunnel:
            rules = "  - MATCH,WARP"
        else:
            lines: list[str] = []
            for cidr in params.allowed_ips:
                keyword = "IP-CIDR6" if ":" in cidr else "IP-CIDR"
                lines.append(f"  - {keyword},{cidr},WARP")
            lines.append("  - MATCH,DIRECT")
            rules = "\n".join(lines)

        config = (
            "port: 7890\n"
            "socks-port: 7891\n"
            "allow-lan: false\n"
            "mode: rule\n"
            "log-level: info\n"
            "\n"
            "dns:\n"
            "  enable: true\n"
            "  nameserver:\n"
            f"{dns_lines}\n"
            "\n"
            "proxies:\n"
            "  - name: WARP\n"
            "    type: wireguard\n"
            f"    server: {host}\n"
            f"    port: {port}\n"
            f"    ip: {params.client_ipv4}\n"
            f"    ipv6: {params.client_ipv6}\n"
            f"    private-key: {params.private_key}\n"
            f"    public-key: {params.peer_public_key}\n"
            "    udp: true\n"
            f"    mtu: {params.mtu}\n"
            "\n"
            "proxy-groups:\n"
            "  - name: Proxy\n"
            "    type: select\n"
            "    proxies:\n"
            "      - WARP\n"
            "      - DIRECT\n"
            "\n"
            "rules:\n"
            f"{rules}\n"
        )
        return config, "warp-clash.yaml"


# ---------------------------------------------------------------------------
# WireSock
# ---------------------------------------------------------------------------
class WireSockGenerator:
    """WireSock configuration (Windows WireGuard variant)."""

    def generate(self, params: GeneratorParams) -> tuple[str, str]:
        dns = ", ".join(params.dns_servers)
        full_tunnel = "0.0.0.0/0" in params.allowed_ips

        lines = [
            "[Interface]",
            f"PrivateKey = {params.private_key}",
            f"Address = {params.client_ipv4}/32",
            f"DNS = {dns}",
            f"MTU = {params.mtu}",
            "",
            "[Peer]",
            f"PublicKey = {params.peer_public_key}",
            f"Endpoint = {params.endpoint}",
        ]

        if full_tunnel:
            lines.append("AllowedIPs = 0.0.0.0/0")
        else:
            for cidr in params.allowed_ips:
                if ":" not in cidr:
                    lines.append(f"AllowedIPs = {cidr}")

        config = "\n".join(lines) + "\n"
        return config, "warp-wiresock.conf"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
GENERATORS: dict[str, type[ConfigGenerator]] = {
    "wireguard": WireGuardGenerator,
    "amnezia": AmneziaWGGenerator,
    "clash": ClashGenerator,
    "wiresock": WireSockGenerator,
}
