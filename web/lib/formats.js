'use strict';

const { FORMATS } = require('./ports');

const FORMAT_LABELS = {
  wireguard: { name: 'WireGuard', descKey: 'fmt_wireguard_desc' },
  amnezia: { name: 'AmneziaWG', descKey: 'fmt_amnezia_desc' },
  clash: { name: 'Clash', descKey: 'fmt_clash_desc' },
  wiresock: { name: 'WireSock', descKey: 'fmt_wiresock_desc' },
};

module.exports = { FORMATS, FORMAT_LABELS };
