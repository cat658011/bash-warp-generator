"""Format → port resolution for WARP relays.

The canonical set of supported format IDs and each format's ordered list of
preferred UDP ports live here.  The resolver finds the first preferred port
that a given relay actually supports, falling back to the relay's first port
when none match.  No JSON config involved.
"""

from __future__ import annotations

FORMATS: frozenset[str] = frozenset({"wireguard", "amnezia", "wiresock", "clash"})

# Each format lists its preferred ports from most-wanted to least-wanted.
# The resolver picks the first port in this list that the relay supports.
FORMAT_PORT_PREFERENCES: dict[str, list[int]] = {
    "wireguard": [2408, 4500, 500, 1701],
    "amnezia":   [4500, 2408, 500, 1701],
    "wiresock":  [2408, 4500, 500, 1701],
    "clash":     [2408, 4500, 500, 1701],
}


def resolve_endpoint(fmt: str, host: str, ports: list[int]) -> str:
    """Return ``host:port`` using format-aware port selection.

    Picks the first port in *fmt*'s preference list that appears in *ports*.
    Falls back to ``ports[0]`` when the format is unknown or none of its
    preferred ports are supported.
    """
    preferences = FORMAT_PORT_PREFERENCES.get(fmt, FORMAT_PORT_PREFERENCES["wireguard"])
    for port in preferences:
        if port in ports:
            return f"{host}:{port}"
    return f"{host}:{ports[0]}"
