'use strict';

/**
 * Format → port resolution for WARP relays (JS mirror of core/ports.py).
 *
 * The resolver finds the first port in a format's preference list that the
 * relay actually supports, falling back to relay.ports[0] when none match.
 * No JSON config involved.
 */

const FORMATS = new Set(['wireguard', 'amnezia', 'wiresock', 'clash']);

// Each format lists its preferred ports from most-wanted to least-wanted.
const FORMAT_PORT_PREFERENCES = {
  wireguard: [2408, 4500, 500, 1701],
  amnezia:   [4500, 2408, 500, 1701],
  wiresock:  [2408, 4500, 500, 1701],
  clash:     [2408, 4500, 500, 1701],
};

/**
 * Return "host:port" using format-aware port selection.
 *
 * Picks the first port in fmt's preference list that relay.ports contains.
 * Falls back to relay.ports[0] when the format is unknown or none of its
 * preferred ports are supported.
 *
 * @param {string} fmt - canonical format ID
 * @param {{ host: string, ports: number[] }} relay - relay object
 * @returns {string}
 */
function resolveEndpoint(fmt, relay) {
  const preferred = FORMAT_PORT_PREFERENCES[fmt] || FORMAT_PORT_PREFERENCES.wireguard;
  const port = preferred.find((p) => relay.ports.includes(p)) ?? relay.ports[0];
  return `${relay.host}:${port}`;
}

module.exports = { FORMATS, FORMAT_PORT_PREFERENCES, resolveEndpoint };
