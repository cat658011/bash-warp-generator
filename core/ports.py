"""Format → port resolution for WARP relays.

Ports are stored as a two-element array: ``[wireguard_port, amneziawg_port]``.
The resolver uses a strict positional index — no preference lists needed.
All intelligence stays in Python; the relay JSON only declares supported ports.
"""

from __future__ import annotations

FORMATS: frozenset[str] = frozenset({"wireguard", "amnezia", "wiresock", "clash"})

# Formats that use the AmneziaWG port (ports[1]).
_AWG_FORMATS: frozenset[str] = frozenset({"amnezia", "wiresock", "clash"})


def resolve_endpoint(fmt: str, host: str, ports: list[int]) -> str:
    """Return ``host:port`` using strict positional index selection.

    - ``wireguard``: always uses ``ports[0]`` (WireGuard port).
    - ``amnezia``, ``wiresock``, ``clash``: use ``ports[1]`` (AmneziaWG port)
      when the relay has at least two ports; fall back to ``ports[0]``
      otherwise to prevent index errors.
    - Unknown format IDs behave like ``wireguard`` (use ``ports[0]``).
    """
    if fmt in _AWG_FORMATS and len(ports) >= 2:
        return f"{host}:{ports[1]}"
    return f"{host}:{ports[0]}"
