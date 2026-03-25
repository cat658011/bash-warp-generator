'use strict';

/**
 * Format → port resolution for WARP relays (JS mirror of core/ports.py).
 *
 * Ports are stored as [wireguard_port, amneziawg_port].
 * The resolver uses a strict positional index — no preference lists needed.
 */

const FORMATS = new Set(['wireguard', 'amnezia', 'wiresock', 'clash']);

// Formats that use the AmneziaWG port (ports[1]).
const _AWG_FORMATS = new Set(['amnezia', 'wiresock', 'clash']);

/**
 * Return "host:port" using strict positional index selection.
 *
 * - wireguard: always uses ports[0] (WireGuard port).
 * - amnezia, wiresock, clash: use ports[1] (AmneziaWG port) when available,
 *   falling back to ports[0] if the relay only has one port.
 * - Unknown format IDs behave like wireguard (use ports[0]).
 *
 * @param {string} fmt - canonical format ID
 * @param {{ host: string, ports: number[] }} relay - relay object
 * @returns {string}
 */
function resolveEndpoint(fmt, relay) {
  if (_AWG_FORMATS.has(fmt) && relay.ports.length >= 2) {
    return `${relay.host}:${relay.ports[1]}`;
  }
  return `${relay.host}:${relay.ports[0]}`;
}

module.exports = { FORMATS, resolveEndpoint };
